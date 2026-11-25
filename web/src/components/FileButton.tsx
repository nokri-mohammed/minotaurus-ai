import { useRef, type ReactNode } from "react";

import { Button } from "./Button";

type Props = { accept: string[]; onFiles: (files: FileList | null) => void; children: ReactNode };

/** A button that opens the file picker; the hidden input does the choosing. */
export function FileButton({ accept, onFiles, children }: Props) {
  const input = useRef<HTMLInputElement>(null);
  return (
    <>
      <input
        ref={input}
        type="file"
        hidden
        accept={accept.join(",")}
        onChange={(event) => {
          onFiles(event.target.files);
          event.target.value = ""; // so the same file can be chosen again
        }}
      />
      <Button onClick={() => input.current?.click()}>{children}</Button>
    </>
  );
}
