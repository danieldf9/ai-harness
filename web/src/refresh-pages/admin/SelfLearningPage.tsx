"use client";

import { useState } from "react";
import { SettingsLayouts } from "@opal/layouts";
import { SvgActivity, SvgCheck, SvgX, SvgSimpleLoader } from "@opal/icons";
import { Button, Table, createTableColumns, Tag } from "@opal/components";
import Text from "@/refresh-components/texts/Text";
import { toast } from "@/hooks/useToast";
import { 
  useHealingPolicies, 
  useLearningRecommendations, 
  useAutoOptimizationRules,
  approveRecommendation,
  rejectRecommendation,
  rollbackRecommendation,
  createHealingPolicy,
  createAutoOptimizationRule,
  deleteHealingPolicy,
  deleteAutoOptimizationRule,
  LearningRecommendation
} from "@/lib/self-learning";
import Modal from "@/refresh-components/Modal";

const recCols = createTableColumns<LearningRecommendation>();
const recommendationColumns = (handleApprove: (id: number) => void, handleReject: (id: number) => void, handleRollback: (id: number) => void) => [
  recCols.column("target_type", {
    header: "Target",
    weight: 15,
    cell: (value, row) => (
      <Text as="span" mainUiBody text05>
        {value} ({row.target_id || "global"})
      </Text>
    ),
  }),
  recCols.column("recommendation_type", {
    header: "Type",
    weight: 15,
    cell: (value) => (
      <Text as="span" mainUiBody text05>
        {value}
      </Text>
    ),
  }),
  recCols.column("evidence_json", {
    header: "Evidence",
    weight: 30,
    cell: (value) => (
      <Text as="span" mainUiBody text05>
        {value?.user_feedback || "No feedback text"}
      </Text>
    ),
  }),
  recCols.column("status", {
    header: "Status",
    weight: 10,
    cell: (value) => {
      let color: "gray" | "green" | "red" = "gray";
      if (value === "approved" || value === "applied") color = "green";
      if (value === "rejected" || value === "error") color = "red";
      return <Tag color={color} title={value} />;
    },
  }),
  recCols.column("id", {
    header: "Actions",
    weight: 30,
    cell: (id, row) => (
      <div className="flex gap-2">
        {row.status === "pending" && (
          <>
            <Button size="sm" onClick={() => handleApprove(id)} icon={SvgCheck}>Approve</Button>
            <Button size="sm" prominence="secondary" onClick={() => handleReject(id)} icon={SvgX}>Reject</Button>
          </>
        )}
        {row.status === "applied" && (
          <Button size="sm" prominence="secondary" onClick={() => handleRollback(id)}>Rollback</Button>
        )}
      </div>
    ),
  }),
];

