import type { Profile } from "../shared/resumeFormat";
export type ResumePhase = "idle" | "upload" | "parse" | "extract" | "error";
export type LatestResume = {
  document_id: string; original_filename?: string; original_size_bytes?: number;
  created_at?: string; parsing_status?: string; llm_status?: string; structured_result?: Profile | null;
};
type LatestResponse = { resume: LatestResume | null };
export type { LatestResponse };
