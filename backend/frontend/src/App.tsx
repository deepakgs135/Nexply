import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import Auth from "./Auth";
import {
  Activity, ArrowDownToLine, ArrowRight, ArrowUpFromLine, Award, BookOpen,
  Check, ChevronDown, CircleHelp, FileCheck2, FileText,
  GraduationCap, LayoutDashboard, LoaderCircle, LockKeyhole, MapPin, Search,
  ShieldCheck, Sparkles, Upload, X,
} from "lucide-react";

type Profile = Record<string, unknown>;
type RecordItem = Record<string, unknown>;
type ResumeRecord = { document_id?: string; original_filename?: string; structured_result?: Profile };
type Phase = "idle" | "upload" | "parse" | "extract" | "done" | "error";
type AuthUser = { app_id: string; full_name: string; email: string };
type AuthResult = { access_token: string; user: AuthUser };

const API_BASE = import.meta.env.VITE_API_BASE || "";
let accessToken = sessionStorage.getItem("nexply_access_token") || "";
const ACCEPTED = ["pdf", "docx", "txt"];
const KNOWN = new Set([
  "full_name", "professional_title", "email", "phone", "location", "websites",
  "professional_summary", "skills", "experience", "education", "projects",
  "certifications", "languages", "awards", "publications", "volunteer_experience",
  "interests", "references", "additional_sections", "parsed_text", "raw_text",
  "document_id", "_id", "model_config",
]);

function label(value: string) {
  const aliases: Record<string, string> = {
    full_name: "Full name", professional_title: "Professional title",
    professional_summary: "Professional summary", cgpa_or_percentage: "Grade",
    job_title: "Role", start_date: "Start date", end_date: "End date",
    employment_type: "Employment type", field_of_study: "Field of study",
    additional_sections: "Additional information", volunteer_experience: "Volunteer experience",
    publication_date: "Published", url: "Link", technologies: "Technologies",
  };
  return aliases[value] || value.replace(/[_-]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
function valueText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.map(valueText).filter(Boolean).join(" · ");
  if (typeof value === "object") return Object.entries(value as RecordItem)
    .filter(([key, item]) => key !== "model_config" && item !== null && item !== "" && (!Array.isArray(item) || item.length > 0))
    .map(([key, item]) => `${label(key)}: ${valueText(item)}`).join(" · ");
  return "";
}
function objectList(value: unknown): RecordItem[] {
  return Array.isArray(value) ? value.filter((item): item is RecordItem => Boolean(item) && typeof item === "object" && !Array.isArray(item)) : [];
}
function stringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map(valueText).filter(Boolean);
}
function humanDate(item: RecordItem) {
  return [valueText(item.start_date), valueText(item.end_date)].filter(Boolean).join(" – ");
}
function allRows(profile: Profile) {
  const rows: Array<{ section: string; field: string; value: string }> = [];
  const visit = (section: string, field: string, value: unknown) => {
    if (value === null || value === undefined || value === "" || (Array.isArray(value) && !value.length)) return;
    if (Array.isArray(value)) value.forEach((child, index) => visit(section, `${field} ${index + 1}`, child));
    else if (typeof value === "object") Object.entries(value as RecordItem).forEach(([key, child]) => visit(section, `${field} · ${label(key)}`, child));
    else rows.push({ section, field, value: valueText(value) });
  };
  Object.entries(profile).filter(([key]) => !["parsed_text", "raw_text", "document_id", "_id", "model_config"].includes(key))
    .forEach(([key, value]) => visit(label(key), label(key), value));
  return rows;
}
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const result = await response.json().catch(() => ({}));
  if (response.status === 401 && accessToken && !path.startsWith("/auth/")) {
    accessToken = "";
    sessionStorage.removeItem("nexply_access_token");
    window.dispatchEvent(new Event("nexply:auth-expired"));
  }
  if (!response.ok) throw new Error(result.detail || `Request failed (${response.status})`);
  return result as T;
}
function formatSize(bytes: number) {
  return bytes < 1048576 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1048576).toFixed(1)} MB`;
}
function safeUrl(text: string) {
  const match = text.match(/https?:\/\/[^\s]+|www\.[^\s]+/i);
  if (!match) return null;
  const href = match[0].startsWith("www.") ? `https://${match[0]}` : match[0];
  try { const url = new URL(href); return ["http:", "https:"].includes(url.protocol) ? url.href : null; } catch { return null; }
}

