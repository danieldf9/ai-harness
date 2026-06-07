# Self-Learning & Self-Healing Framework

## Overview
Onyx now includes a robust **Self-Learning and Self-Healing Framework** designed to maximize agent reliability and continuously improve system performance through a governed feedback loop.

This framework operates in two distinct but connected halves:
1. **Self-Healing (Runtime Recovery):** Real-time interception of agent execution failures, timeouts, and low-confidence responses, followed by policy-driven recovery attempts without human intervention.
2. **Self-Learning (Continuous Improvement):** Background analysis of agent execution traces and user feedback to propose and optionally auto-apply deterministic system optimizations (e.g., prompt revisions).

---

## 1. Self-Healing (Runtime)

The self-healing mechanism is engaged during the standard agent execution flow (e.g., via `llm_loop.py`).

### How It Works
- Whenever an agent run encounters an error (e.g., `timeout`, `empty_retrieval`, `tool_error`, or `low_confidence`), the execution is caught and evaluated against the assigned **Healing Policy**.
- **Healing Policies** are defined per-agent or globally. They outline the permissible bounds for recovery (e.g., `max_retries`, `allow_model_fallback`, `allow_tool_replan`).
- If recovery is permitted, a new strategy is devised (e.g., fallback to a cheaper/faster model on timeout, expand retrieval bounds if context is missing) and the run is retried.
- Every run and recovery attempt is logged fully to the database as an `AgentRunTrace`.

### Governance
- Retries are strictly capped by `max_retries`.
- Strategies are explicit and bounded. The system does not attempt unbounded trial-and-error.

---

## 2. Self-Learning (Background)

The self-learning engine uses asynchronous Celery tasks to process accumulated traces and explicit User Feedback.

### How It Works
- The `generate_learning_recommendations` task scans the `UserFeedbackSignal` table for negative evaluations.
- When it detects systemic issues or explicit corrections from users, it synthesizes a `LearningRecommendation`. For example, it will propose a "prompt update" incorporating the user's correction text.
- The `apply_auto_optimizations` task scans for *approved* recommendations.
- If Auto-Optimization is enabled for the agent (and not in `dry_run` mode), approved recommendations are immediately applied.

### Non-Destructive Prompt Application
When a prompt update is applied:
- The system does **not** overwrite the existing prompt.
- It leverages the `PromptRegistry` to create a brand new draft `PromptVersion`.
- Traffic is then routed 100% to this new version, preserving the previous configuration.

---

## 3. Administration and Rollback

All self-learning and self-healing configurations are managed via the **Admin Dashboard** (`/admin/self-learning`).

- **Dashboard:** View health stats, feedback, policies, and pending recommendations.
- **Approval Workflow:** Admins can manually approve or reject any generated `LearningRecommendation`.
- **Rollback:** Every applied recommendation snapshots the `previous_version_id` of the prompt. Admins can click "Rollback" in the UI to instantly restore the previous configuration and traffic routing.
- **Audit Logging:** Every administrative action (Approve, Reject, Apply, Rollback) triggers a structured JSON log via `onyx.utils.logger` to ensure full enterprise auditability.
