"use client";

import { useState, useEffect } from "react";
import { SettingsLayouts, Content } from "@opal/layouts";
import { SvgClipboard, SvgPlus, SvgSimpleLoader } from "@opal/icons";
import { Button, Table, createTableColumns, InputTypeIn } from "@opal/components";
import Text from "@/refresh-components/texts/Text";
import { Section } from "@/layouts/general-layouts";
import { usePromptTemplates, PromptTemplate, createPromptTemplate } from "@/lib/prompt-registry";
import { toast } from "@/hooks/useToast";
import Link from "next/link";
import { useRouter } from "next/navigation";

const tc = createTableColumns<PromptTemplate>();

const columns = [
  tc.column("name", {
    header: "Template Name",
    weight: 40,
    cell: (value, row) => (
      <Link href={`/admin/prompt-registry/${row.id}`} className="hover:underline font-medium text-text-900">
        <Text as="span" mainUiBody text05>
          {value}
        </Text>
      </Link>
    ),
  }),
  tc.column("description", {
    header: "Description",
    weight: 60,
    cell: (value) => (
      <Text as="span" mainUiBody text05>
        {value || "No description"}
      </Text>
    ),
  }),
];

function PromptRegistryTable() {
  const { templates, isLoading, refresh } = usePromptTemplates();
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const router = useRouter();

  useEffect(() => {
    const handleOpen = () => setIsCreating(true);
    window.addEventListener("open-create-template", handleOpen);
    return () => window.removeEventListener("open-create-template", handleOpen);
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <SvgSimpleLoader className="h-6 w-6" />
      </div>
    );
  }

  const filteredTemplates = templates.filter((t) =>
    t.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const template = await createPromptTemplate(newName, newDesc);
      toast.success("Prompt Template created successfully");
      setIsCreating(false);
      setNewName("");
      setNewDesc("");
      router.push(`/admin/prompt-registry/${template.id}`);
    } catch (e) {
      toast.error("Failed to create template");
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {isCreating ? (
        <Section title="Create New Template">
          <InputTypeIn
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Template Name (e.g. support_agent_prompt)"
          />
          <InputTypeIn
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            placeholder="Description..."
          />
          <div className="flex gap-2 mt-2">
            <Button onClick={handleCreate}>Create</Button>
            <Button prominence="secondary" onClick={() => setIsCreating(false)}>Cancel</Button>
          </div>
        </Section>
      ) : (
        <Section gap={0.5}>
          <InputTypeIn
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search templates..."
            searchIcon
          />
        </Section>
      )}
      
      <Table
        data={filteredTemplates}
        columns={columns}
        getRowId={(row) => String(row.id)}
        pageSize={10}
      />
    </div>
  );
}

export default function PromptRegistryPage() {
  return (
    <SettingsLayouts.Root>
      <SettingsLayouts.Header
        title="Prompt Registry"
        description="Manage, version, and assign system prompts to your agents and workflows."
        icon={SvgClipboard}
        rightChildren={
          <Button onClick={() => window.dispatchEvent(new CustomEvent('open-create-template'))} icon={SvgPlus}>
            New Template
          </Button>
        }
      />
      <SettingsLayouts.Body>
        <PromptRegistryTable />
      </SettingsLayouts.Body>
    </SettingsLayouts.Root>
  );
}
