"use client";

import { useState } from "react";
import { SettingsLayouts, Content } from "@opal/layouts";
import { SvgClipboard, SvgPlus, SvgSimpleLoader, SvgCheck, SvgX } from "@opal/icons";
import { Button, Table, createTableColumns, InputTypeIn } from "@opal/components";
import Text from "@/refresh-components/texts/Text";
import { Section } from "@/layouts/general-layouts";
import { 
  usePromptTemplates, 
  usePromptVersions, 
  usePromptAssignments,
  createPromptVersion,
  setPromptTrafficAllocations,
  createPromptAssignment,
  PromptVersion,
  PromptAssignment,
  deletePromptTemplate
} from "@/lib/prompt-registry";
import { toast } from "@/hooks/useToast";
import { useRouter } from "next/navigation";

const vtc = createTableColumns<PromptVersion>();
const atc = createTableColumns<PromptAssignment>();

export default function PromptRegistryDetailPage({ templateId }: { templateId: number }) {
  const { templates, isLoading: tLoading } = usePromptTemplates();
  const { versions, isLoading: vLoading, refresh: vRefresh } = usePromptVersions(templateId);
  const { assignments, isLoading: aLoading, refresh: aRefresh } = usePromptAssignments(templateId);
  
  const [isCreatingVersion, setIsCreatingVersion] = useState(false);
  const [newVersionContent, setNewVersionContent] = useState("");
  
  const [isCreatingAssignment, setIsCreatingAssignment] = useState(false);
  const [targetType, setTargetType] = useState("persona");
  const [targetId, setTargetId] = useState("");

  const [isManagingTraffic, setIsManagingTraffic] = useState(false);
  const [trafficAllocations, setTrafficAllocations] = useState<{ [id: number]: number | string }>({});

  const router = useRouter();
  
  const [isDeleting, setIsDeleting] = useState(false);

  const template = templates.find((t) => t.id === templateId);

  if (tLoading || vLoading || aLoading) {
    return (
      <SettingsLayouts.Root>
        <div className="flex justify-center py-12">
          <SvgSimpleLoader className="h-6 w-6" />
        </div>
      </SettingsLayouts.Root>
    );
  }

  if (!template) {
    return (
      <SettingsLayouts.Root>
        <div className="py-12 px-8">Template not found.</div>
      </SettingsLayouts.Root>
    );
  }

  const handleDeleteTemplate = async () => {
    if (!confirm("Are you sure you want to delete this prompt template? This action cannot be undone.")) {
      return;
    }
    
    setIsDeleting(true);
    try {
      await deletePromptTemplate(templateId);
      toast.success("Prompt template deleted successfully");
      router.push("/admin/prompt-registry");
    } catch (e) {
      toast.error("Failed to delete prompt template");
      setIsDeleting(false);
    }
  };

  const handleCreateVersion = async () => {
    if (!newVersionContent.trim()) return;
    try {
      await createPromptVersion(templateId, newVersionContent);
      toast.success("New version created successfully");
      setIsCreatingVersion(false);
      setNewVersionContent("");
      vRefresh();
    } catch (e) {
      toast.error("Failed to create version");
    }
  };

  const handleOpenTrafficManager = () => {
    const allocations: { [id: number]: number | string } = {};
    versions.forEach(v => {
      allocations[v.id] = v.traffic_percentage || 0;
    });
    setTrafficAllocations(allocations);
    setIsManagingTraffic(true);
  };

  const handleSaveTraffic = async () => {
    const total = Object.values(trafficAllocations).reduce<number>((acc, val) => acc + (Number(val) || 0), 0);
    if (total > 0 && Math.abs(total - 100) > 0.1) {
      toast.error("Total traffic must sum to exactly 100%");
      return;
    }
    try {
      const payload = Object.entries(trafficAllocations).map(([id, traffic]) => ({
        version_id: Number(id),
        traffic_percentage: Number(traffic) || 0,
      }));
      await setPromptTrafficAllocations(templateId, payload);
      toast.success("Traffic allocations updated");
      setIsManagingTraffic(false);
      vRefresh();
    } catch (e) {
      toast.error("Failed to update traffic allocations");
    }
  };

  const handleCreateAssignment = async () => {
    if (!targetId.trim()) return;
    try {
      await createPromptAssignment(templateId, targetType, targetId);
      toast.success("Assignment created successfully");
      setIsCreatingAssignment(false);
      setTargetId("");
      aRefresh();
    } catch (e) {
      toast.error("Failed to create assignment");
    }
  };

  const versionColumns = [
    vtc.column("version_number", {
      header: "Version",
      weight: 15,
      cell: (value) => (
        <Text as="span" mainUiBody text05>
          v{value}
        </Text>
      ),
    }),
    vtc.column("content", {
      header: "Content Snippet",
      weight: 50,
      cell: (value) => (
        <Text as="span" mainUiBody text05 className="truncate block max-w-sm">
          {value.slice(0, 80) + (value.length > 80 ? "..." : "")}
        </Text>
      ),
    }),
    vtc.column("is_active", {
      header: "Active",
      weight: 10,
      cell: (value) => (
        value ? <SvgCheck className="text-status-success-01 h-5 w-5" /> : <span className="text-text-400">—</span>
      ),
    }),
    vtc.column("traffic_percentage", {
      header: "Traffic %",
      weight: 10,
      cell: (value) => (
        <Text as="span" mainUiBody text05>
          {value > 0 ? `${value}%` : "—"}
        </Text>
      ),
    }),
  ];

  const assignmentColumns = [
    atc.column("target_type", {
      header: "Target Type",
      weight: 40,
      cell: (value) => <Text as="span" mainUiBody text05>{value}</Text>,
    }),
    atc.column("target_id", {
      header: "Target ID",
      weight: 60,
      cell: (value) => <Text as="span" mainUiBody text05>{value}</Text>,
    }),
  ];

  return (
    <SettingsLayouts.Root>
      <SettingsLayouts.Header
        title={template.name}
        description={template.description || "Manage versions and assignments for this template."}
        icon={SvgClipboard}
        rightChildren={
          <div className="flex gap-2">
            <Button onClick={handleDeleteTemplate} variant="danger" disabled={isDeleting}>
              {isDeleting ? "Deleting..." : "Delete Template"}
            </Button>
            <Button href="/admin/prompt-registry" prominence="secondary">
              Back to Registry
            </Button>
          </div>
        }
      />
      <SettingsLayouts.Body>
        <div className="flex flex-col gap-8">
          {/* Versions Section */}
          <Section title="Versions">
            <div className="mb-4 flex gap-4">
              <Button onClick={() => setIsCreatingVersion(!isCreatingVersion)} icon={isCreatingVersion ? SvgX : SvgPlus}>
                {isCreatingVersion ? "Cancel" : "New Version"}
              </Button>
              <Button onClick={isManagingTraffic ? () => setIsManagingTraffic(false) : handleOpenTrafficManager} icon={isManagingTraffic ? SvgX : undefined} prominence="secondary">
                {isManagingTraffic ? "Cancel Traffic Allocation" : "Manage Traffic Allocation"}
              </Button>
            </div>
            
            {isCreatingVersion && (
              <div className="mb-4 p-4 border rounded bg-background-50">
                <h3 className="text-lg font-medium">Create New Version</h3>
                <div className="mt-2">
                  <textarea
                    className="w-full p-2 border rounded resize-y min-h-[150px]"
                    value={newVersionContent}
                    onChange={(e) => setNewVersionContent(e.target.value)}
                    placeholder="Enter the prompt content here..."
                  />
                  {!newVersionContent.trim() && (
                    <p className="text-sm text-status-error-05 mt-1">Prompt content is required</p>
                  )}
                </div>
                <div className="flex gap-2 mt-2">
                  <Button onClick={handleCreateVersion} disabled={!newVersionContent.trim()}>
                    Save Version
                  </Button>
                </div>
              </div>
            )}

            {isManagingTraffic && (
              <div className="mb-4 p-4 border rounded bg-background-50">
                <h3 className="text-lg font-medium">A/B Testing - Traffic Allocation</h3>
                <p className="text-sm text-text-500 mb-4">Set percentage of traffic for each version. Total must be 100%.</p>
                <div className="flex flex-col gap-2">
                  {versions.map((v) => (
                    <div key={v.id} className="flex items-center gap-4">
                      <span className="w-24 font-medium">v{v.version_number}</span>
                      <div className="w-32">
                        <InputTypeIn
                          value={trafficAllocations[v.id] !== undefined ? String(trafficAllocations[v.id]) : ""}
                          onChange={(e) => setTrafficAllocations({ ...trafficAllocations, [v.id]: e.target.value })}
                          placeholder="%"
                        />
                      </div>
                      <span className="text-sm text-text-400">%</span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2 mt-4">
                  <Button onClick={handleSaveTraffic}>Save Allocations</Button>
                </div>
              </div>
            )}

            <Table
              data={versions}
              columns={versionColumns}
              getRowId={(row) => String(row.id)}
              pageSize={10}
            />
          </Section>

          {/* Assignments Section */}
          <Section title="Assignments">
            <div className="mb-4">
              <Button onClick={() => setIsCreatingAssignment(!isCreatingAssignment)} icon={isCreatingAssignment ? SvgX : SvgPlus}>
                {isCreatingAssignment ? "Cancel" : "New Assignment"}
              </Button>
            </div>
            
            {isCreatingAssignment && (
              <div className="mb-4 p-4 border rounded bg-background-50">
                <h3 className="text-lg font-medium">Assign to Target</h3>
                <div className="mt-2 flex gap-4">
                  <InputTypeIn
                    value={targetType}
                    onChange={(e) => setTargetType(e.target.value)}
                    placeholder="Target Type (e.g. persona)"
                  />
                  <InputTypeIn
                    value={targetId}
                    onChange={(e) => setTargetId(e.target.value)}
                    placeholder="Target ID (e.g. 1)"
                  />
                  <Button onClick={handleCreateAssignment}>Assign</Button>
                </div>
              </div>
            )}

            <Table
              data={assignments}
              columns={assignmentColumns}
              getRowId={(row) => String(row.id)}
              pageSize={10}
            />
          </Section>
        </div>
      </SettingsLayouts.Body>
    </SettingsLayouts.Root>
  );
}
