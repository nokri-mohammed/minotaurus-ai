import { IconDeviceDesktop, IconMoon, IconSun } from "@tabler/icons-react";

import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { isThemeChoice, THEME_CHOICES, type ThemeChoice } from "../theme";

type Props = { value: ThemeChoice; onChange: (choice: ThemeChoice) => void };

/** The shadcn mode toggle: a sun/moon button that opens Dark, System and Light. */
export function ModeToggle({ value, onChange }: Props) {
  const items = [];
  for (const choice of THEME_CHOICES) {
    items.push(
      <DropdownMenuRadioItem key={choice.id} value={choice.id}>
        {choice.label}
      </DropdownMenuRadioItem>,
    );
  }
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" aria-label="Choose theme">
          {value === "system" && <IconDeviceDesktop />}
          {value === "light" && <IconSun />}
          {value === "dark" && <IconMoon />}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuRadioGroup
          value={value}
          onValueChange={(id) => {
            if (isThemeChoice(id)) onChange(id);
          }}
        >
          {items}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
