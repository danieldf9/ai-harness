import useSWR from "swr";
import { errorHandlingFetcher } from "@/lib/fetcher";

export interface HealingPolicy {
  id: number;
  name: string;
  target_type: string;
  target_id: string | null;
  enabled: boolean;
  low_confidence_threshold: number | null;
  max_retries: number;
  allow_model_fallback: boolean;
  allow_retrieval_expansion: boolean;
  allow_retrieval_narrowing: boolean;
  allow_tool_replan: boolean;
  allow_prompt_fallback: boolean;
  allow_human_escalation: boolean;
}

export interface LearningRecommendation {
  id: number;
  target_type: string;
  target_id: string;
  recommendation_type: string;
  current_config_json: any;
  proposed_config_json: any;
  evidence_json: any;
  confidence_score: number | null;
  status: string;
}

export interface AutoOptimizationRule {
  id: number;
  target_type: string;
  target_id: string | null;
  is_dry_run: boolean;
  min_confidence_score: number;
  require_human_approval: boolean;
}

export function useHealingPolicies() {
  const { data, error, mutate } = useSWR<HealingPolicy[]>(
    "/api/admin/self-learning/policies",
    errorHandlingFetcher
  );
  return {
    policies: data || [],
    isLoading: !error && !data,
    isError: error,
    refresh: mutate,
  };
}

export function useLearningRecommendations() {
  const { data, error, mutate } = useSWR<LearningRecommendation[]>(
    "/api/admin/self-learning/recommendations",
    errorHandlingFetcher
  );
  return {
    recommendations: data || [],
    isLoading: !error && !data,
    isError: error,
    refresh: mutate,
  };
}

export function useAutoOptimizationRules() {
  const { data, error, mutate } = useSWR<AutoOptimizationRule[]>(
    "/api/admin/self-learning/auto-optimization",
    errorHandlingFetcher
  );
  return {
    rules: data || [],
    isLoading: !error && !data,
    isError: error,
    refresh: mutate,
  };
}

export async function approveRecommendation(id: number) {
  const res = await fetch(`/api/admin/self-learning/recommendations/${id}/approve`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to approve recommendation");
  }
  return res.json();
}

export async function rejectRecommendation(id: number) {
  const res = await fetch(`/api/admin/self-learning/recommendations/${id}/reject`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to reject recommendation");
  }
  return res.json();
}

export async function rollbackRecommendation(id: number) {
  const res = await fetch(`/api/admin/self-learning/recommendations/${id}/rollback`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to rollback recommendation");
  }
  return res.json();
}

export async function createHealingPolicy(policy: Partial<HealingPolicy>) {
  const res = await fetch("/api/admin/self-learning/policies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: policy.name || "New Policy",
      target_type: policy.target_type || "global",
      target_id: policy.target_id || null,
      enabled: policy.enabled ?? true,
      low_confidence_threshold: policy.low_confidence_threshold || 0.7,
      max_retries: policy.max_retries || 3,
      allow_model_fallback: policy.allow_model_fallback ?? true,
      allow_retrieval_expansion: policy.allow_retrieval_expansion ?? true,
      allow_retrieval_narrowing: policy.allow_retrieval_narrowing ?? true,
      allow_tool_replan: policy.allow_tool_replan ?? true,
      allow_prompt_fallback: policy.allow_prompt_fallback ?? false,
      allow_human_escalation: policy.allow_human_escalation ?? true,
    }),
  });
  if (!res.ok) throw new Error("Failed to create healing policy");
  return res.json();
}

export async function createAutoOptimizationRule(rule: Partial<AutoOptimizationRule>) {
  const res = await fetch("/api/admin/self-learning/auto-optimization", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_type: rule.target_type || "global",
      target_id: rule.target_id || null,
      is_dry_run: rule.is_dry_run ?? true,
      min_confidence_score: rule.min_confidence_score || 0.8,
      require_human_approval: rule.require_human_approval ?? true,
    }),
  });
  if (!res.ok) throw new Error("Failed to create optimization rule");
  return res.json();
}

export async function deleteHealingPolicy(id: number) {
  const res = await fetch(`/api/admin/self-learning/policies/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete healing policy");
  return res.json();
}

export async function deleteAutoOptimizationRule(id: number) {
  const res = await fetch(`/api/admin/self-learning/auto-optimization/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete auto-optimization rule");
  return res.json();
}