function ItemMeta({ item }: { item: RecordItem }) {
  const parts = [valueText(item.company || item.institution || item.publisher || item.organization), humanDate(item), valueText(item.location)];
  return <div className="entry-meta">{parts.filter(Boolean).map((part, index) => <span key={`${part}-${index}`}>{index === 2 && <MapPin size={12} />}{part}</span>)}</div>;
}
function DetailLines({ item, exclude = [] }: { item: RecordItem; exclude?: string[] }) {
  const excluded = new Set(["company", "company_name", "institution", "publisher", "organization", "name", "title", "role", "job_title", "degree", "start_date", "end_date", "location", "employment_type", ...exclude]);
  const entries = Object.entries(item).filter(([key, value]) => !excluded.has(key) && value !== null && value !== "" && (!Array.isArray(value) || value.length > 0));
  const bulletEntries = entries.filter(([key, value]) => ["responsibilities", "achievements", "outcomes", "details", "coursework", "honors"].includes(key) && Array.isArray(value));
  const remaining = entries.filter(([key]) => !bulletEntries.some(([bulletKey]) => bulletKey === key));
  return <>
    {remaining.map(([key, value]) => <div className="detail-line" key={key}><span>{label(key)}</span><strong>{valueText(value)}</strong></div>)}
    {bulletEntries.map(([key, value]) => <div className="bullet-group" key={key}><strong>{label(key)}</strong><ul>{stringList(value).map((text, index) => <li key={`${key}-${index}`}>{text}</li>)}</ul></div>)}
  </>;
}

