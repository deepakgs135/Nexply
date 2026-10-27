import { useEffect, useRef, useState } from "react";
import type { Profile } from "../shared/resumeFormat";
import type { ResumePhase } from "./profileWorkspaceTypes";

const ACCEPTED = ["pdf", "docx", "txt"];
type Props = {
  maxSizeMb: number; setDocumentId: (value: string) => void; setFilename: (value: string) => void;
  setProfile: (value: Profile | null) => void; setSourceProfile: (value: Profile | null) => void;
  setPhase: (value: ResumePhase) => void; setPhaseLabel: (value: string) => void;
  setError: (value: string) => void; setSaveError: (value: string) => void; loadLatest: () => Promise<void>;
};

export function useResumeFile(props: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState("");
  const [textPreview, setTextPreview] = useState("");
  const [requestId, setRequestId] = useState("");
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    if (!file) { setFileUrl(""); setTextPreview(""); return; }
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (extension === "pdf") {
      const url = URL.createObjectURL(file); setFileUrl(url); setTextPreview("");
      return () => URL.revokeObjectURL(url);
    }
    setFileUrl("");
    if (extension === "txt") void file.text().then(setTextPreview).catch(() => setTextPreview(""));
    else setTextPreview("");
  }, [file]);

  function chooseFile(next?: File) {
    if (!next) return;
    const extension = next.name.split(".").pop()?.toLowerCase() || "";
    if (!ACCEPTED.includes(extension)) { props.setError("Choose a PDF, DOCX, or TXT resume."); return; }
    if (next.size > props.maxSizeMb * 1048576) { props.setError(`This file exceeds the ${props.maxSizeMb} MB upload limit.`); return; }
    if (!next.size) { props.setError("This file is empty. Choose a resume with content."); return; }
    setFile(next); setRequestId(crypto.randomUUID()); props.setDocumentId(""); props.setFilename(next.name);
    props.setProfile(null); props.setSourceProfile(null); props.setPhase("idle"); props.setPhaseLabel("");
    props.setError(""); props.setSaveError("");
  }

  async function reset() {
    setFile(null); setRequestId(""); props.setError(""); props.setPhase("idle"); props.setPhaseLabel("");
    if (inputRef.current) inputRef.current.value = "";
    await props.loadLatest();
  }
  function clear() { setFile(null); setRequestId(""); }
  return { inputRef, file, setFile, fileUrl, textPreview, requestId, setRequestId, dragging, setDragging, chooseFile, reset, clear };
}
