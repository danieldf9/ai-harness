import PromptRegistryDetailPage from "@/refresh-pages/admin/PromptRegistryDetailPage";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  const id = parseInt(resolvedParams.id, 10);
  if (isNaN(id)) {
    return <div>Invalid ID</div>;
  }
  return <PromptRegistryDetailPage templateId={id} />;
}
