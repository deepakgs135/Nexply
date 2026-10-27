import { useEffect, useState } from "react";
import { ArrowDownToLine, Sparkles, X } from "lucide-react";
import { api, downloadBlob } from "../shared/api";
import { valueText, type Profile } from "../shared/resumeFormat";
import { ResumePreview } from "./ResumeEditor";

type AIResult = { model: string; structured_result: Profile };

export default function RexResumeBuilder({ profile, documentId }: { profile: Profile; documentId: string }) {
  const hasProfileData = Object.keys(profile).some((key) => profile[key] !== null && profile[key] !== undefined && profile[key] !== "");
  const [open, setOpen] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [model, setModel] = useState("");
  const [modelsLoading, setModelsLoading] = useState(false);
  const [jobDescription, setJobDescription] = useState("");
  const [generating, setGenerating] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AIResult | null>(null);

  useEffect(() => {
    if (!open || models.length) return;
    setModelsLoading(true);
    api<{ models: string[]; default_model: string }>("/resumes/ai/models")
      .then((response) => { setModels(response.models); setModel(response.default_model); })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load local Ollama models."))
      .finally(() => setModelsLoading(false));
  }, [open, models.length]);

  async function generate() {
    if (!documentId || generating) return;
    setGenerating(true); setError(""); setResult(null);
    try {
      const response = await api<AIResult>(`/resumes/${encodeURIComponent(documentId)}/ai-resume`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model, target_job_description: jobDescription.trim() || null }),
      });
      setResult(response);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "REX could not generate a resume."); }
    finally { setGenerating(false); }
  }

  async function exportDraft() {
    if (!documentId || !result) return;
    setExporting(true); setError("");
    try {
      const blob = await downloadBlob(`/resumes/${encodeURIComponent(documentId)}/ai-resume/export`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ structured_result: result.structured_result }),
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${valueText(result.structured_result.full_name).replace(/[^A-Za-z0-9_-]+/g, "-") || "candidate"}-resume.docx`;
      document.body.appendChild(anchor); anchor.click(); anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not export the REX draft."); }
    finally { setExporting(false); }
  }

  return <>
    <button className="resume-editor-button secondary rex-smart-profile-button" type="button" disabled={!documentId || !hasProfileData} onClick={() => { setError(""); setResult(null); setOpen(true); }} title={documentId ? "Generate a polished resume with REX" : "Save your profile before generating a REX resume"}><Sparkles size={14} /> REX Smart</button>
    {open && <div className="ai-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !generating && !exporting) setOpen(false); }}><section className="ai-modal" role="dialog" aria-modal="true" aria-labelledby="profile-rex-title">
      <header className="ai-modal-header"><div><span className="ai-modal-icon"><Sparkles size={18} /></span><div><span className="section-eyebrow">REX AGENT</span><h2 id="profile-rex-title">Build a resume with REX</h2><p>REX uses your saved profile. The generated draft won’t replace it.</p></div></div><button type="button" className="ai-modal-close" aria-label="Close REX" onClick={() => setOpen(false)} disabled={generating || exporting}><X size={18} /></button></header>
      <div className="ai-modal-body"><label className="ai-form-field"><span>Writing model</span><select value={model} disabled={modelsLoading || generating || !models.length} onChange={(event) => setModel(event.target.value)}>{models.length ? models.map((item) => <option key={item} value={item}>{item}{item === "llama3.1:8b" ? " · Recommended" : ""}</option>) : <option value="">{modelsLoading ? "Loading local models…" : "No models available"}</option>}</select><small>Runs locally with your installed Ollama models. Save field edits before asking REX to write.</small></label>
        <label className="ai-form-field"><span>Target job description <em>Optional</em></span><textarea rows={5} maxLength={12000} value={jobDescription} disabled={generating} onChange={(event) => setJobDescription(event.target.value)} placeholder="Paste a job description to tailor emphasis and wording. Leave blank for a general resume." /><small>{jobDescription.length.toLocaleString()} / 12,000 characters</small></label>
        {error && <div className="ai-error" role="alert">{error}</div>}
        {generating && <div className="ai-progress"><span className="ai-spinner"><Sparkles size={15} /></span><span><strong>REX is preparing your resume</strong><small>Reviewing your saved profile with Ollama…</small></span></div>}
        {result && <section className="ai-result-card"><div className="ai-result-heading"><div><span className="history-status complete">Draft ready</span><small>Generated with {result.model}</small></div><strong>{valueText(result.structured_result.full_name) || "Candidate resume"}</strong><p>{valueText(result.structured_result.professional_title)}</p></div><div className="ai-generated-preview"><ResumePreview profile={result.structured_result} /></div></section>}
      </div>
      <footer className="ai-modal-footer"><button className="ai-secondary-button" type="button" onClick={() => setOpen(false)} disabled={generating || exporting}>Close</button>{result && <button className="ai-secondary-button" type="button" onClick={() => void exportDraft()} disabled={exporting}>{exporting ? "Preparing…" : <><ArrowDownToLine size={15} /> Export DOCX</>}</button>}<button className="ai-primary-button" type="button" onClick={() => void generate()} disabled={!model || modelsLoading || generating || exporting}>{generating ? "Generating…" : result ? "Regenerate draft" : <><Sparkles size={15} /> Generate with REX</>}</button></footer>
    </section></div>}
  </>;
}
