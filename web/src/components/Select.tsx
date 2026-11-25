import {
  Select as ShadSelect,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useId } from "react";
import { groupOptions } from "./groupOptions";

// `group` is optional: options with the same group share one heading in the list.
export type Option = { id: string; label: string; group?: string };

type Props = {
  label: string;
  options: Option[];
  value: string | null;
  onChange: (id: string) => void;
  disabled?: boolean;
};

export function Select({ label, options, value, onChange, disabled }: Props) {
  const id = useId();
  const sections = groupOptions(options);
  const groups = [];
  for (let s = 0; s < sections.length; s += 1) {
    const section = sections[s];
    const items = [];
    for (const o of section.items) {
      items.push(
        <SelectItem key={o.id} value={o.id}>
          {o.label}
        </SelectItem>,
      );
    }
    if (s > 0) groups.push(<SelectSeparator key={`sep-${s}`} />);
    groups.push(
      <SelectGroup key={section.title ?? "all"}>
        {section.title !== null && <SelectLabel>{section.title}</SelectLabel>}
        {items}
      </SelectGroup>,
    );
  }
  let current: string | undefined;
  if (value !== null) current = value;
  return (
    <div className="field">
      <Label htmlFor={id}>{label}</Label>
      <ShadSelect value={current} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger id={id}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>{groups}</SelectContent>
      </ShadSelect>
    </div>
  );
}