export default function SelfLearningPage() {
  const { recommendations, isLoading: recLoading, refresh: refreshRecs } = useLearningRecommendations();
  const { policies, isLoading: polLoading, refresh: refreshPolicies } = useHealingPolicies();
  const { rules, isLoading: rulesLoading, refresh: refreshRules } = useAutoOptimizationRules();

  const [showAddPolicy, setShowAddPolicy] = useState(false);
  const [showAddRule, setShowAddRule] = useState(false);

  // Policy form state
  const [policyName, setPolicyName] = useState("");
  const [policyTargetType, setPolicyTargetType] = useState("global");
  const [policyRetries, setPolicyRetries] = useState(3);
  const [policyThreshold, setPolicyThreshold] = useState(0.7);

  // Rule form state
  const [ruleTargetType, setRuleTargetType] = useState("global");
  const [ruleMinConfidence, setRuleMinConfidence] = useState(0.8);
  const [ruleRequireApproval, setRuleRequireApproval] = useState(true);
  const [ruleIsDryRun, setRuleIsDryRun] = useState(true);

  const handleAddPolicy = async () => {
    try {
      await createHealingPolicy({ 
        name: policyName || "New Policy", 
        target_type: policyTargetType,
        max_retries: policyRetries,
        low_confidence_threshold: policyThreshold
      });
      toast.success("Healing policy created");
      setShowAddPolicy(false);
      setPolicyName(""); // reset
      refreshPolicies();
    } catch (e) {
      toast.error("Failed to create healing policy");
    }
  };

  const handleAddRule = async () => {
    try {
      await createAutoOptimizationRule({ 
        target_type: ruleTargetType,
        min_confidence_score: ruleMinConfidence,
        require_human_approval: ruleRequireApproval,
        is_dry_run: ruleIsDryRun
      });
      toast.success("Auto-optimization rule created");
      setShowAddRule(false);
      refreshRules();
    } catch (e) {
      toast.error("Failed to create auto-optimization rule");
    }
  };

  const handleDeletePolicy = async (id: number) => {
    try {
      await deleteHealingPolicy(id);
      toast.success("Healing policy deleted");
      refreshPolicies();
    } catch (e) {
      toast.error("Failed to delete policy");
    }
  };

  const handleDeleteRule = async (id: number) => {
    try {
      await deleteAutoOptimizationRule(id);
      toast.success("Auto-optimization rule deleted");
      refreshRules();
    } catch (e) {
      toast.error("Failed to delete rule");
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await approveRecommendation(id);
      toast.success("Recommendation approved");
      refreshRecs();
    } catch (e) {
      toast.error("Failed to approve recommendation");
    }
  };

  const handleReject = async (id: number) => {
    try {
      await rejectRecommendation(id);
      toast.success("Recommendation rejected");
      refreshRecs();
    } catch (e) {
      toast.error("Failed to reject recommendation");
    }
  };

  const handleRollback = async (id: number) => {
    try {
      await rollbackRecommendation(id);
      toast.success("Recommendation rolled back successfully");
      refreshRecs();
    } catch (e) {
      toast.error("Failed to rollback recommendation");
    }
  };

  if (recLoading || polLoading || rulesLoading) {
    return (
      <div className="flex justify-center py-12">
        <SvgSimpleLoader className="h-6 w-6" />
      </div>
    );
  }

  return (
    <SettingsLayouts.Root>
      <SettingsLayouts.Header
        title="Self-Learning & Healing"
        description="Govern the automatic recovery and self-improvement of your agents based on runtime errors and user feedback."
        icon={SvgActivity}
      />
      <SettingsLayouts.Body>
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-4 border border-border rounded-lg p-6 bg-background">
            <div>
              <h2 className="text-xl font-semibold text-text-900 mb-1">Learning Recommendations</h2>
              <p className="text-sm text-text-500">Suggested prompt and configuration updates based on recent user feedback and evaluations.</p>
            </div>
            <Table
              data={recommendations}
              columns={recommendationColumns(handleApprove, handleReject, handleRollback)}
              getRowId={(row) => String(row.id)}
              pageSize={10}
            />
          </div>

          <div className="flex flex-col gap-4 border border-border rounded-lg p-6 bg-background">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-text-900 mb-1">Active Healing Policies</h2>
                <p className="text-sm text-text-500">Policies dictating how the system recovers from errors like low confidence or tool failures.</p>
              </div>
              <Button onClick={() => setShowAddPolicy(true)}>Add Policy</Button>
            </div>
            <div className="flex flex-col gap-2">
              {policies.length === 0 ? (
                <Text mainUiBody text05>No active healing policies found.</Text>
              ) : (
                policies.map(p => (
                  <div key={p.id} className="p-4 border border-border-200 rounded-lg bg-background-50 flex justify-between items-center">
                    <div className="flex flex-wrap items-center gap-2">
                      <Text className="font-semibold">
                        {p.name}{" "}
                        <span className="text-text-500 font-normal ml-1">
                          | Target: {p.target_type} {p.target_id ? `(${p.target_id})` : "(Global)"} | Retries: {p.max_retries} | Status: {p.enabled ? "Enabled" : "Disabled"}
                        </span>
                      </Text>
                    </div>
                    <Button size="sm" prominence="secondary" onClick={() => handleDeletePolicy(p.id)} icon={SvgX}>Delete</Button>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="flex flex-col gap-4 border border-border rounded-lg p-6 bg-background">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-text-900 mb-1">Auto-Optimization Rules</h2>
                <p className="text-sm text-text-500">Rules governing when recommendations can be automatically applied.</p>
              </div>
              <Button onClick={() => setShowAddRule(true)}>Add Rule</Button>
            </div>
            <div className="flex flex-col gap-2">
              {rules.length === 0 ? (
                <Text mainUiBody text05>No auto-optimization rules found.</Text>
              ) : (
                rules.map(r => (
                  <div key={r.id} className="p-4 border border-border-200 rounded-lg bg-background-50 flex justify-between items-center">
                    <div className="flex flex-wrap items-center gap-2">
                      <Text className="font-semibold">
                        {r.target_type} {r.target_id ? `(${r.target_id})` : "(Global)"}{" "}
                        <span className="text-text-500 font-normal ml-1">
                          | Requires Human Approval: {r.require_human_approval ? "Yes" : "No"} | Dry Run: {r.is_dry_run ? "Yes" : "No"} | Min Confidence: {r.min_confidence_score}
                        </span>
                      </Text>
                    </div>
                    <Button size="sm" prominence="secondary" onClick={() => handleDeleteRule(r.id)} icon={SvgX}>Delete</Button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <Modal open={showAddPolicy} onOpenChange={setShowAddPolicy}>
          <Modal.Content width="sm">
            <Modal.Header title="Add Healing Policy" />
            <Modal.Body>
              <div className="flex flex-col gap-4 mt-2">
                <div>
                  <Text className="text-sm font-semibold mb-1">Policy Name</Text>
                  <input className="w-full border border-border rounded px-3 py-1.5" value={policyName} onChange={(e) => setPolicyName(e.target.value)} placeholder="E.g., Low Confidence Fallback" />
                </div>
                <div>
                  <Text className="text-sm font-semibold mb-1">Target Type</Text>
                  <select className="w-full border border-border rounded px-3 py-1.5" value={policyTargetType} onChange={(e) => setPolicyTargetType(e.target.value)}>
                    <option value="global">Global</option>
                    <option value="prompt">Prompt</option>
                    <option value="tool">Tool</option>
                  </select>
                </div>
                <div>
                  <Text className="text-sm font-semibold mb-1">Max Retries</Text>
                  <input type="number" className="w-full border border-border rounded px-3 py-1.5" value={policyRetries} onChange={(e) => setPolicyRetries(Number(e.target.value))} />
                </div>
                <div>
                  <Text className="text-sm font-semibold mb-1">Low Confidence Threshold</Text>
                  <input type="number" step="0.1" className="w-full border border-border rounded px-3 py-1.5" value={policyThreshold} onChange={(e) => setPolicyThreshold(Number(e.target.value))} />
                </div>
              </div>
              <div className="flex justify-end gap-2 mt-6">
                <Button prominence="secondary" onClick={() => setShowAddPolicy(false)}>Cancel</Button>
                <Button onClick={handleAddPolicy}>Create Policy</Button>
              </div>
            </Modal.Body>
          </Modal.Content>
        </Modal>

        <Modal open={showAddRule} onOpenChange={setShowAddRule}>
          <Modal.Content width="sm">
            <Modal.Header title="Add Auto-Optimization Rule" />
            <Modal.Body>
              <div className="flex flex-col gap-4 mt-2">
                <div>
                  <Text className="text-sm font-semibold mb-1">Target Type</Text>
                  <select className="w-full border border-border rounded px-3 py-1.5" value={ruleTargetType} onChange={(e) => setRuleTargetType(e.target.value)}>
                    <option value="global">Global</option>
                    <option value="prompt">Prompt</option>
                  </select>
                </div>
                <div>
                  <Text className="text-sm font-semibold mb-1">Min Confidence Score</Text>
                  <input type="number" step="0.1" className="w-full border border-border rounded px-3 py-1.5" value={ruleMinConfidence} onChange={(e) => setRuleMinConfidence(Number(e.target.value))} />
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="requireHuman" checked={ruleRequireApproval} onChange={(e) => setRuleRequireApproval(e.target.checked)} />
                  <label htmlFor="requireHuman"><Text className="text-sm">Require Human Approval</Text></label>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="isDryRun" checked={ruleIsDryRun} onChange={(e) => setRuleIsDryRun(e.target.checked)} />
                  <label htmlFor="isDryRun"><Text className="text-sm">Dry Run (Log Only)</Text></label>
                </div>
              </div>
              <div className="flex justify-end gap-2 mt-6">
                <Button prominence="secondary" onClick={() => setShowAddRule(false)}>Cancel</Button>
                <Button onClick={handleAddRule}>Create Rule</Button>
              </div>
            </Modal.Body>
          </Modal.Content>
        </Modal>
      </SettingsLayouts.Body>
    </SettingsLayouts.Root>
  );
}
