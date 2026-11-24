import { Header, Label, ListBox, ListBoxItem, ListBoxSection, Popover, Select as AriaSelect, SelectValue } from "react-aria-components";
import { Button } from "./Button";
import { groupOptions } from "./groupOptions";

// `group` is optional: options with the same group share one heading in the list.
export type Option = { id: string; label: string; group?: string };

type Props = {
  label: string;
  options: Option[];
  value: string | null;
  onChange: (id: string) => void;
  isDisabled?: boolean;
};

export function Select({ label, options, value, onChange, isDisabled }: Props) {
  const sections = groupOptions(options);
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
        <ListBox>
          {sections.map((section) => (
            <ListBoxSection key={section.title ?? "all"}>
              {section.title !== null && <Header className="menu-heading">{section.title}</Header>}
              {section.items.map((o) => (
                <ListBoxItem key={o.id} id={o.id} textValue={o.label}>{o.label}</ListBoxItem>
              ))}
            </ListBoxSection>
          ))}
        </ListBox>
      </Popover>
    </AriaSelect>
  );
}
