import type { ReactNode } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Props = { title: string; note?: ReactNode; actions?: ReactNode; className?: string; children: ReactNode };

/** A shadcn card: a title, an optional note, optional actions on the right, content below. */
export function Panel({ title, note, actions, className, children }: Props) {
  return (
    <Card className={cn(className)}>
      <CardHeader>
        <div className="flex flex-col gap-1.5">
          <CardTitle>{title}</CardTitle>
          {note && <CardDescription>{note}</CardDescription>}
        </div>
        {actions}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
