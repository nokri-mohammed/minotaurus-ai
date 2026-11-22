import { useEffect, useState } from "react";
import { Arena } from "./Arena";
import { AppShell } from "./components";
import { type Api, chooseApi } from "./net";

export function App() {
  const [choice, setChoice] = useState<{ api: Api; mock: boolean } | null>(null);

  useEffect(() => {
    async function pick() {
      setChoice(await chooseApi());
    }
    void pick();
  }, []);

  if (!choice) return null;
  return (
    <AppShell mock={choice.mock}>
      <Arena api={choice.api} />
    </AppShell>
  );
}
