// POST /api/brain: upload one .onnx brain (multipart field "file").
import { type BrainInfo, brainInfoSchema } from "../../protocol";
import type { ApiService } from "../ApiService";

export async function uploadBrain(api: ApiService, file: File): Promise<BrainInfo> {
  const form = new FormData();
  form.append("file", file);
  return api.post("/api/brain", brainInfoSchema, form);
}
