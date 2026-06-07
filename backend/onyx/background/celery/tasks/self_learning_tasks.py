from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session
import json

from onyx.db.engine.sql_engine import get_session_with_tenant
from onyx.db.models import UserFeedbackSignal
from onyx.db.models import LearningRecommendation
from onyx.db.models import AutoOptimizationRule
from onyx.db.prompt_registry import fetch_effective_prompt, insert_prompt_version, set_prompt_versions_traffic
from onyx.utils.logger import setup_logger

logger = setup_logger()

@shared_task(
    name="generate_learning_recommendations",
    soft_time_limit=300,
    time_limit=360,
    max_retries=3
)
def generate_learning_recommendations(tenant_id: str) -> None:
    """
    Periodically processes recent negative feedback and generates
    LearningRecommendations.
    """
    logger.info(f"Starting generate_learning_recommendations for tenant {tenant_id}")
    with get_session_with_tenant(tenant_id) as db_session:
        # Fetch unresolved negative feedback
        signals = db_session.execute(
            select(UserFeedbackSignal)
            .where(UserFeedbackSignal.signal_type == "negative")
            # In a real app we'd filter for unprocessed ones
            .limit(10)
        ).scalars().all()
        
        for signal in signals:
            # Check if a recommendation already exists for this signal
            existing = db_session.execute(
                select(LearningRecommendation)
                .where(LearningRecommendation.target_type == "agent")
                .where(LearningRecommendation.target_id == str(signal.agent_id) if signal.agent_id else "global")
            ).scalars().first()
            
            if existing:
                continue
                
            rec = LearningRecommendation(
                target_type="agent",
                target_id=str(signal.agent_id) if signal.agent_id else "global",
                recommendation_type="prompt_update",
                current_config_json={"prompt": "Current base prompt..."},
                proposed_config_json={"prompt_correction": f"Incorporate feedback: {signal.correction_text or signal.comment}"},
                evidence_json={
                    "user_feedback": signal.comment,
                    "signal_id": signal.id
                },
                confidence_score=0.75,
                impact_estimate_json={"description": "Based on negative user feedback."},
                status="pending"
            )
            db_session.add(rec)
            
        db_session.commit()
    logger.info("Finished generate_learning_recommendations")

@shared_task(
    name="apply_auto_optimizations",
    soft_time_limit=300,
    time_limit=360,
    max_retries=3
)
def apply_auto_optimizations(tenant_id: str) -> None:
    """
    Periodically checks for approved learning recommendations and applies them.
    (This implements the auto-optimization and rollback capability conceptually)
    """
    logger.info(f"Starting apply_auto_optimizations for tenant {tenant_id}")
    with get_session_with_tenant(tenant_id) as db_session:
        # Fetch approved recommendations
        recs = db_session.execute(
            select(LearningRecommendation)
            .where(LearningRecommendation.status == "approved")
            .limit(10)
        ).scalars().all()
        
        # In a full system, we'd look up AutoOptimizationRule based on the agent or global config.
        # We can simulate dry-run mode via AutoOptimizationRule.
        global_rule = db_session.execute(
            select(AutoOptimizationRule)
            .where(AutoOptimizationRule.scope_type == "global")
        ).scalars().first()
        
        is_dry_run = global_rule.guardrails_json.get("is_dry_run", True) if global_rule else True

        for rec in recs:
            # Here we update the actual Prompt or Agent definition
            # based on proposed_config_json
            if is_dry_run:
                logger.info(f"Dry-run mode: Simulating application of recommendation {rec.id} for {rec.target_type} {rec.target_id}")
                rec.status = "auto_approved_dry_run"
            else:
                logger.info(f"Applying recommendation {rec.id} for {rec.target_type} {rec.target_id}")
                try:
                    # Attempt to find the effective prompt for this agent
                    active_version = fetch_effective_prompt(rec.target_type, rec.target_id, db_session)
                    if active_version:
                        template_id = active_version.prompt_template_id
                        # Store previous version for rollback
                        rec.current_config_json = {"previous_version_id": active_version.id}
                        
                        new_content = active_version.content + "\n\n# System Policy Update\n" + rec.proposed_config_json.get("prompt_correction", "")
                        
                        # Create new version
                        new_version = insert_prompt_version(
                            template_id=template_id,
                            content=new_content,
                            created_by_user_id=None,
                            db_session=db_session
                        )
                        
                        # Set 100% traffic to new version
                        set_prompt_versions_traffic(
                            template_id=template_id,
                            traffic_allocations={new_version.id: 100.0},
                            db_session=db_session
                        )
                        rec.status = "applied"
                        logger.info(json.dumps({
                            "event": "self_learning_applied",
                            "recommendation_id": rec.id,
                            "target_type": rec.target_type,
                            "target_id": rec.target_id,
                            "previous_version_id": active_version.id,
                            "new_version_id": new_version.id,
                            "description": "Auto-optimization successfully applied"
                        }))
                    else:
                        logger.warning(f"No active prompt found for {rec.target_type} {rec.target_id}. Cannot apply.")
                        rec.status = "error"
                except Exception as e:
                    logger.error(f"Failed to apply recommendation {rec.id}: {e}")
                    rec.status = "error"
            
        db_session.commit()
    logger.info("Finished apply_auto_optimizations")
