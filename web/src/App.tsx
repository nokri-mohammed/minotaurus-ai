import { Arena } from "./Arena";
import { AppShell } from "./components";
import { realApi } from "./net";

export function App() {
  return (
    <AppShell>
      <Arena api={realApi} />
    </AppShell>
  );
}
