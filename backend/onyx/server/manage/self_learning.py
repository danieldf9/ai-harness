from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from onyx.auth.users import current_curator_or_admin_user
from onyx.db.engine.sql_engine import get_session
from onyx.db.models import User
from onyx.db.models import HealingPolicy
from onyx.db.models import LearningRecommendation
from onyx.db.models import AutoOptimizationRule
from onyx.db.models import PromptVersion
from onyx.db.prompt_registry import set_prompt_versions_traffic
from onyx.utils.logger import setup_logger
import json

logger = setup_logger()

router = APIRouter(prefix="/admin/self-learning")

class HealingPolicyCreate(BaseModel):
    name: str
    target_type: str
    target_id: Optional[str] = None
    enabled: bool = True
    low_confidence_threshold: Optional[float] = None
    max_retries: int = 3
    allow_model_fallback: bool = True
    allow_retrieval_expansion: bool = True
    allow_retrieval_narrowing: bool = True
    allow_tool_replan: bool = True
    allow_prompt_fallback: bool = True
    allow_human_escalation: bool = True

class HealingPolicyResponse(HealingPolicyCreate):
    id: int

@router.get("/policies", response_model=List[HealingPolicyResponse])
def get_healing_policies(
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Get all self-healing policies."""
    policies = db_session.execute(select(HealingPolicy)).scalars().all()
    return [HealingPolicyResponse(
        id=p.id,
        name=p.name,
        target_type=p.target_type,
        target_id=p.target_id,
        enabled=p.enabled,
        low_confidence_threshold=p.low_confidence_threshold,
        max_retries=p.max_retries,
        allow_model_fallback=p.allow_model_fallback,
        allow_retrieval_expansion=p.allow_retrieval_expansion,
        allow_retrieval_narrowing=p.allow_retrieval_narrowing,
        allow_tool_replan=p.allow_tool_replan,
        allow_prompt_fallback=p.allow_prompt_fallback,
        allow_human_escalation=p.allow_human_escalation
    ) for p in policies]

@router.post("/policies", response_model=HealingPolicyResponse)
def create_healing_policy(
    policy: HealingPolicyCreate,
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Create a new self-healing policy."""
    db_policy = HealingPolicy(
        name=policy.name,
        target_type=policy.target_type,
        target_id=policy.target_id,
        enabled=policy.enabled,
        low_confidence_threshold=policy.low_confidence_threshold,
        max_retries=policy.max_retries,
        allow_model_fallback=policy.allow_model_fallback,
        allow_retrieval_expansion=policy.allow_retrieval_expansion,
        allow_retrieval_narrowing=policy.allow_retrieval_narrowing,
        allow_tool_replan=policy.allow_tool_replan,
        allow_prompt_fallback=policy.allow_prompt_fallback,
        allow_human_escalation=policy.allow_human_escalation
    )
    db_session.add(db_policy)
    db_session.commit()
    db_session.refresh(db_policy)
    return HealingPolicyResponse(
        id=db_policy.id,
        **policy.dict()
    )

@router.delete("/policies/{policy_id}")
def delete_healing_policy(
    policy_id: int,
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Delete a self-healing policy."""
    policy = db_session.get(HealingPolicy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Healing policy not found")
        
    db_session.delete(policy)
    db_session.commit()
    logger.info(f"Deleted healing policy {policy_id} by user {user.id}")
    return {"status": "deleted"}

class RecommendationResponse(BaseModel):
    id: int
    target_type: str
    target_id: str
    recommendation_type: str
    current_config_json: Dict[str, Any]
    proposed_config_json: Dict[str, Any]
    evidence_json: Dict[str, Any]
    confidence_score: Optional[float]
    status: str

@router.get("/recommendations", response_model=List[RecommendationResponse])
def get_recommendations(
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Get all learning recommendations pending review."""
    recs = db_session.execute(
        select(LearningRecommendation)
    ).scalars().all()
    
    return [RecommendationResponse(
        id=r.id,
        target_type=r.target_type,
        target_id=r.target_id,
        recommendation_type=r.recommendation_type,
        current_config_json=r.current_config_json,
        proposed_config_json=r.proposed_config_json,
        evidence_json=r.evidence_json,
        confidence_score=r.confidence_score,
        status=r.status
    ) for r in recs]

@router.post("/recommendations/{rec_id}/approve")
def approve_recommendation(
    rec_id: int,
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Approve a learning recommendation."""
    rec = db_session.get(LearningRecommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    # In a full implementation, this would actually apply the changes.
    # For now, just mark it as approved.
    rec.status = "approved"
    rec.reviewed_by_user_id = user.id
    db_session.commit()
    logger.info(json.dumps({
        "event": "self_learning_approved",
        "recommendation_id": rec.id,
        "target_type": rec.target_type,
        "target_id": rec.target_id,
        "reviewed_by_user_id": str(user.id),
        "description": "Admin approved learning recommendation"
    }))
    return {"status": "approved"}

@router.post("/recommendations/{rec_id}/reject")
def reject_recommendation(
    rec_id: int,
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Reject a learning recommendation."""
    rec = db_session.get(LearningRecommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    rec.status = "rejected"
    rec.reviewed_by_user_id = user.id
    db_session.commit()
    logger.info(json.dumps({
        "event": "self_learning_rejected",
        "recommendation_id": rec.id,
        "target_type": rec.target_type,
        "target_id": rec.target_id,
        "reviewed_by_user_id": str(user.id),
        "description": "Admin rejected learning recommendation"
    }))
    return {"status": "rejected"}

@router.post("/recommendations/{rec_id}/rollback")
def rollback_recommendation(
    rec_id: int,
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Rollback an applied learning recommendation to its previous configuration."""
    rec = db_session.get(LearningRecommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    if rec.status != "applied":
        raise HTTPException(status_code=400, detail="Only applied recommendations can be rolled back")
        
    prev_version_id = rec.current_config_json.get("previous_version_id")
    if not prev_version_id:
        raise HTTPException(status_code=400, detail="No previous version recorded for rollback")
        
    prev_version = db_session.get(PromptVersion, prev_version_id)
    if not prev_version:
        raise HTTPException(status_code=404, detail="Previous prompt version not found")
        
    set_prompt_versions_traffic(
        template_id=prev_version.prompt_template_id,
        traffic_allocations={prev_version_id: 100.0},
        db_session=db_session
    )
    
    rec.status = "rolled_back"
    db_session.commit()
    
    logger.info(json.dumps({
        "event": "self_learning_rolled_back",
        "recommendation_id": rec.id,
        "target_type": rec.target_type,
        "target_id": rec.target_id,
        "rolled_back_by_user_id": str(user.id),
        "restored_version_id": prev_version_id,
        "description": "Admin rolled back an auto-optimization"
    }))
    
    return {"status": "rolled_back"}

class AutoOptimizationRuleCreate(BaseModel):
    target_type: str
    target_id: Optional[str] = None
    is_dry_run: bool = True
    min_confidence_score: float = 0.8
    require_human_approval: bool = True

class AutoOptimizationRuleResponse(AutoOptimizationRuleCreate):
    id: int

@router.get("/auto-optimization", response_model=List[AutoOptimizationRuleResponse])
def get_auto_optimization_rules(
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Get all auto-optimization rules."""
    rules = db_session.execute(select(AutoOptimizationRule)).scalars().all()
    return [AutoOptimizationRuleResponse(
        id=r.id,
        target_type=r.scope_type,
        target_id=r.scope_id,
        is_dry_run=r.guardrails_json.get("is_dry_run", True),
        min_confidence_score=r.guardrails_json.get("min_confidence_score", 0.8),
        require_human_approval=r.guardrails_json.get("require_human_approval", True)
    ) for r in rules]

@router.post("/auto-optimization", response_model=AutoOptimizationRuleResponse)
def create_auto_optimization_rule(
    rule: AutoOptimizationRuleCreate,
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Create a new auto-optimization rule."""
    db_rule = AutoOptimizationRule(
        name=f"Rule for {rule.target_type} {rule.target_id or 'global'}",
        scope_type=rule.target_type,
        scope_id=rule.target_id,
        rule_type="prompt_update",
        guardrails_json={
            "is_dry_run": rule.is_dry_run,
            "min_confidence_score": rule.min_confidence_score,
            "require_human_approval": rule.require_human_approval
        }
    )
    db_session.add(db_rule)
    db_session.commit()
    db_session.refresh(db_rule)
    return AutoOptimizationRuleResponse(
        id=db_rule.id,
        **rule.dict()
    )

@router.delete("/auto-optimization/{rule_id}")
def delete_auto_optimization_rule(
    rule_id: int,
    user: User = Depends(current_curator_or_admin_user),
    db_session: Session = Depends(get_session)
):
    """Delete an auto-optimization rule."""
    rule = db_session.get(AutoOptimizationRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Auto-optimization rule not found")
        
    db_session.delete(rule)
    db_session.commit()
    logger.info(f"Deleted auto-optimization rule {rule_id} by user {user.id}")
    return {"status": "deleted"}
