import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight, ArrowUpFromLine, BriefcaseBusiness, FileCheck2, FileText, LoaderCircle, RefreshCw, ShieldCheck, Upload, UserRound, X } from "lucide-react";
import ResumeEditor from "../components/ResumeEditor";
import RexResumeBuilder from "../components/RexResumeBuilder";
import { api } from "../shared/api";
import { formatSize, type Profile } from "../shared/resumeFormat";

type Preferences = {
  current_ctc: string; expected_ctc: string; expected_ctc_range: string; minimum_expected_ctc: string;
  currency: string; preferred_locations: string[]; preferred_job_titles: string[]; work_mode: string;
  employment_types: string[]; notice_period: string; availability: string;
  willing_to_relocate: boolean | null; preferred_industries: string[];
};
const EMPTY_PREFERENCES: Preferences = {
  current_ctc: "", expected_ctc: "", expected_ctc_range: "", minimum_expected_ctc: "", currency: "INR",
  preferred_locations: [], preferred_job_titles: [], work_mode: "", employment_types: [], notice_period: "",
  availability: "", willing_to_relocate: null, preferred_industries: [],
};
const joined = (value: unknown) => Array.isArray(value) ? value.filter((item): item is string => typeof item === "string").join(", ") : "";

type LatestResume = {
  document_id: string;
  original_filename?: string;
  original_size_bytes?: number;
  created_at?: string;
  parsing_status?: string;
  llm_status?: string;
  structured_result?: Profile | null;
};
type LatestResponse = { resume: LatestResume | null };
type Phase = "idle" | "upload" | "parse" | "extract" | "error";
const ACCEPTED = ["pdf", "docx", "txt"];

