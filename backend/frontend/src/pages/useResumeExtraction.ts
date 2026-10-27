import { useRef, useState } from "react";
import { api } from "../shared/api";
import type { Profile } from "../shared/resumeFormat";
import type { LatestResume, ResumePhase } from "./profileWorkspaceTypes";

type Props = { file: File | null; requestId: string; documentId: string; filename: string;
  setDocumentId: (value: string) => void; setFilename: (value: string) => void;
  setSourceProfile: (value: Profile | null) => void; setProfile: (value: Profile | null) => void;
  setPhase: (value: ResumePhase) => void; setPhaseLabel: (value: string) => void; setError: (value: string) => void;
};

export function useResumeExtraction(props: Props) {
  const working = useRef(false);
  const [busy, setBusy] = useState(false);
  async function analyze() {
    if (working.current || busy || (!props.file && !props.documentId)) return;
    working.current = true; setBusy(true); props.setError("");
    try {
      let activeId = props.documentId;
      if (props.file && !activeId) {
        props.setPhase("upload"); props.setPhaseLabel("Saving the original resume");
        const body = new FormData(); body.append("file", props.file);
        const uploaded = await api<{ document_id: string }>("/resumes/upload", { method: "POST", body, headers: { "Idempotency-Key": props.requestId } });
        activeId = uploaded.document_id; props.setDocumentId(activeId);
      }
      if (!activeId) throw new Error("Choose a resume before starting extraction.");
      props.setPhase("parse"); props.setPhaseLabel("Reading all pages and sections");
      await api(`/resumes/${encodeURIComponent(activeId)}/parse`, { method: "POST" });
      props.setPhase("extract"); props.setPhaseLabel("Organizing the complete candidate profile");
      await api(`/resumes/${encodeURIComponent(activeId)}/extract`, { method: "POST" });
      const record = await api<LatestResume>(`/resumes/${encodeURIComponent(activeId)}`);
      const extracted = record.structured_result || {};
      props.setDocumentId(activeId); props.setFilename(record.original_filename || props.file?.name || props.filename);
      props.setSourceProfile(extracted); props.setProfile(extracted);
      props.setPhase("idle"); props.setPhaseLabel("Profile extracted. Review and edit the profile blocks.");
    } catch (caught) {
      props.setPhase("error"); props.setError(caught instanceof Error ? caught.message : "Resume extraction failed.");
    } finally { setBusy(false); working.current = false; }
  }
  return { busy, analyze };
}
