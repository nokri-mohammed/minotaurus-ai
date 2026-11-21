// Skeleton: prove the page can reach the game server.
export {};
const statusLine = document.querySelector<HTMLParagraphElement>("#statusLine");

async function greet(): Promise<void> {
  if (!statusLine) return;
  try {
    const response = await fetch("/api/hello");
    const data: { message: string } = await response.json();
    statusLine.textContent = `Hello world. ${data.message}.`;
  } catch {
    statusLine.textContent = "Hello world. The server is not running (start it with: uv run minotaurus serve).";
  }
}

void greet();
