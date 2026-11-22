import { expect, test } from "bun:test";
import { ApiService } from "../ApiService";
import { uploadBrain } from "./brain";

test("uploadBrain posts the file in the field 'file' to /api/brain", async () => {
  let seen: { url: string; init?: RequestInit } | undefined;
  const fetchFn = (async (url: string, init?: RequestInit) => {
    seen = { url, init };
    return new Response(JSON.stringify({ name: "q1", method: "qtable" }));
  }) as unknown as typeof fetch;
  const brain = await uploadBrain(new ApiService({ fetchFn }), new File(["x"], "q1.onnx"));
  expect(brain).toEqual({ name: "q1", method: "qtable" });
  expect(seen?.url).toBe("/api/brain");
  expect(seen?.init?.method).toBe("POST");
  expect((seen?.init?.body as FormData).get("file")).toBeInstanceOf(File);
});

test("uploadBrain surfaces the server's refusal", async () => {
  const fetchFn = (async () => new Response(JSON.stringify({ message: "Operator not allowed" }), { status: 400 })) as unknown as typeof fetch;
  await expect(uploadBrain(new ApiService({ fetchFn }), new File(["x"], "q1.onnx"))).rejects.toThrow("Operator not allowed");
});
