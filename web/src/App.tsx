import { Arena } from "./Arena";
import { chooseApi } from "./net";

const { api, mock } = chooseApi();

export function App() {
  return (
    <main>
      <header>
        <img src="/icon.jpeg" alt="" width="48" height="48" />
        <h1>minotaurus-ai arena</h1>
      </header>
      {mock && <p className="banner">Mock mode: a scripted run, no server involved.</p>}
      <Arena api={api} />
    </main>
  );
}