export default function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState("");
  const [textPreview, setTextPreview] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [phaseLabel, setPhaseLabel] = useState("");
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [query, setQuery] = useState("");
  const [maxSizeMb, setMaxSizeMb] = useState(15);
  const [apiOnline, setApiOnline] = useState(false);
  const [skillsExpanded, setSkillsExpanded] = useState(false);
  const [activeDetail, setActiveDetail] = useState("");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    api<{ max_upload_size_mb: number }>("/api/config")
      .then((config) => { setMaxSizeMb(config.max_upload_size_mb); setApiOnline(true); })
      .catch(() => setApiOnline(false));
    if (!accessToken) { setAuthChecked(true); return; }
    api<AuthUser>("/auth/me")
      .then(setUser)
      .catch(() => { accessToken = ""; sessionStorage.removeItem("nexply_access_token"); })
      .finally(() => setAuthChecked(true));
  }, []);
  useEffect(() => {
    const expireSession = () => signOut();
    window.addEventListener("nexply:auth-expired", expireSession);
    return () => window.removeEventListener("nexply:auth-expired", expireSession);
  }, []);

  function authenticated(result: AuthResult) {
    accessToken = result.access_token;
    sessionStorage.setItem("nexply_access_token", result.access_token);
    setUser(result.user);
  }
  function signOut() {
    accessToken = "";
    sessionStorage.removeItem("nexply_access_token");
    setUser(null);
    setAuthChecked(true);
    reset();
  }
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

  const entries = useMemo(() => profile ? allRows(profile) : [], [profile]);
  const filteredProfile = useMemo(() => {
    if (!profile || !query.trim()) return profile;
    const q = query.trim().toLowerCase();
    const subset: Profile = {};
    for (const [key, value] of Object.entries(profile)) {
      const text = `${label(key)} ${valueText(value)}`.toLowerCase();
      if (text.includes(q)) subset[key] = value;
      else if (Array.isArray(value)) {
        const matching = value.filter((entry) => valueText(entry).toLowerCase().includes(q));
        if (matching.length) subset[key] = matching;
      }
    }
    return subset;
  }, [profile, query]);
  const busy = ["upload", "parse", "extract"].includes(phase);
  const rawRows = useMemo(() => profile ? allRows(Object.fromEntries(Object.entries(profile).filter(([key]) => !KNOWN.has(key)))) : [], [profile]);

  function chooseFile(next?: File) {
    if (!next) return;
    const extension = next.name.split(".").pop()?.toLowerCase() || "";
    if (!ACCEPTED.includes(extension)) { setError("Choose a PDF, DOCX, or TXT resume."); return; }
    if (next.size > maxSizeMb * 1048576) { setError(`This file exceeds the ${maxSizeMb} MB upload limit.`); return; }
    if (!next.size) { setError("This file is empty. Choose a resume with content."); return; }
    setFile(next); setDocumentId(""); setProfile(null); setPhase("idle"); setPhaseLabel(""); setError(""); setQuery(""); setActiveDetail("");
  }
  async function analyze() {
    if (busy || (!file && !documentId)) return;
    setError("");
    try {
      let activeId = documentId;
      if (!activeId && file) {
        setPhase("upload"); setPhaseLabel("Saving original document");
        const body = new FormData(); body.append("file", file);
        const uploaded = await api<{ document_id: string }>("/resumes/upload", { method: "POST", body });
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
    }
  }
  function reset() {
    setFile(null); setDocumentId(""); setProfile(null); setPhase("idle"); setPhaseLabel(""); setError(""); setQuery(""); setActiveDetail("");
    if (inputRef.current) inputRef.current.value = "";
  }
  function exportJson() {
    if (!profile) return;
    const blob = new Blob([JSON.stringify(profile, null, 2)], { type: "application/json" });
    const href = URL.createObjectURL(blob); const anchor = document.createElement("a");
    anchor.href = href; anchor.download = `${file?.name.replace(/\.[^.]+$/, "") || "candidate-profile"}-structured.json`;
    anchor.click(); URL.revokeObjectURL(href);
  }

  const visibleProfile = filteredProfile || {};
  const skills = stringList(visibleProfile.skills);
  const experience = objectList(visibleProfile.experience);
  const education = objectList(visibleProfile.education);
  const projects = objectList(visibleProfile.projects);
  const volunteer = objectList(visibleProfile.volunteer_experience);
  const publications = objectList(visibleProfile.publications);
  const name = valueText(profile?.full_name) || "Candidate profile";
  const title = valueText(profile?.professional_title);
  const visibleEntryCount = allRows(visibleProfile).length;
  const contact = ["email", "phone", "location"].filter((key) => valueText(visibleProfile[key]));
  const customSections = objectList(visibleProfile.additional_sections);
  const links = stringList(visibleProfile.websites);
  const otherSections = Object.entries(visibleProfile).filter(([key, value]) => !KNOWN.has(key) && value !== null && value !== "" && (!Array.isArray(value) || value.length));
  const steps = [
    { id: "upload", label: "Upload", done: ["parse", "extract", "done"].includes(phase) },
    { id: "parse", label: "Read document", done: ["extract", "done"].includes(phase) },
    { id: "extract", label: "Structure profile", done: phase === "done" },
  ];

  if (!user) return <Auth onAuthenticated={authenticated} checking={!authChecked} />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="NEXPLY home"><span className="brand-symbol">N</span><span className="brand-word">NEXPLY<small>AI</small></span></a>
        <button className="workspace-select"><span className="workspace-monogram">T</span><span><small>WORKSPACE</small><strong>Talent operations</strong></span><ChevronDown size={15} /></button>
        <div className="side-caption">WORKSPACE</div>
        <nav className="side-nav" aria-label="Workspace">
          <a className="nav-link selected" href="#workspace"><LayoutDashboard size={17} /><span>Candidate intelligence</span><i /></a>
          <a className="nav-link muted" aria-disabled="true"><FileText size={17} /><span>Job descriptions</span><em>SOON</em></a>
          <a className="nav-link muted" aria-disabled="true"><Activity size={17} /><span>Activity</span><em>SOON</em></a>
        </nav>
        <div className="side-bottom"><div className="privacy-card"><ShieldCheck size={17} /><strong>Designed for responsible review</strong><p>Structured candidate information stays clear and reviewable.</p></div><div className="member-card"><span className="member-avatar">{user.full_name.slice(0, 1).toUpperCase()}</span><span><strong>{user.full_name}</strong><small>{user.email}</small></span><button onClick={signOut} aria-label="Sign out" title="Sign out">↗</button></div></div>
      </aside>

      <main className="main-content" id="workspace">
        <header className="topbar"><div className="breadcrumbs">Workspace <span>/</span> <strong>Candidate intelligence</strong></div><div className="topbar-actions"><span className="privacy-status"><LockKeyhole size={13} /> Private workspace</span><span className="user-dot">{user.full_name.slice(0, 1).toUpperCase()}</span><button className="signout-button" onClick={signOut}>Sign out</button></div></header>
        <div className="page-wrap">
          <section className="page-intro"><div><div className="eyebrow"><span /> CANDIDATE WORKSPACE</div><h1>Candidate intelligence</h1><p>Review a resume alongside every structured detail extracted from it.</p></div><a href="/docs" className="docs-button" target="_blank" rel="noreferrer"><CircleHelp size={15} /> API docs <ArrowRight size={13} /></a></section>
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
                {activeDetail && <div className="selected-source"><span className="selected-source-dot" /><span><small>DETAIL SELECTED</small><strong>{activeDetail}</strong></span></div>}
                <div className="viewer-footer"><ShieldCheck size={13} /> Select a profile detail to mark it for review.</div>
              </>}
              {file && <div className="analysis-controls"><div className={`api-status ${apiOnline ? "online" : "offline"}`}><i />{apiOnline ? "API connected" : "API unavailable"}</div><button className="primary-button" type="button" disabled={busy || !apiOnline} onClick={analyze}>{busy ? <><LoaderCircle className="spin" size={15} /> Working…</> : phase === "done" ? <>Analysis complete <Check size={14} /></> : phase === "error" && documentId ? <>Retry analysis <ArrowRight size={14} /></> : <>Analyze resume <ArrowRight size={14} /></>}</button></div>}
              {(busy || phase === "error") && <div className="progress-panel" aria-live="polite"><strong>{phaseLabel}</strong><div className="progress-steps">{steps.map((step) => <span className={step.done ? "finished" : phase === step.id ? "working" : ""} key={step.id}>{step.done ? <Check size={12} /> : phase === step.id ? <LoaderCircle size={12} className="spin" /> : <i />}{step.label}</span>)}</div>{error && <div className="error-message" role="alert">{error}{documentId && " Your upload is saved; retry to continue."}</div>}</div>}
            </article>

            <article className="profile-card card">
              <div className="profile-toolbar"><div><div className="section-eyebrow">STRUCTURED PROFILE</div><h2>{profile ? name : "Candidate details"}</h2><p>{profile ? `${title ? `${title} · ` : ""}${query ? `${visibleEntryCount} of ${entries.length} details` : `${entries.length} extracted details`} · ${file?.name}` : "Your extracted profile will appear here."}</p></div><div className="toolbar-actions"><label className="profile-search"><Search size={14} /><input aria-label="Search candidate details" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search profile" />{query && <button type="button" aria-label="Clear search" onClick={() => setQuery("")}><X size={13} /></button>}</label><button className="export-button" type="button" disabled={!profile} onClick={exportJson}><ArrowDownToLine size={15} /> Export JSON</button></div></div>
              {!profile ? <div className="empty-profile"><div className="empty-illustration"><div className="illustration-document"><i /><i /><i /><i /></div><span><Sparkles size={16} /></span></div><h3>{file ? "Profile details will appear here" : "Your profile, side by side"}</h3><p>{file ? "Analyze the selected resume to see contact information, experience, skills, education, and more." : "Upload a resume to review the original document next to the complete structured candidate profile."}</p></div> : <>
                <div className="profile-scroll">
                  {(contact.length > 0 || links.length > 0) && <section className="profile-section"><SectionHeading title="Contact" count={contact.length + links.length} /><div className="contact-grid">{contact.map((key) => <div className="contact-row" key={key}><span>{label(key)}</span><strong>{valueText(visibleProfile[key])}</strong></div>)}{links.length > 0 && <div className="contact-row links-row"><span>Links</span><div className="link-pills">{links.map((link, index) => { const href = safeUrl(link); const name = link.match(/^([^:]+):/)?.[1] || link.replace(/^https?:\/\/(www\.)?/, "").split(/[/?#]/)[0]; return href ? <a href={href} target="_blank" rel="noreferrer" key={`${link}-${index}`}>{name} ↗</a> : <span key={`${link}-${index}`}>{link}</span>; })}</div></div>}</div></section>}
                  {valueText(visibleProfile.professional_summary) && <section className="profile-section"><SectionHeading title="Summary" icon={<Sparkles size={14} />} /><p className="summary-text">{valueText(visibleProfile.professional_summary)}</p></section>}
                  {experience.length > 0 && <section className="profile-section"><SectionHeading title="Experience" count={experience.length} />{experience.map((item, index) => <article className={`experience-entry ${activeDetail === `Experience · ${valueText(item.job_title || item.title || item.company)}` ? "entry-selected" : ""}`} key={`exp-${index}`} onClick={() => setActiveDetail(`Experience · ${valueText(item.job_title || item.title || item.company)}`)}><div className="entry-title"><div><strong>{valueText(item.job_title || item.title || item.role) || "Role not specified"}</strong>{valueText(item.company) && <span> · {valueText(item.company)}</span>}</div>{index === 0 && <small className="source-badge">Source details</small>}</div><ItemMeta item={item} /><DetailLines item={item} /></article>)}</section>}
                  {education.length > 0 && <section className="profile-section"><SectionHeading title="Education" count={education.length} icon={<GraduationCap size={15} />} /><div className="entry-list">{education.map((item, index) => <article className="compact-entry" key={`edu-${index}`} onClick={() => setActiveDetail(`Education · ${valueText(item.institution || item.degree)}`)}><div className="entry-title"><div><strong>{valueText(item.degree) || "Education"}</strong>{valueText(item.institution) && <span> · {valueText(item.institution)}</span>}</div></div><ItemMeta item={item} /><DetailLines item={item} exclude={["coursework", "honors"]} />{stringList(item.coursework).length > 0 && <div className="detail-line"><span>Coursework</span><strong>{stringList(item.coursework).join(" · ")}</strong></div>}{stringList(item.honors).length > 0 && <div className="detail-line"><span>Honors</span><strong>{stringList(item.honors).join(" · ")}</strong></div>}</article>)}</div></section>}
                  {skills.length > 0 && <section className="profile-section"><SectionHeading title="Skills" count={skills.length} /><div className="skill-pills">{(skillsExpanded ? skills : skills.slice(0, 18)).map((skill, index) => <button type="button" className={`skill-pill ${activeDetail === `Skills · ${skill}` ? "pill-selected" : ""}`} onClick={() => setActiveDetail(`Skills · ${skill}`)} key={`${skill}-${index}`}>{skill}</button>)}{skills.length > 18 && <button type="button" className="more-pill" onClick={() => setSkillsExpanded(!skillsExpanded)}>{skillsExpanded ? "Show fewer" : `+ ${skills.length - 18} more`}</button>}</div></section>}
                  {projects.length > 0 && <section className="profile-section"><SectionHeading title="Projects" count={projects.length} />{projects.map((item, index) => <article className="project-entry" key={`project-${index}`} onClick={() => setActiveDetail(`Project · ${valueText(item.name)}`)}><div className="entry-title"><strong>{valueText(item.name) || "Project"}</strong>{valueText(item.role) && <span> · {valueText(item.role)}</span>}</div><ItemMeta item={item} />{valueText(item.description) && <p className="project-description">{valueText(item.description)}</p>}<DetailLines item={item} exclude={["description", "technologies"]} />{stringList(item.technologies).length > 0 && <div className="skill-pills small-pills">{stringList(item.technologies).map((technology, i) => <span className="skill-pill" key={`${technology}-${i}`}>{technology}</span>)}</div>}</article>)}</section>}
                  {stringList(visibleProfile.certifications).length > 0 && <section className="profile-section"><SectionHeading title="Certifications" count={stringList(visibleProfile.certifications).length} icon={<Award size={14} />} /><ul className="simple-list">{stringList(visibleProfile.certifications).map((item, index) => <li key={`cert-${index}`}>{item}</li>)}</ul></section>}
                  {publications.length > 0 && <section className="profile-section"><SectionHeading title="Publications" count={publications.length} icon={<BookOpen size={14} />} />{publications.map((item, index) => <article className="publication-entry" key={`pub-${index}`} onClick={() => setActiveDetail(`Publication · ${valueText(item.title)}`)}><strong>{valueText(item.title) || "Publication"}</strong><ItemMeta item={item} />{valueText(item.description) && <p>{valueText(item.description)}</p>}<DetailLines item={item} exclude={["description"]} /></article>)}</section>}
                  {volunteer.length > 0 && <section className="profile-section"><SectionHeading title="Volunteer experience" count={volunteer.length} />{volunteer.map((item, index) => <article className="compact-entry" key={`vol-${index}`}><div className="entry-title"><strong>{valueText(item.job_title || item.title) || "Volunteer"}</strong>{valueText(item.company) && <span> · {valueText(item.company)}</span>}</div><ItemMeta item={item} /><DetailLines item={item} /></article>)}</section>}
                  {(["languages", "awards", "interests", "references" ] as const).map((key) => { const list = stringList(visibleProfile[key]); return list.length ? <section className="profile-section" key={key}><SectionHeading title={label(key)} count={list.length} />{key === "languages" || key === "interests" ? <div className="skill-pills">{list.map((item, index) => <span className="skill-pill" key={`${key}-${index}`}>{item}</span>)}</div> : <ul className="simple-list">{list.map((item, index) => <li key={`${key}-${index}`}>{item}</li>)}</ul>}</section> : null; })}
                  {customSections.length > 0 && <section className="profile-section"><SectionHeading title="Additional information" count={customSections.length} />{customSections.map((item, index) => <article className="publication-entry" key={`custom-${index}`}><strong>{valueText(item.title) || "Additional information"}</strong><DetailLines item={item} /></article>)}</section>}
                  {otherSections.length > 0 && <section className="profile-section"><SectionHeading title="Other extracted details" count={rawRows.length} />{rawRows.map((row, index) => <div className="detail-line raw-detail" key={`raw-${index}`}><span>{row.section} · {row.field}</span><strong>{row.value}</strong></div>)}</section>}
                  {visibleEntryCount === 0 && <div className="no-profile-results">{query ? `No profile details match “${query}”. Clear the search to see all extracted information.` : "No structured profile details were returned from this resume."}</div>}
                </div>
                <div className="profile-footer"><span><ShieldCheck size={13} /> Extracted from the source document</span><span>Review for accuracy before use</span></div>
              </>}
            </article>
          </section>
          <footer className="app-footer"><span>© 2026 NEXPLY AI</span><span>Structured candidate information for thoughtful review.</span><span className={apiOnline ? "footer-online" : "footer-offline"}><i />{apiOnline ? "All systems operational" : "API unavailable"}</span></footer>
        </div>
      </main>
    </div>
  );
}

function SectionHeading({ title, count, icon }: { title: string; count?: number; icon?: ReactNode }) {
  return <div className="profile-section-heading">{icon && <span className="section-heading-icon">{icon}</span>}<h3>{title}</h3>{count !== undefined && <span className="section-count">{count}</span>}</div>;
}
