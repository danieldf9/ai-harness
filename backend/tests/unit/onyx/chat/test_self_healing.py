import pytest
from unittest.mock import MagicMock, patch
from onyx.chat.self_healing import evaluate_healing_policy
from onyx.db.models import HealingPolicy

@patch('onyx.chat.self_healing.get_healing_policy')
def test_evaluate_healing_policy_max_retries_exceeded(mock_get_policy):
    mock_policy = MagicMock(spec=HealingPolicy)
    mock_policy.max_retries = 3
    mock_policy.allow_human_escalation = True
    mock_get_policy.return_value = mock_policy
    
    result = evaluate_healing_policy(
        db_session=MagicMock(),
        agent_id=1,
        error_type="timeout",
        error_message="timeout",
        current_retry_count=3
    )
    assert result["action"] == "escalate"
    assert result["reason"] == "max_retries_exceeded"
    
@patch('onyx.chat.self_healing.get_healing_policy')
def test_evaluate_healing_policy_no_policy(mock_get_policy):
    mock_get_policy.return_value = None
    
    result = evaluate_healing_policy(
        db_session=MagicMock(),
        agent_id=1,
        error_type="timeout",
        error_message="timeout",
        current_retry_count=0
    )
    assert result["action"] == "fail"
    assert result["reason"] == "no_policy"

@patch('onyx.chat.self_healing.get_healing_policy')
def test_evaluate_healing_policy_tool_error(mock_get_policy):
    mock_policy = MagicMock(spec=HealingPolicy)
    mock_policy.max_retries = 3
    mock_policy.allow_tool_replan = True
    mock_get_policy.return_value = mock_policy
    
    result = evaluate_healing_policy(
        db_session=MagicMock(),
        agent_id=1,
        error_type="tool_error",
        error_message="Action failed",
        current_retry_count=0
    )
    assert result["action"] == "retry"
    assert result["strategy"] == "tool_replan"
