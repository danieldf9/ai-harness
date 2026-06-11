"use client";

import AdminSidebar from "@/sections/sidebar/AdminSidebar";
import { usePathname } from "next/navigation";
import { useSettingsContext } from "@/providers/SettingsProvider";
import { ApplicationStatus } from "@/interfaces/settings";
import { Button, Text } from "@opal/components";
import { markdown } from "@opal/utils";
import useScreenSize from "@/hooks/useScreenSize";
import { SvgSidebar, SvgSimpleLoader } from "@opal/icons";
import { useSidebarState } from "@/layouts/sidebar-layouts";
import { Section } from "@/layouts/general-layouts";
import { isVectorDbRequiredRoute } from "@/lib/admin-routes";
import LiteModeIndexingNotice from "@/sections/admin/LiteModeIndexingNotice";

export interface ClientLayoutProps {
  children: React.ReactNode;
}

export default function ClientLayout({ children }: ClientLayoutProps) {
  const { setFolded } = useSidebarState();
  const { isMobile } = useScreenSize();
  const pathname = usePathname();
  const settings = useSettingsContext();

  // Certain admin panels have their own custom sidebar.
  // For those pages, we skip rendering the default `AdminSidebar` and let those individual pages render their own.
  const hasCustomSidebar = pathname.startsWith("/admin/connectors");

  // Lite mode (no vector DB): connector/indexing pages can't run, show a notice.
  const vectorDbEnabled = settings.settings.vector_db_enabled !== false;
  let content = children;
  if (isVectorDbRequiredRoute(pathname)) {
    if (settings.settingsLoading) {
      content = (
        <Section padding={2}>
          <SvgSimpleLoader className="h-6 w-6" />
        </Section>
      );
    } else if (!vectorDbEnabled) {
      content = <LiteModeIndexingNotice />;
    }
  }

  return (
    <div className="h-screen w-screen flex overflow-hidden">

      {hasCustomSidebar ? (
        <div className="flex-1 min-w-0 min-h-0 overflow-y-auto">{content}</div>
      ) : (
        <>
          <AdminSidebar />
          <div
            data-main-container
            className="flex flex-1 flex-col min-w-0 min-h-0 overflow-y-auto"
          >
            {isMobile && (
              <div className="flex items-center px-4 pt-2">
                <Button
                  prominence="internal"
                  icon={SvgSidebar}
                  onClick={() => setFolded(false)}
                />
              </div>
            )}
            {content}
          </div>
        </>
      )}
    </div>
  );
}
