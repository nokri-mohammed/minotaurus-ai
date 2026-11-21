import { Label, ListBox, ListBoxItem, Popover, Select as AriaSelect, SelectValue } from "react-aria-components";
import { Button } from "./Button";

export type Option = { id: string; label: string };

type Props = {
  label: string;
  options: Option[];
  value: string | null;
  onChange: (id: string) => void;
  isDisabled?: boolean;
};

export function Select({ label, options, value, onChange, isDisabled }: Props) {
  return (
    <AriaSelect
      className="field"
      selectedKey={value}
      onSelectionChange={(key) => onChange(String(key))}
      isDisabled={isDisabled}
    >
      <Label>{label}</Label>
      <Button>
        <SelectValue />
        <span aria-hidden="true" className="chevron">▾</span>
      </Button>
      <Popover className="menu">
        <ListBox items={options}>
          {(o) => <ListBoxItem id={o.id} textValue={o.label}>{o.label}</ListBoxItem>}
        </ListBox>
      </Popover>
    </AriaSelect>
  );
}
