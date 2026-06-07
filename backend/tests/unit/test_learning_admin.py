import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from onyx.server.manage.self_learning import approve_recommendation, rollback_recommendation
from onyx.db.models import LearningRecommendation, PromptVersion
from onyx.db.models import User

def test_approve_recommendation():
    mock_session = MagicMock()
    mock_user = User(id="user_123")
    
    rec = LearningRecommendation(
        id=1,
        status="pending",
        target_type="agent",
        target_id="1"
    )
    
    mock_session.get.return_value = rec
    
    response = approve_recommendation(
        rec_id=1,
        user=mock_user,
        db_session=mock_session
    )
    
    assert response["status"] == "approved"
    assert rec.status == "approved"
    assert rec.reviewed_by_user_id == mock_user.id
    assert mock_session.commit.called

def test_rollback_recommendation():
    mock_session = MagicMock()
    mock_user = User(id="user_123")
    
    rec = LearningRecommendation(
        id=1,
        status="applied",
        target_type="agent",
        target_id="1",
        current_config_json={"previous_version_id": 99}
    )
    
    prev_version = PromptVersion(
        id=99,
        prompt_template_id=10
    )
    
    def mock_get(model, id):
        if model == LearningRecommendation:
            return rec
        if model == PromptVersion:
            return prev_version
        return None
        
    mock_session.get.side_effect = mock_get
    
    with patch("onyx.server.manage.self_learning.set_prompt_versions_traffic") as mock_set_traffic:
        response = rollback_recommendation(
            rec_id=1,
            user=mock_user,
            db_session=mock_session
        )
        
        assert response["status"] == "rolled_back"
        assert rec.status == "rolled_back"
        mock_set_traffic.assert_called_once_with(
            template_id=10,
            traffic_allocations={99: 100.0},
            db_session=mock_session
        )
        assert mock_session.commit.called

def test_rollback_recommendation_not_applied():
    mock_session = MagicMock()
    mock_user = User(id="user_123")
    
    rec = LearningRecommendation(
        id=1,
        status="pending",
        target_type="agent",
        target_id="1"
    )
    
    mock_session.get.return_value = rec
    
    with pytest.raises(HTTPException) as excinfo:
        rollback_recommendation(
            rec_id=1,
            user=mock_user,
            db_session=mock_session
        )
    
    assert excinfo.value.status_code == 400
    assert "Only applied recommendations can be rolled back" in excinfo.value.detail
