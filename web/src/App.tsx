import { Arena } from "./Arena";
import { AppShell } from "./components";
import { apiService } from "./ApiService";

export function App() {
  return (
    <AppShell>
      <Arena api={apiService} />
    </AppShell>
  );
}
