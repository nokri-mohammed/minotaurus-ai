import type { ReactNode } from "react";
import { FileTrigger } from "react-aria-components";
import { Button } from "./Button";

type Props = { accept: string[]; onFiles: (files: FileList | null) => void; children: ReactNode };

export function FileButton({ accept, onFiles, children }: Props) {
  return (
    <FileTrigger acceptedFileTypes={accept} onSelect={onFiles}>
      <Button>{children}</Button>
    </FileTrigger>
  );
}
