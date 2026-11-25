import { IconInfoCircle } from "@tabler/icons-react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { tipFor } from "../glossary";

type Props = { label: string; text?: string };

/** A small (i) button that explains a label in a tooltip. Without `text` it looks the label up. */
export function InfoTip({ label, text }: Props) {
  const shown = text ?? tipFor(label);
  if (shown === null) return null;
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          aria-label={`About ${label}`}
          className="inline-flex size-4 shrink-0 items-center justify-center rounded-full align-middle text-muted-foreground outline-none hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50"
        >
          <IconInfoCircle className="size-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-60">{shown}</TooltipContent>
    </Tooltip>
  );
}
