import { afterEach, expect, test } from "bun:test";
import { uploadBrain } from "./brain";

const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });

test("uploadBrain posts the file in the field 'file' to /api/brain", async () => {
  let seen: { url: string; init?: RequestInit } | undefined;
  globalThis.fetch = (async (url: string, init?: RequestInit) => {
    seen = { url, init };
    return new Response(JSON.stringify({ name: "q1", method: "qtable" }));
  }) as unknown as typeof fetch;
  expect(await uploadBrain(new File(["x"], "q1.onnx"))).toEqual({ name: "q1", method: "qtable" });
  expect(seen?.url).toBe("/api/brain");
  expect(seen?.init?.method).toBe("POST");
  expect((seen?.init?.body as FormData).get("file")).toBeInstanceOf(File);
});

test("uploadBrain surfaces the server's refusal", async () => {
  globalThis.fetch = (async () => new Response(JSON.stringify({ message: "Operator not allowed" }), { status: 400 })) as unknown as typeof fetch;
  await expect(uploadBrain(new File(["x"], "q1.onnx"))).rejects.toThrow("Operator not allowed");
});
