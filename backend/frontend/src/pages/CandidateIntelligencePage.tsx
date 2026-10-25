import { useEffect, useRef, useState } from "react";
import { ArrowRight, ArrowUpFromLine, Check, CircleHelp, FileCheck2, FileText, LoaderCircle, ShieldCheck, Sparkles, Upload, X } from "lucide-react";
import { api } from "../shared/api";
import StructuredProfile from "../components/StructuredProfile";
import RexManualProfile from "../components/RexManualProfile";
import ResumeEditor from "../components/ResumeEditor";
import { formatSize, type Profile } from "../shared/resumeFormat";
type ResumeRecord = { document_id?: string; original_filename?: string; structured_result?: Profile };
type Phase = "idle" | "upload" | "parse" | "extract" | "done" | "error";

const ACCEPTED = ["pdf", "docx", "txt"];


export default function CandidateIntelligencePage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const analyzingRef = useRef(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadRequestId, setUploadRequestId] = useState("");
  const [fileUrl, setFileUrl] = useState("");
  const [textPreview, setTextPreview] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [phaseLabel, setPhaseLabel] = useState("");
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [maxSizeMb, setMaxSizeMb] = useState(15);
  const [apiOnline, setApiOnline] = useState(false);
  const [manualProfileOpen, setManualProfileOpen] = useState(false);
  const [manualBuilderOpen, setManualBuilderOpen] = useState(false);
  const [manualDraft, setManualDraft] = useState<Profile>({});
  const [manualSaving, setManualSaving] = useState(false);
  const [manualSaveError, setManualSaveError] = useState("");

  useEffect(() => {
    api<{ max_upload_size_mb: number }>("/api/config")
      .then((config) => { setMaxSizeMb(config.max_upload_size_mb); setApiOnline(true); })
      .catch(() => setApiOnline(false));
  }, []);

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

  const busy = ["upload", "parse", "extract"].includes(phase);

  function chooseFile(next?: File) {
    if (!next) return;
    const extension = next.name.split(".").pop()?.toLowerCase() || "";
    if (!ACCEPTED.includes(extension)) { setError("Choose a PDF, DOCX, or TXT resume."); return; }
    if (next.size > maxSizeMb * 1048576) { setError(`This file exceeds the ${maxSizeMb} MB upload limit.`); return; }
    if (!next.size) { setError("This file is empty. Choose a resume with content."); return; }
    setFile(next); setUploadRequestId(crypto.randomUUID()); setDocumentId(""); setProfile(null); setPhase("idle"); setPhaseLabel(""); setError("");
  }
  async function analyze() {
    if (analyzingRef.current || busy || (!file && !documentId)) return;
    analyzingRef.current = true;
    setError("");
    try {
      let activeId = documentId;
      if (!activeId && file) {
        setPhase("upload"); setPhaseLabel("Saving original document");
        const body = new FormData(); body.append("file", file);
        const uploaded = await api<{ document_id: string }>("/resumes/upload", {
          method: "POST",
          body,
          headers: { "Idempotency-Key": uploadRequestId },
        });
        activeId = uploaded.document_id; setDocumentId(activeId);
      }
      if (!activeId) throw new Error("Select a resume before starting extraction.");
      setPhase("parse"); setPhaseLabel("Reading the complete document");
      await api(`/resumes/${encodeURIComponent(activeId)}/parse`, { method: "POST" });
      setPhase("extract"); setPhaseLabel("Organizing all supported profile details");
      await api(`/resumes/${encodeURIComponent(activeId)}/extract`, { method: "POST" });
      const record = await api<ResumeRecord>(`/resumes/${encodeURIComponent(activeId)}`);
      setProfile(record.structured_result || {}); setPhase("done"); setPhaseLabel("Profile ready for review");
    } catch (caught) {
      setPhase("error"); setError(caught instanceof Error ? caught.message : "Resume extraction failed.");
    } finally {
      analyzingRef.current = false;
    }
  }
  function reset() {
    setFile(null); setUploadRequestId(""); setDocumentId(""); setProfile(null); setPhase("idle"); setPhaseLabel(""); setError("");
    if (inputRef.current) inputRef.current.value = "";
  }
  function updateManualDraft(path: (string | number)[], value: unknown) {
    setManualDraft((current) => {
      const copy = structuredClone(current) as Record<string, unknown>;
      let parent: any = copy;
      for (const part of path.slice(0, -1)) parent = parent[part];
      parent[path[path.length - 1]] = value;
      return copy;
    });
  }
  async function saveManualDraft() {
    if (manualSaving) return;
    setManualSaving(true); setManualSaveError("");
    try {
      const result = await api<{ document_id: string; structured_result: Profile }>("/resumes/manual-profile", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ structured_result: manualDraft }),
      });
      setDocumentId(result.document_id); setProfile(result.structured_result); setPhase("done"); setPhaseLabel("Manual resume saved");
      setManualBuilderOpen(false); setManualDraft({});
    } catch (caught) { setManualSaveError(caught instanceof Error ? caught.message : "Could not save this resume."); }
    finally { setManualSaving(false); }
  }
  const steps = [
    { id: "upload", label: "Upload", done: ["parse", "extract", "done"].includes(phase) },
    { id: "parse", label: "Read document", done: ["extract", "done"].includes(phase) },
    { id: "extract", label: "Structure profile", done: phase === "done" },
  ];

  return (
    <div className="page-wrap">
          <section className="page-intro"><div><div className="eyebrow"><span /> CANDIDATE WORKSPACE</div><h1>Candidate intelligence</h1><p>Review a resume alongside every structured detail extracted from it.</p></div><div className="candidate-intro-actions"><button className="rex-manual-start" type="button" onClick={() => { setManualDraft({}); setManualSaveError(""); setManualBuilderOpen(true); }} disabled={!apiOnline}><FileText size={15} /> Build manually</button><button className="candidate-rex-start" type="button" onClick={() => setManualProfileOpen(true)} disabled={!apiOnline}><Sparkles size={15} /> Create with REX</button><a href="/docs" className="docs-button" target="_blank" rel="noreferrer"><CircleHelp size={15} /> API docs <ArrowRight size={13} /></a></div></section>
          <section className="process-rail" aria-label="Resume analysis workflow">{steps.map((step, index) => <div className={`process-step ${phase === step.id ? "active" : ""} ${step.done ? "done" : ""}`} key={step.id}><span className="step-index">{step.done ? <Check size={14} /> : `0${index + 1}`}</span><span className="step-copy"><strong>{step.label}</strong><small>{index === 0 ? "Keep original on file" : index === 1 ? "Text across every page" : "Complete structured output"}</small></span>{index < 2 && <span className="step-connector" />}</div>)}</section>

          <section className="review-layout">
            <article className="source-card card">
              {!file ? <>
                <div className="source-heading"><div><div className="section-eyebrow">SOURCE DOCUMENT</div><h2>Resume input</h2><p>Upload a resume to create a candidate profile.</p></div><span className="heading-icon"><Upload size={18} /></span></div>
                <div className={`drop-area ${dragging ? "dragging" : ""}`} onClick={() => inputRef.current?.click()} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") inputRef.current?.click(); }} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files[0]); }} role="button" tabIndex={0} aria-label="Choose a resume file or drop one here">
                  <input ref={inputRef} type="file" accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain" hidden onChange={(event) => { chooseFile(event.target.files?.[0]); event.currentTarget.value = ""; }} />
                  <span className="drop-icon"><ArrowUpFromLine size={20} /></span><strong>Drop your resume here</strong><span className="drop-subline">or <button type="button" onClick={(event) => { event.stopPropagation(); inputRef.current?.click(); }}>browse files</button></span><span className="format-pills"><i>PDF</i><i>DOCX</i><i>TXT</i><span>Up to {maxSizeMb} MB</span></span>
                </div>
                <div className="upload-actions"><span className={`api-status ${apiOnline ? "online" : "offline"}`}><i />{apiOnline ? "API connected" : "API unavailable"}</span><button className="primary-button" type="button" disabled>Analyze resume <ArrowRight size={15} /></button></div>
                <div className="privacy-note"><ShieldCheck size={14} /> Original files stay with the resume record.</div>
              </> : <>
                <div className="source-filebar"><span className="file-symbol"><FileCheck2 size={17} /></span><span className="selected-meta"><strong title={file.name}>{file.name}</strong><small>{formatSize(file.size)} · {file.name.split(".").pop()?.toUpperCase()} · Original kept on file</small></span><button className="source-action" type="button" title="Replace resume" aria-label="Replace resume" onClick={() => inputRef.current?.click()}><Upload size={15} /></button><button className="source-action remove" type="button" title="Remove resume" aria-label="Remove resume" onClick={reset}><X size={16} /></button>
                  <input ref={inputRef} type="file" accept=".pdf,.docx,.txt" hidden onChange={(event) => { chooseFile(event.target.files?.[0]); event.currentTarget.value = ""; }} />
                </div>
                {fileUrl ? <div className="document-viewer"><div className="viewer-toolbar"><span><i /> Source document</span><span>PDF preview</span></div><iframe title="Resume PDF document" src={fileUrl} /></div> : <div className="nonpdf-viewer"><div className="nonpdf-heading"><FileText size={17} /><span>{file.name.toUpperCase().endsWith(".TXT") ? "TEXT DOCUMENT" : "DOCUMENT PREVIEW"}</span></div>{textPreview ? <pre>{textPreview}</pre> : <div className="nonpdf-message"><FileText size={27} /><strong>Document ready</strong><span>DOCX text will be extracted during analysis.</span></div>}</div>}
                <div className="viewer-footer"><ShieldCheck size={13} /> Select a profile detail to mark it for review.</div>
              </>}
              {file && <div className="analysis-controls"><div className={`api-status ${apiOnline ? "online" : "offline"}`}><i />{apiOnline ? "API connected" : "API unavailable"}</div><button className="primary-button" type="button" disabled={busy || !apiOnline} onClick={analyze}>{busy ? <><LoaderCircle className="spin" size={15} /> Working…</> : phase === "done" ? <>Analysis complete <Check size={14} /></> : phase === "error" && documentId ? <>Retry analysis <ArrowRight size={14} /></> : <>Analyze resume <ArrowRight size={14} /></>}</button></div>}
              {(busy || phase === "error") && <div className="progress-panel" aria-live="polite"><strong>{phaseLabel}</strong><div className="progress-steps">{steps.map((step) => <span className={step.done ? "finished" : phase === step.id ? "working" : ""} key={step.id}>{step.done ? <Check size={12} /> : phase === step.id ? <LoaderCircle size={12} className="spin" /> : <i />}{step.label}</span>)}</div>{error && <div className="error-message" role="alert">{error}{documentId && " Your upload is saved; retry to continue."}</div>}</div>}
            </article>

          <StructuredProfile profile={profile} filename={file?.name || (documentId ? "Manually created profile · REX" : undefined)} documentId={documentId || undefined} onProfileSaved={setProfile} />
          </section>
          {manualProfileOpen && <RexManualProfile onClose={() => setManualProfileOpen(false)} onSaved={(id, savedProfile) => { setDocumentId(id); setProfile(savedProfile); setPhase("done"); setPhaseLabel("Manual profile saved"); setManualProfileOpen(false); }} />}
          {manualBuilderOpen && <ResumeEditor mode="create" profile={manualDraft} documentId="" saving={manualSaving} error={manualSaveError} onChange={updateManualDraft} onSave={() => void saveManualDraft()} onCancel={() => { if (!manualSaving) setManualBuilderOpen(false); }} />}
          <footer className="app-footer"><span>© 2026 NEXPLY AI</span><span>Structured candidate information for thoughtful review.</span><span className={apiOnline ? "footer-online" : "footer-offline"}><i />{apiOnline ? "All systems operational" : "API unavailable"}</span></footer>
    </div>
  );
}
