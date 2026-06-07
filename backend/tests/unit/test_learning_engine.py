import pytest
from unittest.mock import MagicMock, patch
import uuid

from onyx.background.celery.tasks.self_learning_tasks import generate_learning_recommendations, apply_auto_optimizations
from onyx.db.models import UserFeedbackSignal, LearningRecommendation, AutoOptimizationRule

def test_generate_learning_recommendations_creates_rec():
    mock_session = MagicMock()
    
    # Mock some negative feedback
    signal = UserFeedbackSignal(
        id=1,
        agent_id=1,
        signal_type="negative",
        comment="This is wrong",
        correction_text="Should be this instead",
    )
    
    # Mock db_session.execute().scalars().all() / first()
    mock_session.execute.return_value.scalars.return_value.all.return_value = [signal]
    # For the 'existing' check, return None
    mock_session.execute.return_value.scalars.return_value.first.return_value = None
    
    with patch("onyx.background.celery.tasks.self_learning_tasks.get_session_with_tenant") as mock_get_session:
        # Mock context manager
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        generate_learning_recommendations("test_tenant")
        
        # Verify add was called with a LearningRecommendation
        assert mock_session.add.called
        added_rec = mock_session.add.call_args[0][0]
        assert isinstance(added_rec, LearningRecommendation)
        assert added_rec.target_id == "1"
        assert added_rec.recommendation_type == "prompt_update"
        assert "Should be this instead" in added_rec.proposed_config_json["prompt_correction"]

def test_apply_auto_optimizations_dry_run():
    mock_session = MagicMock()
    
    rec = LearningRecommendation(
        id=10,
        target_type="agent",
        target_id="1",
        status="approved",
        proposed_config_json={"prompt_correction": "Fix this"},
    )
    
    rule = AutoOptimizationRule(guardrails_json={"is_dry_run": True})
    
    # 1. Fetch approved recs
    # 2. Fetch global rule
    def mock_execute_side_effect(stmt, *args, **kwargs):
        mock_result = MagicMock()
        stmt_str = str(stmt).lower()
        if "learning_recommendation" in stmt_str:
            mock_result.scalars().all.return_value = [rec]
        else:
            mock_result.scalars().first.return_value = rule
        return mock_result
    
    mock_session.execute.side_effect = mock_execute_side_effect
    
    with patch("onyx.background.celery.tasks.self_learning_tasks.get_session_with_tenant") as mock_get_session:
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        apply_auto_optimizations("test_tenant")
        
        assert rec.status == "auto_approved_dry_run"
