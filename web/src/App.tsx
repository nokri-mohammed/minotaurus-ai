import { Arena } from "./Arena";
import { AppShell } from "./components";
import { chooseApi } from "./net";

const { api, mock } = chooseApi();

export function App() {
  return (
    <AppShell mock={mock}>
      <Arena api={api} />
    </AppShell>
  );
}