export default function ProfilePage() {
  const fileInput = useRef<HTMLInputElement>(null);
  const working = useRef(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [maxSizeMb, setMaxSizeMb] = useState(15);
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState("");
  const [textPreview, setTextPreview] = useState("");
  const [requestId, setRequestId] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [filename, setFilename] = useState("");
  const [sourceProfile, setSourceProfile] = useState<Profile | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [phaseLabel, setPhaseLabel] = useState("");
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [preferences, setPreferences] = useState<Preferences>(EMPTY_PREFERENCES);
  const [preferencesSaving, setPreferencesSaving] = useState(false);
  const [preferencesMessage, setPreferencesMessage] = useState("");
  const [preferencesTableReady, setPreferencesTableReady] = useState(false);

  const loadLatest = useCallback(async () => {
    try {
      const result = await api<LatestResponse>("/resumes/latest");
      const latest = result.resume;
      setDocumentId(latest?.document_id || "");
      setFilename(latest?.original_filename || "");
      setProfile(latest?.structured_result || null);
      setSourceProfile(latest?.structured_result || null);
      try {
        const storedResponse = await api<{ job_preferences: Partial<Preferences>; configured: boolean }>("/resumes/preferences");
        const stored = storedResponse.job_preferences || {};
        setPreferencesTableReady(storedResponse.configured);
        setPreferencesMessage(storedResponse.configured ? "" : "Run the preferences SQL file to enable saving.");
        const text = (value: unknown) => typeof value === "string" ? value : "";
        setPreferences({
          ...EMPTY_PREFERENCES,
          current_ctc: text(stored.current_ctc), expected_ctc: text(stored.expected_ctc),
          expected_ctc_range: text(stored.expected_ctc_range), minimum_expected_ctc: text(stored.minimum_expected_ctc),
          currency: text(stored.currency) || "INR", work_mode: text(stored.work_mode),
          notice_period: text(stored.notice_period), availability: text(stored.availability),
          willing_to_relocate: typeof stored.willing_to_relocate === "boolean" ? stored.willing_to_relocate : null,
          preferred_locations: Array.isArray(stored.preferred_locations) ? stored.preferred_locations : [],
          preferred_job_titles: Array.isArray(stored.preferred_job_titles) ? stored.preferred_job_titles : [],
          employment_types: Array.isArray(stored.employment_types) ? stored.employment_types : [],
          preferred_industries: Array.isArray(stored.preferred_industries) ? stored.preferred_industries : [],
        });
      } catch {
        setPreferencesTableReady(false);
        setPreferencesMessage("Could not load preferences from PostgreSQL.");
      }
      setPhase("idle");
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load your latest profile.");
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    api<{ max_upload_size_mb: number }>("/api/config")
      .then((config) => { setMaxSizeMb(config.max_upload_size_mb); setApiOnline(true); })
      .catch(() => setApiOnline(false));
    void loadLatest();
  }, [loadLatest]);

  useEffect(() => {
    if (!file) { setFileUrl(""); setTextPreview(""); return; }
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (extension === "pdf") {
      const url = URL.createObjectURL(file);
      setFileUrl(url);
      setTextPreview("");
      return () => URL.revokeObjectURL(url);
    }
    setFileUrl("");
    if (extension === "txt") void file.text().then(setTextPreview).catch(() => setTextPreview(""));
    else setTextPreview("");
  }, [file]);

  function chooseFile(next?: File) {
    if (!next) return;
    const extension = next.name.split(".").pop()?.toLowerCase() || "";
    if (!ACCEPTED.includes(extension)) { setError("Choose a PDF, DOCX, or TXT resume."); return; }
    if (next.size > maxSizeMb * 1048576) { setError(`This file exceeds the ${maxSizeMb} MB upload limit.`); return; }
    if (!next.size) { setError("This file is empty. Choose a resume with content."); return; }
    setFile(next);
    setRequestId(crypto.randomUUID());
    setDocumentId("");
    setFilename(next.name);
    setProfile(null);
    setSourceProfile(null);
    setPhase("idle");
    setPhaseLabel("");
    setError("");
    setSaveError("");
  }

  async function analyze() {
    if (working.current || busy || (!file && !documentId)) return;
    working.current = true;
    setBusy(true);
    setError("");
    try {
      let activeId = documentId;
      if (file && !activeId) {
        setPhase("upload"); setPhaseLabel("Saving the original resume");
        const body = new FormData(); body.append("file", file);
        const uploaded = await api<{ document_id: string }>("/resumes/upload", {
          method: "POST", body, headers: { "Idempotency-Key": requestId },
        });
        activeId = uploaded.document_id;
        setDocumentId(activeId);
      }
      if (!activeId) throw new Error("Choose a resume before starting extraction.");
      setPhase("parse"); setPhaseLabel("Reading all pages and sections");
      await api(`/resumes/${encodeURIComponent(activeId)}/parse`, { method: "POST" });
      setPhase("extract"); setPhaseLabel("Organizing the complete candidate profile");
      await api(`/resumes/${encodeURIComponent(activeId)}/extract`, { method: "POST" });
      const record = await api<LatestResume>(`/resumes/${encodeURIComponent(activeId)}`);
      const extracted = record.structured_result || {};
      setDocumentId(activeId);
      setFilename(record.original_filename || file?.name || filename);
      setSourceProfile(extracted);
      setProfile(extracted);
      setPhase("idle"); setPhaseLabel("Profile extracted. Review and edit the profile blocks.");
    } catch (caught) {
      setPhase("error");
      setError(caught instanceof Error ? caught.message : "Resume extraction failed.");
    } finally {
      setBusy(false);
      working.current = false;
    }
  }

  function startManual() {
    setFile(null); setRequestId(""); setDocumentId(""); setFilename("Manual profile");
    setSourceProfile(null); setProfile({}); setPhase("idle"); setPhaseLabel(""); setError(""); setSaveError("");
  }

  function updateProfile(path: (string | number)[], value: unknown) {
    setProfile((current) => {
      const updated = structuredClone(current || {}) as Record<string, unknown>;
      let parent: any = updated;
      for (let index = 0; index < path.length - 1; index += 1) {
        const part = path[index];
        if (parent[part] === undefined || parent[part] === null) parent[part] = typeof path[index + 1] === "number" ? [] : {};
        parent = parent[part];
      }
      parent[path[path.length - 1]] = value;
      return updated;
    });
  }

  async function saveProfile() {
    if (!profile || saving) return;
    setSaving(true); setSaveError("");
    try {
      if (documentId) {
        const result = await api<{ structured_result: Profile }>(`/resumes/${encodeURIComponent(documentId)}/structured-result`, {
          method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ structured_result: profile }),
        });
        setProfile(result.structured_result); setSourceProfile(result.structured_result);
        if (preferencesTableReady) await persistPreferences();
      } else {
        const result = await api<{ document_id: string; structured_result: Profile }>("/resumes/manual-profile", {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ structured_result: profile }),
        });
        setDocumentId(result.document_id); setFilename("Manually created resume");
        setProfile(result.structured_result); setSourceProfile(result.structured_result);
        if (preferencesTableReady) await persistPreferences();
      }
    } catch (caught) {
      setSaveError(caught instanceof Error ? caught.message : "Could not save your profile.");
    } finally { setSaving(false); }
  }

  async function resetSource() {
    setFile(null); setRequestId(""); setError(""); setPhase("idle"); setPhaseLabel("");
    if (fileInput.current) fileInput.current.value = "";
    await loadLatest();
  }

  function setPreference<K extends keyof Preferences>(key: K, value: Preferences[K]) {
    setPreferences((current) => ({ ...current, [key]: value }));
    setPreferencesMessage("");
  }

  async function persistPreferences() {
    await api("/resumes/preferences", {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_preferences: preferences }),
    });
  }

  async function savePreferences() {
    if (!preferencesTableReady || preferencesSaving) return;
    setPreferencesSaving(true); setPreferencesMessage("");
    try { await persistPreferences(); setPreferencesMessage("Preferences saved"); }
    catch (caught) { setPreferencesMessage(caught instanceof Error ? caught.message : "Could not save preferences."); }
    finally { setPreferencesSaving(false); }
  }

  return <div className="page-wrap profile-page">
    <section className="page-intro profile-page-intro">
      <div><div className="eyebrow"><span /> YOUR PRIVATE WORKSPACE</div><h1>Profile</h1><p>Upload a resume or build your profile block by block. Your latest resume stays in this workspace.</p></div>
      <span className={`api-status ${apiOnline ? "online" : "offline"}`}><i />{apiOnline ? "API connected" : "API unavailable"}</span>
    </section>
    <section className="profile-workspace">
      <article className="profile-source-column">
        <section className="profile-upload-card card">
          <div className="source-heading"><div><div className="section-eyebrow">RESUME SOURCE</div><h2>{file ? "Selected resume" : filename || "Upload your resume"}</h2><p>Only your latest resume and its structured profile are kept.</p></div><span className="heading-icon"><Upload size={18} /></span></div>
          {!file && !documentId && <div className={`drop-area profile-drop-area ${dragging ? "dragging" : ""}`} onClick={() => fileInput.current?.click()} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") fileInput.current?.click(); }} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files[0]); }} role="button" tabIndex={0} aria-label="Choose a resume file or drop one here">
            <span className="drop-icon"><ArrowUpFromLine size={20} /></span><strong>Drop your resume here</strong><span className="drop-subline">or <button type="button" onClick={(event) => { event.stopPropagation(); fileInput.current?.click(); }}>browse files</button></span><span className="format-pills"><i>PDF</i><i>DOCX</i><i>TXT</i><span>Up to {maxSizeMb} MB</span></span>
          </div>}
          {(file || documentId) && <div className="profile-source-file"><span className="file-symbol"><FileCheck2 size={17} /></span><div><strong title={file?.name || filename}>{file?.name || filename}</strong><small>{file ? `${formatSize(file.size)} · ${file.name.split(".").pop()?.toUpperCase()} · Ready to analyze` : `Latest resume · ${sourceProfile ? "Profile available" : "Needs analysis"}`}</small></div><button className="source-action" type="button" onClick={() => fileInput.current?.click()} aria-label="Replace resume" title="Replace resume"><Upload size={15} /></button>{file && <button className="source-action remove" type="button" onClick={() => void resetSource()} aria-label="Cancel selected resume"><X size={15} /></button>}</div>}
          <input ref={fileInput} type="file" accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain" hidden onChange={(event) => { chooseFile(event.target.files?.[0]); event.currentTarget.value = ""; }} />
          {fileUrl && <div className="profile-source-preview"><iframe title="Selected resume preview" src={fileUrl} /></div>}
          {textPreview && <pre className="profile-text-preview">{textPreview}</pre>}
          {!file && documentId && filename && <div className="profile-existing-file"><FileText size={16} /><span>Your original file is stored securely with this profile.</span></div>}
          {((file || documentId) && !sourceProfile) && <div className="profile-source-actions"><button className="primary-button" type="button" disabled={busy || !apiOnline} onClick={() => void analyze()}>{busy ? <><LoaderCircle className="spin" size={15} /> {phaseLabel || "Working…"}</> : phase === "error" ? <>Retry extraction <RefreshCw size={14} /></> : documentId ? <>Analyze latest resume <ArrowRight size={14} /></> : <>Upload and extract <ArrowRight size={14} /></>}</button></div>}
          {busy && <div className="profile-process-state"><span className="process-loader"><LoaderCircle className="spin" size={15} /></span><span><strong>{phaseLabel}</strong><small>Your document is processed page by page.</small></span></div>}
          {error && <div className="error-message" role="alert">{error}</div>}
          <div className="privacy-note"><ShieldCheck size={14} /> Your resume belongs to your account. Replacing it removes the previous original and profile.</div>
        </section>

        <section className="profile-preferences-card card">
          <div className="profile-preferences-heading"><span className="heading-icon"><BriefcaseBusiness size={17} /></span><div><span className="section-eyebrow">JOB SEARCH</span><h2>Preferences</h2><p>Set compensation, location, and role preferences for your next opportunity.</p></div></div>
          <div className="preferences-grid">
            <label>Current CTC<div className="preference-input-with-unit"><input value={preferences.current_ctc} onChange={(e) => setPreference("current_ctc", e.target.value)} placeholder="e.g. 8,00,000 per year" /><select value={preferences.currency} onChange={(e) => setPreference("currency", e.target.value)} aria-label="Currency"><option>INR</option><option>USD</option><option>EUR</option><option>GBP</option></select></div></label>
            <label>Expected CTC<input value={preferences.expected_ctc} onChange={(e) => setPreference("expected_ctc", e.target.value)} placeholder="e.g. 12,00,000 per year" /></label>
            <label>Expected CTC range<input value={preferences.expected_ctc_range} onChange={(e) => setPreference("expected_ctc_range", e.target.value)} placeholder="e.g. 10–14 LPA" /></label>
            <label>Minimum expected CTC<input value={preferences.minimum_expected_ctc} onChange={(e) => setPreference("minimum_expected_ctc", e.target.value)} placeholder="e.g. 10,00,000 per year" /></label>
            <label>Preferred locations<input value={joined(preferences.preferred_locations)} onChange={(e) => setPreference("preferred_locations", e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} placeholder="City, region, or remote" /></label>
            <label>Preferred roles<input value={joined(preferences.preferred_job_titles)} onChange={(e) => setPreference("preferred_job_titles", e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} placeholder="Role titles, separated by commas" /></label>
            <label>Work mode<select value={preferences.work_mode} onChange={(e) => setPreference("work_mode", e.target.value)}><option value="">Choose work mode</option><option>On-site</option><option>Hybrid</option><option>Remote</option><option>Flexible</option></select></label>
            <label>Employment type<input value={joined(preferences.employment_types)} onChange={(e) => setPreference("employment_types", e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} placeholder="Full-time, contract, etc." /></label>
            <label>Notice period<input value={preferences.notice_period} onChange={(e) => setPreference("notice_period", e.target.value)} placeholder="e.g. 30 days" /></label>
            <label>Availability<input value={preferences.availability} onChange={(e) => setPreference("availability", e.target.value)} placeholder="e.g. Immediate, from June 2026" /></label>
            <label>Preferred industries<input value={joined(preferences.preferred_industries)} onChange={(e) => setPreference("preferred_industries", e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} placeholder="Industries, separated by commas" /></label>
            <label>Open to relocation<select value={preferences.willing_to_relocate === null ? "" : String(preferences.willing_to_relocate)} onChange={(e) => setPreference("willing_to_relocate", e.target.value === "" ? null : e.target.value === "true")}><option value="">Not specified</option><option value="true">Yes</option><option value="false">No</option></select></label>
          </div>
          <div className="preferences-footer"><span>{preferencesMessage || "Stored in PostgreSQL against your authenticated app_id"}</span><button type="button" className="primary-button" disabled={!preferencesTableReady || preferencesSaving} onClick={() => void savePreferences()}>{preferencesSaving ? "Saving…" : "Save preferences"}</button></div>
        </section>
      </article>

      <section className="profile-fields-column card">
        {profile ? <ResumeEditor embedded mode={documentId ? "edit" : "create"} profile={profile} filename={filename} documentId={documentId} saving={saving} error={saveError} onChange={updateProfile} onSave={() => void saveProfile()} onCancel={() => setProfile(sourceProfile ? structuredClone(sourceProfile) : null)} extraActions={<RexResumeBuilder profile={profile} documentId={documentId} />} /> : <div className="profile-start-state">
          <span className="profile-start-icon"><UserRound size={24} /></span><span className="section-eyebrow">CANDIDATE PROFILE</span><h2>{loaded && !documentId ? "Start your profile" : "Your profile blocks appear here"}</h2><p>{sourceProfile ? "Extracted details are loaded into editable profile blocks." : "Choose how you want to begin. You can upload a resume or fill each profile section yourself."}</p>
          {!sourceProfile && <div className="profile-start-actions"><button className="primary-button" type="button" onClick={() => fileInput.current?.click()}><Upload size={15} /> Upload a resume</button><button className="export-button" type="button" onClick={startManual}><FileText size={15} /> Fill in manually</button></div>}
        </div>}
      </section>
    </section>
    <footer className="app-footer"><span>© 2026 NEXPLY AI</span><span>One current resume. Complete, editable profile blocks.</span><span className={apiOnline ? "footer-online" : "footer-offline"}><i />{apiOnline ? "All systems operational" : "API unavailable"}</span></footer>
  </div>;
}
