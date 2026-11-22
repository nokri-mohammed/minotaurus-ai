import { Arena } from "./Arena";
import { AppShell } from "./components";
import { arenaApi } from "./services";

export function App() {
  return (
    <AppShell>
      <Arena api={arenaApi} />
    </AppShell>
  );
}
