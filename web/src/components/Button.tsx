import type { ReactNode } from "react";
import { Button as AriaButton } from "react-aria-components";

type Props = {
  variant?: "primary" | "secondary";
  onPress?: () => void;
  isDisabled?: boolean;
  children: ReactNode;
};

/** The one primary action is near-black; everything else is the grey secondary. */
export function Button({ variant = "secondary", ...rest }: Props) {
  return <AriaButton className={`btn btn-${variant}`} {...rest} />;
}
