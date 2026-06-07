from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from onyx.db.models import UserFeedbackSignal
from onyx.db.models import LearningRecommendation
from onyx.db.models import AgentRunTrace
from onyx.utils.logger import setup_logger

logger = setup_logger()

def process_feedback_signal(
    db_session: Session,
    chat_message_id: int,
    is_positive: Optional[bool],
    feedback_text: Optional[str],
    user_id: Optional[UUID],
    predefined_feedback: Optional[str]
) -> None:
    """
    Process incoming user feedback. Creates a UserFeedbackSignal and potentially 
    generates a LearningRecommendation for admin review.
    """
    try:
        # We try to correlate the chat message to an AgentRunTrace.
        # For simplicity, we just use the most recent trace for this user's session.
        # A more robust system would link ChatMessage directly to AgentRunTrace.
        # We will retrieve the latest trace for this user.
        trace_stmt = select(AgentRunTrace).where(AgentRunTrace.user_id == user_id).order_by(AgentRunTrace.created_at.desc()).limit(1)
        latest_trace = db_session.execute(trace_stmt).scalar_one_or_none()
        
        signal_type = "positive" if is_positive else "negative" if is_positive is False else "neutral"
        score = 1.0 if is_positive else 0.0 if is_positive is False else 0.5
        
        signal = UserFeedbackSignal(
            run_trace_id=latest_trace.id if latest_trace else None,
            user_id=user_id,
            agent_id=latest_trace.agent_id if latest_trace else None,
            signal_type=signal_type,
            score=score,
            comment=feedback_text,
            correction_text=feedback_text if is_positive is False and feedback_text else None,
            metadata_json={"chat_message_id": chat_message_id, "predefined_feedback": predefined_feedback}
        )
        db_session.add(signal)
        
        # If it's negative and has feedback text, we generate a recommendation for the admin
        if is_positive is False and feedback_text:
            rec = LearningRecommendation(
                target_type="agent",
                target_id=str(latest_trace.agent_id) if latest_trace and latest_trace.agent_id else "global",
                recommendation_type="prompt_update",
                current_config_json={"prompt": "Current base prompt..."},
                proposed_config_json={"prompt_correction": f"Include correction: {feedback_text}"},
                evidence_json={"user_feedback": feedback_text, "chat_message_id": chat_message_id},
                confidence_score=0.8,
                impact_estimate_json={"description": "Improves answer accuracy based on user feedback."},
                status="pending"
            )
            db_session.add(rec)
            
        db_session.commit()
    except Exception as e:
        logger.error(f"Error processing feedback signal: {e}")
        db_session.rollback()
