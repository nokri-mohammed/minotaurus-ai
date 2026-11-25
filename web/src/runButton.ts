/** The run button's text on the LED panel. The LED font has no triangle or square sign, so
 *  > (a triangle) and # (a solid block) stand in. */
export function runLedLabel(running: boolean): string {
  if (running) return "# STOP";
  return "> START";
}
