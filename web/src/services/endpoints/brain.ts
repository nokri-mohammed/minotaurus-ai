// POST /api/brain: upload one .onnx brain (multipart field "file").
import { type BrainInfo, brainInfoSchema } from "../../protocol";
import { apiService } from "../ApiService";

export async function uploadBrain(file: File): Promise<BrainInfo> {
  const form = new FormData();
  form.append("file", file);
  return apiService.post("/api/brain", brainInfoSchema, form);
}
