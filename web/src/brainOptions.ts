// How a brain is named in a dropdown: its name and the first 8 characters of its id.
import type { BrainInfo } from "./protocol";
import type { Option } from "./components";

export const SHORT_ID_LENGTH = 8;

export function shortId(id: string): string {
  return id.slice(0, SHORT_ID_LENGTH);
}

export function brainLabel(brain: Pick<BrainInfo, "id" | "name">): string {
  return `${brain.name} (${shortId(brain.id)})`;
}

export function brainOptions(brains: BrainInfo[]): Option[] {
  const options: Option[] = [];
  for (const brain of brains) options.push({ id: brain.id, label: brainLabel(brain) });
  return options;
}

/** A list with `brain` at the top; an older entry with the same id is replaced. */
export function withBrain(brains: BrainInfo[], brain: BrainInfo): BrainInfo[] {
  const list: BrainInfo[] = [brain];
  for (const other of brains) {
    if (other.id !== brain.id) list.push(other);
  }
  return list;
}
