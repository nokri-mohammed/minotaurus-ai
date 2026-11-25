import type { ComponentProps } from "react";

import { Button as ShadButton } from "@/components/ui/button";

type Props = Omit<ComponentProps<typeof ShadButton>, "variant"> & { variant?: "primary" | "secondary" };

/** The one primary action is the dark default button; everything else is the grey secondary. */
export function Button({ variant = "secondary", ...rest }: Props) {
  let shad: "default" | "secondary" = "secondary";
  if (variant === "primary") shad = "default";
  return <ShadButton variant={shad} {...rest} />;
}
