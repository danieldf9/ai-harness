import pytest
from unittest.mock import MagicMock
from onyx.chat.feedback_processing import process_feedback_signal
from onyx.db.models import UserFeedbackSignal
from onyx.db.models import LearningRecommendation

def test_process_feedback_signal_positive():
    db_session = MagicMock()
    # Mock trace lookup
    mock_trace = MagicMock()
    mock_trace.id = 1
    mock_trace.agent_id = 1
    
    mock_stmt = MagicMock()
    mock_scalar = MagicMock(return_value=mock_trace)
    mock_execute = MagicMock()
    mock_execute.scalar_one_or_none = mock_scalar
    db_session.execute.return_value = mock_execute
    
    process_feedback_signal(
        db_session=db_session,
        chat_message_id=100,
        is_positive=True,
        feedback_text="Great answer!",
        user_id=None,
        predefined_feedback=None
    )
    
    # Verify UserFeedbackSignal was added
    assert db_session.add.call_count == 1
    added_obj = db_session.add.call_args[0][0]
    assert isinstance(added_obj, UserFeedbackSignal)
    assert added_obj.signal_type == "positive"
    assert added_obj.score == 1.0
    
def test_process_feedback_signal_negative_with_text():
    db_session = MagicMock()
    mock_trace = MagicMock()
    mock_trace.id = 1
    mock_trace.agent_id = 1
    
    mock_scalar = MagicMock(return_value=mock_trace)
    mock_execute = MagicMock()
    mock_execute.scalar_one_or_none = mock_scalar
    db_session.execute.return_value = mock_execute
    
    process_feedback_signal(
        db_session=db_session,
        chat_message_id=101,
        is_positive=False,
        feedback_text="Wrong answer. Use the metric table.",
        user_id=None,
        predefined_feedback=None
    )
    
    # Should add both UserFeedbackSignal and LearningRecommendation
    assert db_session.add.call_count == 2
    
    signal = db_session.add.call_args_list[0][0][0]
    rec = db_session.add.call_args_list[1][0][0]
    
    assert isinstance(signal, UserFeedbackSignal)
    assert signal.signal_type == "negative"
    assert signal.correction_text == "Wrong answer. Use the metric table."
    
    assert isinstance(rec, LearningRecommendation)
    assert rec.target_type == "agent"
    assert rec.recommendation_type == "prompt_update"
