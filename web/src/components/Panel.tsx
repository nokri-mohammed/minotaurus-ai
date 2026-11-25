import type { ReactNode } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Props = { title: string; note?: ReactNode; actions?: ReactNode; className?: string; children: ReactNode };

/** A shadcn card: a title, an optional note, optional actions on the right, content below. */
export function Panel({ title, note, actions, className, children }: Props) {
  return (
    <Card className={cn(className)}>
      <CardHeader className="flex-nowrap items-center">
        <div className="flex min-w-0 flex-col gap-1.5">
          <CardTitle>{title}</CardTitle>
          {note && <CardDescription>{note}</CardDescription>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
