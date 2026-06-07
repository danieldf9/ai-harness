import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from onyx.db.models import AgentRunTrace
from onyx.db.models import HealingPolicy
from onyx.utils.logger import setup_logger

logger = setup_logger()

def get_healing_policy(db_session: Session, agent_id: Optional[int]) -> Optional[HealingPolicy]:
    """Retrieve the applicable healing policy for the agent."""
    stmt = select(HealingPolicy).where(HealingPolicy.enabled == True)
    
    # Simple precedence: check for agent specific, then fallback to global
    if agent_id:
        agent_stmt = stmt.where(HealingPolicy.target_type == "agent", HealingPolicy.target_id == str(agent_id))
        agent_policy = db_session.execute(agent_stmt).scalar_one_or_none()
        if agent_policy:
            return agent_policy

    global_stmt = stmt.where(HealingPolicy.target_type == "global")
    return db_session.execute(global_stmt).scalar_one_or_none()

def record_agent_run_trace(
    db_session: Session,
    session_id: Optional[UUID],
    agent_id: Optional[int],
    user_id: Optional[UUID],
    prompt_template_id: Optional[int],
    prompt_version_id: Optional[int],
    model_name: str,
    retrieval_strategy: str,
    tool_plan_json: Optional[Dict],
    tools_called_json: Optional[Dict],
    citations_json: Optional[Dict],
    latency_ms: int,
    token_usage_json: Optional[Dict],
    outcome_status: str,
    confidence_score: Optional[float],
    failure_reason: Optional[str],
    recovery_actions_json: Optional[Dict],
    final_resolution: str,
) -> AgentRunTrace:
    """Record a trace of the agent execution."""
    trace = AgentRunTrace(
        session_id=session_id,
        agent_id=agent_id,
        user_id=user_id,
        prompt_template_id=prompt_template_id,
        prompt_version_id=prompt_version_id,
        model_name=model_name,
        retrieval_strategy=retrieval_strategy,
        tool_plan_json=tool_plan_json,
        tools_called_json=tools_called_json,
        citations_json=citations_json,
        latency_ms=latency_ms,
        token_usage_json=token_usage_json,
        outcome_status=outcome_status,
        confidence_score=confidence_score,
        failure_reason=failure_reason,
        recovery_actions_json=recovery_actions_json,
        final_resolution=final_resolution,
    )
    db_session.add(trace)
    db_session.commit()
    return trace

def evaluate_healing_policy(
    db_session: Session,
    agent_id: Optional[int],
    error_type: str,
    error_message: str,
    current_retry_count: int,
) -> Dict[str, Any]:
    """
    Evaluate the healing policy and return a recovery strategy.
    Returns a dict with 'action', 'strategy', 'fallback_model', etc.
    """
    policy = get_healing_policy(db_session, agent_id)
    
    if not policy:
        logger.info(f"No healing policy found for agent {agent_id}. Failing gracefully.")
        return {"action": "fail", "reason": "no_policy"}

    if current_retry_count >= policy.max_retries:
        logger.warning(f"Max retries ({policy.max_retries}) exceeded for agent {agent_id}.")
        return {
            "action": "escalate" if policy.allow_human_escalation else "fail",
            "reason": "max_retries_exceeded"
        }

    # Determine recovery strategy based on error type
    if error_type == "timeout" and policy.allow_model_fallback:
        return {
            "action": "retry",
            "strategy": "model_fallback",
            "message": "The primary model timed out. Falling back to a secondary model."
        }
    
    if error_type == "empty_retrieval" and policy.allow_retrieval_expansion:
        return {
            "action": "retry",
            "strategy": "expand_retrieval",
            "message": "No relevant context found. Expanding search bounds."
        }
        
    if error_type == "tool_error" and policy.allow_tool_replan:
        return {
            "action": "retry",
            "strategy": "tool_replan",
            "message": f"Tool encountered an error: {error_message}. Disabling tool for this run."
        }

    if error_type == "low_confidence":
        threshold = policy.low_confidence_threshold or 0.0
        # If we have a confidence error, it implies it was lower than the threshold
        return {
            "action": "ask_clarifying_question",
            "strategy": "clarification",
            "message": "I'm not confident enough to answer this. Could you clarify your question?"
        }

    return {"action": "fail", "reason": "unhandled_error_type"}

