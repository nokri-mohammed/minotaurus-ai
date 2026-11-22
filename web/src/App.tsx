import { Arena } from "./Arena";
import { AppShell } from "./components";
import { apiService } from "./services/ApiService";

export function App() {
  return (
    <AppShell>
      <Arena api={apiService} />
    </AppShell>
  );
}
