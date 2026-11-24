export type GroupedOption = { id: string; label: string; group?: string };
export type Section<T extends GroupedOption> = { title: string | null; items: T[] };

// Split a flat list into sections by `group`, keeping the order the groups first appear in.
// Options with no group share one section with no title.
export function groupOptions<T extends GroupedOption>(options: T[]): Section<T>[] {
  const sections: Section<T>[] = [];
  for (const option of options) {
    const title = option.group ?? null;
    let section = sections.find((s) => s.title === title);
    if (!section) {
      section = { title, items: [] };
      sections.push(section);
    }
    section.items.push(option);
  }
  return sections;
}
