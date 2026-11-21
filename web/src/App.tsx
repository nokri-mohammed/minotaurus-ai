import { useState } from "react";
import { Button } from "react-aria-components";

type Greeting = { message: string; engine: string };

// Hello world: proves the page (React + React Aria) can reach the local game server.
export function App() {
  const [text, setText] = useState("Press the button to ask the server.");

  async function ask(): Promise<void> {
    setText("Asking the server...");
    try {
      const response = await fetch("/api/hello");
      const data: Greeting = await response.json();
      setText(`${data.message} (${data.engine})`);
    } catch {
      setText("The server is not running. Start everything with: uv run minotaurus dev");
    }
  }

  return (
    <main>
      <img src="/icon.jpeg" alt="minotaurus-ai logo" width="128" height="128" />
      <h1>minotaurus-ai</h1>
      <p>Hello world.</p>
      <Button onPress={ask}>Ask the server</Button>
      <p role="status">{text}</p>
    </main>
  );
}
