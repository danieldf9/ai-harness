# Self-Learning & Self-Healing Framework

The Onyx Self-Learning & Self-Healing framework is an enterprise-safe, observable, and governed system designed to automatically recover from execution errors (healing) and continuously improve agent reliability over time (learning).

## Key Concepts

- **Self-Healing (Runtime):** Real-time recovery from tool failures, low-confidence responses, or context retrieval issues. Configured via `HealingPolicy`.
- **Self-Learning (Offline):** Closed-loop improvement using user feedback. The system processes negative feedback signals, generating `LearningRecommendation`s for admins to review.
- **Admin Governance:** No uncontrolled AI behavior. All optimizations (like prompt updates) must be approved by an administrator before being applied.

## Core Components

1. **Healing Policy (`HealingPolicy`)**
   Defines rules for fallback behavior. You can configure global or per-agent policies:
   - `allow_model_fallback`: Switch to a different LLM if the primary times out.
   - `allow_retrieval_expansion`: Widen the search if no context is found.
   - `allow_tool_replan`: Ask the LLM to rethink if a tool call fails.

2. **Feedback Processing Pipeline**
   When users provide feedback (thumbs down), a `UserFeedbackSignal` is recorded. If there is actionable text ("e.g. This was incorrect, use the metrics table"), a background job evaluates it and generates a `LearningRecommendation`.

3. **Admin Governance & Auto-Optimization**
   Admins can review pending `LearningRecommendation`s. Approved recommendations are applied periodically by the Celery `apply_auto_optimizations` task.
   - **Dry Run Mode:** `AutoOptimizationRule` entities can be set to `is_dry_run = True` to simulate the application of rules without modifying the active prompts.

## Admin API Endpoints

The framework exposes REST endpoints for governance under `/admin/self-learning`:

### 1. View & Manage Healing Policies
- `GET /admin/self-learning/policies`: List all healing policies.
- `POST /admin/self-learning/policies`: Create a new healing policy.

### 2. Review Learning Recommendations
- `GET /admin/self-learning/recommendations`: List pending optimizations generated from user feedback.
- `POST /admin/self-learning/recommendations/{id}/approve`: Approve a recommendation to be applied by the auto-optimizer.
- `POST /admin/self-learning/recommendations/{id}/reject`: Reject a recommendation.

## Background Tasks

Celery beat schedules the offline learning tasks:
- `generate-learning-recommendations`: Runs every 30 minutes. Aggregates negative feedback and creates actionable recommendations.
- `apply-auto-optimizations`: Runs hourly. Updates the agent configuration with approved optimizations.

## Traceability

Every agent execution that undergoes healing or learning is recorded in the `AgentRunTrace` table. This provides a complete audit log of what strategies were attempted, what failed, and how the system recovered.
