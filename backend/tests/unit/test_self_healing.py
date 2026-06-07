import pytest
from unittest.mock import MagicMock, patch

from onyx.chat.self_healing import evaluate_healing_policy
from onyx.db.models import HealingPolicy

def test_evaluate_healing_policy_timeout_with_fallback():
    mock_session = MagicMock()
    policy = HealingPolicy(
        max_retries=3,
        allow_model_fallback=True,
        allow_human_escalation=True,
    )
    
    with patch("onyx.chat.self_healing.get_healing_policy", return_value=policy):
        result = evaluate_healing_policy(
            db_session=mock_session,
            agent_id=1,
            error_type="timeout",
            error_message="Connection timed out",
            current_retry_count=0
        )
        assert result["action"] == "retry"
        assert result["strategy"] == "model_fallback"

def test_evaluate_healing_policy_max_retries():
    mock_session = MagicMock()
    policy = HealingPolicy(
        max_retries=3,
        allow_human_escalation=True,
    )
    
    with patch("onyx.chat.self_healing.get_healing_policy", return_value=policy):
        result = evaluate_healing_policy(
            db_session=mock_session,
            agent_id=1,
            error_type="timeout",
            error_message="Connection timed out",
            current_retry_count=3
        )
        assert result["action"] == "escalate"
        assert result["reason"] == "max_retries_exceeded"

def test_evaluate_healing_policy_low_confidence():
    mock_session = MagicMock()
    policy = HealingPolicy(
        max_retries=3,
        low_confidence_threshold=0.7,
    )
    
    with patch("onyx.chat.self_healing.get_healing_policy", return_value=policy):
        result = evaluate_healing_policy(
            db_session=mock_session,
            agent_id=1,
            error_type="low_confidence",
            error_message="Score was 0.5",
            current_retry_count=0
        )
        assert result["action"] == "ask_clarifying_question"
        assert result["strategy"] == "clarification"

def test_no_policy_fails_gracefully():
    mock_session = MagicMock()
    with patch("onyx.chat.self_healing.get_healing_policy", return_value=None):
        result = evaluate_healing_policy(
            db_session=mock_session,
            agent_id=1,
            error_type="timeout",
            error_message="Timeout",
            current_retry_count=0
        )
        assert result["action"] == "fail"
        assert result["reason"] == "no_policy"