def run_with_healing(
    loop_fn,
    setup_info: dict,
    model_llm,
    *args,
    **kwargs
):
    from onyx.db.engine.sql_engine import get_session_with_current_tenant
    
    retry_count = 0
    max_retries = 3
    success = False
    
    while retry_count <= max_retries and not success:
        start_time = time.time()
        try:
            loop_fn(*args, **kwargs)
            
            # Post-run evaluation for empty retrieval
            sc = kwargs.get("state_container")
            if sc:
                tool_calls = sc.get_tool_calls()
                has_search = any("search" in tc.tool_name.lower() for tc in tool_calls)
                if has_search and len(sc.get_all_search_docs()) == 0:
                    raise Exception("empty_retrieval")
            
            success = True
            
            with get_session_with_current_tenant() as db_session:
                tools_called = [json.loads(tc.model_dump_json()) for tc in sc.get_tool_calls()] if sc else None
                record_agent_run_trace(
                    db_session=db_session,
                    session_id=setup_info.get("session_id"),
                    agent_id=setup_info.get("agent_id"),
                    user_id=setup_info.get("user_id"),
                    prompt_template_id=None,
                    prompt_version_id=None,
                    model_name=model_llm.config.model_name,
                    retrieval_strategy="standard",
                    tool_plan_json=None,
                    tools_called_json={"tools": tools_called} if tools_called else None,
                    citations_json=list(sc.get_all_search_docs().keys()) if sc else None,
                    latency_ms=int((time.time() - start_time) * 1000),
                    token_usage_json=None, # Token usage extracted elsewhere or not available in sc
                    outcome_status="success",
                    confidence_score=1.0,
                    failure_reason=None,
                    recovery_actions_json=None,
                    final_resolution="success"
                )
        except Exception as e:
            error_str = str(e).lower()
            if error_str == "empty_retrieval":
                error_type = "empty_retrieval"
            elif "timeout" in error_str:
                error_type = "timeout"
            elif "tool" in error_str:
                error_type = "tool_error"
            else:
                error_type = "unhandled"

            with get_session_with_current_tenant() as db_session:
                recovery_strategy = evaluate_healing_policy(
                    db_session=db_session,
                    agent_id=setup_info.get("agent_id"),
                    error_type=error_type,
                    error_message=str(e),
                    current_retry_count=retry_count
                )
                
                sc = kwargs.get("state_container")
                tools_called = [json.loads(tc.model_dump_json()) for tc in sc.get_tool_calls()] if sc else None
                
                record_agent_run_trace(
                    db_session=db_session,
                    session_id=setup_info.get("session_id"),
                    agent_id=setup_info.get("agent_id"),
                    user_id=setup_info.get("user_id"),
                    prompt_template_id=None,
                    prompt_version_id=None,
                    model_name=model_llm.config.model_name,
                    retrieval_strategy="standard",
                    tool_plan_json=None,
                    tools_called_json={"tools": tools_called} if tools_called else None,
                    citations_json=list(sc.get_all_search_docs().keys()) if sc else None,
                    latency_ms=int((time.time() - start_time) * 1000),
                    token_usage_json=None,
                    outcome_status="error",
                    confidence_score=0.0,
                    failure_reason=str(e),
                    recovery_actions_json=recovery_strategy,
                    final_resolution=recovery_strategy.get("action", "fail")
                )

            if recovery_strategy.get("action") == "retry":
                retry_count += 1
                logger.info(f"Self-healing: retrying... Strategy: {recovery_strategy.get('strategy')}")
                time.sleep(1)
                continue
            else:
                raise e
