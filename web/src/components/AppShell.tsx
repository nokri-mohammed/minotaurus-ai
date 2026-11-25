import { IconBrain, IconPlayerPlay, type Icon } from "@tabler/icons-react";
import { useEffect, useState, type ReactNode } from "react";

import { Separator } from "@/components/ui/separator";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import type { Page } from "../page";
import { applyThemeChoice, loadThemeChoice, saveThemeChoice, watchSystemTheme } from "../services/theme";
import type { ThemeChoice } from "../theme";
import { ModeToggle } from "./ModeToggle";

type Props = { page: Page; children: ReactNode };

type NavItem = { page: Page; title: string; icon: Icon };

const NAV: NavItem[] = [
  { page: "arena", title: "Arena", icon: IconPlayerPlay },
  { page: "brains", title: "Brains", icon: IconBrain },
];

function titleOf(page: Page): string {
  for (const item of NAV) {
    if (item.page === page) return item.title;
  }
  return "Arena";
}

/** The shadcn dashboard shell: an inset sidebar, a header with the page title, then the page. */
export function AppShell({ page, children }: Props) {
  const [choice, setChoice] = useState<ThemeChoice>(loadThemeChoice);

  useEffect(() => {
    applyThemeChoice(choice);
    return watchSystemTheme(() => applyThemeChoice(choice));
  }, [choice]);

  function pick(next: ThemeChoice) {
    saveThemeChoice(next);
    setChoice(next);
  }

  const items = [];
  for (const item of NAV) {
    items.push(
      <SidebarMenuItem key={item.page}>
        <SidebarMenuButton asChild isActive={page === item.page} tooltip={item.title}>
          <a href={`#${item.page}`}>
            <item.icon />
            <span>{item.title}</span>
          </a>
        </SidebarMenuButton>
      </SidebarMenuItem>,
    );
  }

  return (
    <TooltipProvider>
      <SidebarProvider
        style={
          {
            "--sidebar-width": "calc(var(--spacing) * 64)",
            "--header-height": "calc(var(--spacing) * 12)",
          } as React.CSSProperties
        }
      >
        <Sidebar variant="inset" collapsible="offcanvas">
          <SidebarHeader>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild className="data-[slot=sidebar-menu-button]:p-1.5!">
                  <a href="#arena">
                    <img src="/icon.jpeg" alt="" width="20" height="20" className="rounded-sm" />
                    <span className="text-base font-semibold">minotaurus-ai</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>{items}</SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
          <SidebarFooter className="gap-3 px-3 pb-4">
            <p className="text-center text-xs text-muted-foreground">Local arena, 127.0.0.1</p>
          </SidebarFooter>
        </Sidebar>
        <SidebarInset>
          <header className="flex h-(--header-height) shrink-0 items-center gap-2 border-b">
            <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
              <SidebarTrigger className="-ml-1" />
              <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
              <h1 className="text-base font-medium">{titleOf(page)}</h1>
              <div className="ml-auto">
                <ModeToggle value={choice} onChange={pick} />
              </div>
            </div>
          </header>
          <div className="flex flex-1 flex-col gap-4 p-4 md:p-6">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  );
}
