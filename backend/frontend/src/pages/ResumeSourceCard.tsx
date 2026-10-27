import type { RefObject } from "react";
import { ArrowRight, ArrowUpFromLine, FileCheck2, FileText, LoaderCircle, RefreshCw, ShieldCheck, Upload, X } from "lucide-react";
import { formatSize, type Profile } from "../shared/resumeFormat";
import type { ResumePhase } from "./profileWorkspaceTypes";

type Props = {
  file: File | null; documentId: string; filename: string; sourceProfile: Profile | null;
  fileUrl: string; textPreview: string; apiOnline: boolean; maxSizeMb: number; busy: boolean;
  phaseLabel: string; phase: ResumePhase; error: string; dragging: boolean;
  inputRef: RefObject<HTMLInputElement | null>; onDragging: (dragging: boolean) => void;
  onChooseFile: (file?: File) => void; onAnalyze: () => void; onReset: () => void;
};

export default function ResumeSourceCard({ file, documentId, filename, sourceProfile, fileUrl, textPreview, apiOnline, maxSizeMb, busy, phaseLabel, phase, error, dragging, inputRef, onDragging, onChooseFile, onAnalyze, onReset }: Props) {
  return <section className="profile-upload-card card">
    <div className="source-heading"><div><div className="section-eyebrow">RESUME SOURCE</div><h2>{file ? "Selected resume" : filename || "Upload your resume"}</h2><p>Only your latest resume and its structured profile are kept.</p></div><span className="heading-icon"><Upload size={18} /></span></div>
    {!file && !documentId && <div className={`drop-area profile-drop-area ${dragging ? "dragging" : ""}`} onClick={() => inputRef.current?.click()} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") inputRef.current?.click(); }} onDragOver={(event) => { event.preventDefault(); onDragging(true); }} onDragLeave={() => onDragging(false)} onDrop={(event) => { event.preventDefault(); onDragging(false); onChooseFile(event.dataTransfer.files[0]); }} role="button" tabIndex={0} aria-label="Choose a resume file or drop one here">
      <span className="drop-icon"><ArrowUpFromLine size={20} /></span><strong>Drop your resume here</strong><span className="drop-subline">or <button type="button" onClick={(event) => { event.stopPropagation(); inputRef.current?.click(); }}>browse files</button></span><span className="format-pills"><i>PDF</i><i>DOCX</i><i>TXT</i><span>Up to {maxSizeMb} MB</span></span>
    </div>}
    {(file || documentId) && <div className="profile-source-file"><span className="file-symbol"><FileCheck2 size={17} /></span><div><strong title={file?.name || filename}>{file?.name || filename}</strong><small>{file ? `${formatSize(file.size)} · ${file.name.split(".").pop()?.toUpperCase()} · Ready to analyze` : `Latest resume · ${sourceProfile ? "Profile available" : "Needs analysis"}`}</small></div><button className="source-action" type="button" onClick={() => inputRef.current?.click()} aria-label="Replace resume" title="Replace resume"><Upload size={15} /></button>{file && <button className="source-action remove" type="button" onClick={onReset} aria-label="Cancel selected resume"><X size={15} /></button>}</div>}
    <input ref={inputRef} type="file" accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain" hidden onChange={(event) => { onChooseFile(event.target.files?.[0]); event.currentTarget.value = ""; }} />
    {fileUrl && <div className="profile-source-preview"><iframe title="Selected resume preview" src={fileUrl} /></div>}
    {textPreview && <pre className="profile-text-preview">{textPreview}</pre>}
    {!file && documentId && filename && <div className="profile-existing-file"><FileText size={16} /><span>Your original file is stored securely with this profile.</span></div>}
    {(file || documentId) && !sourceProfile && <div className="profile-source-actions"><button className="primary-button" type="button" disabled={busy || !apiOnline} onClick={onAnalyze}>{busy ? <><LoaderCircle className="spin" size={15} /> {phaseLabel || "Working…"}</> : phase === "error" ? <>Retry extraction <RefreshCw size={14} /></> : documentId ? <>Analyze latest resume <ArrowRight size={14} /></> : <>Upload and extract <ArrowRight size={14} /></>}</button></div>}
    {busy && <div className="profile-process-state"><span className="process-loader"><LoaderCircle className="spin" size={15} /></span><span><strong>{phaseLabel}</strong><small>Your document is processed page by page.</small></span></div>}
    {error && <div className="error-message" role="alert">{error}</div>}
    <div className="privacy-note"><ShieldCheck size={14} /> Your resume belongs to your account. Replacing it removes the previous original and profile.</div>
  </section>;
}
