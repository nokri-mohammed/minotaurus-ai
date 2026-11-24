/** The text of the one run button: play while idle, stop while a run goes. */
export function runButtonText(running: boolean): string {
  return running ? "■ Stop" : "▶ Start run";
}
