import useSWR from "swr";
import { errorHandlingFetcher } from "@/lib/fetcher";

export interface PromptTemplate {
  id: number;
  name: string;
  description: string | null;
  owner_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface PromptVersion {
  id: number;
  prompt_template_id: number;
  version_number: number;
  content: string;
  created_by_user_id: string | null;
  created_at: string;
  is_active: boolean;
  traffic_percentage: number;
}

export interface PromptAssignment {
  id: number;
  prompt_template_id: number;
  target_type: string;
  target_id: string;
  created_at: string;
}

export function usePromptTemplates() {
  const { data, error, isLoading, mutate } = useSWR<PromptTemplate[]>(
    "/api/manage/prompt-registry/templates",
    errorHandlingFetcher
  );
  return {
    templates: data || [],
    isLoading,
    error,
    refresh: mutate,
  };
}

export function usePromptVersions(templateId: number) {
  const { data, error, isLoading, mutate } = useSWR<PromptVersion[]>(
    `/api/manage/prompt-registry/templates/${templateId}/versions`,
    errorHandlingFetcher
  );
  return {
    versions: data || [],
    isLoading,
    error,
    refresh: mutate,
  };
}

export function usePromptAssignments(templateId: number) {
  const { data, error, isLoading, mutate } = useSWR<PromptAssignment[]>(
    `/api/manage/prompt-registry/templates/${templateId}/assignments`,
    errorHandlingFetcher
  );
  return {
    assignments: data || [],
    isLoading,
    error,
    refresh: mutate,
  };
}

export async function createPromptTemplate(name: string, description?: string) {
  const res = await fetch("/api/manage/prompt-registry/templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error("Failed to create prompt template");
  return res.json();
}

export async function createPromptVersion(templateId: number, content: string) {
  const res = await fetch(`/api/manage/prompt-registry/templates/${templateId}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error("Failed to create prompt version");
  return res.json();
}

export async function setPromptTrafficAllocations(templateId: number, allocations: { version_id: number; traffic_percentage: number }[]) {
  const res = await fetch(`/api/manage/prompt-registry/templates/${templateId}/traffic`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ allocations }),
  });
  if (!res.ok) throw new Error("Failed to set traffic allocations");
  return res.json();
}

export async function createPromptAssignment(templateId: number, targetType: string, targetId: string) {
  const res = await fetch(`/api/manage/prompt-registry/templates/${templateId}/assignments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_type: targetType, target_id: targetId }),
  });
  if (!res.ok) throw new Error("Failed to create prompt assignment");
  return res.json();
}

export async function deletePromptTemplate(templateId: number) {
  const res = await fetch(`/api/manage/prompt-registry/templates/${templateId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete prompt template");
  return res.json();
}
