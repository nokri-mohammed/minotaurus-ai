import { IconDownload } from "@tabler/icons-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { brainDownloadUrl } from "../services";

type Props = { brainId: string; className?: string };

/** A link that saves the brain's file (the .tar bundle, or the .onnx it came as). */
export function DownloadButton({ brainId, className }: Props) {
  return (
    <a
      href={brainDownloadUrl(brainId)}
      download
      className={cn(buttonVariants({ variant: "secondary" }), className)}
      onClick={(event) => event.stopPropagation()}
    >
      <IconDownload aria-hidden="true" />
      Download
    </a>
  );
}
