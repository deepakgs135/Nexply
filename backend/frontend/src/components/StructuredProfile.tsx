import { useEffect, useMemo, useState } from "react";
import { ArrowDownToLine, Award, BookOpen, GraduationCap, Pencil, Save, Search, ShieldCheck, Sparkles, X } from "lucide-react";
import { api, downloadBlob } from "../shared/api";
import {
  allRows, DetailLines, isMissingValue, ItemMeta, label, objectList, safeUrl, SectionHeading,
  stringList, valueText, type Profile,
} from "../shared/resumeFormat";

const STANDARD_FIELDS = new Set([
  "full_name", "professional_title", "email", "phone", "location", "websites",
  "professional_summary", "skills", "experience", "education", "projects",
  "certifications", "languages", "awards", "publications", "volunteer_experience",
  "interests", "references", "additional_sections", "parsed_text", "raw_text",
  "document_id", "_id", "model_config",
]);

export default function StructuredProfile({
  profile,
  filename,
  parsingStatus,
  extractionStatus,
  documentId,
  onProfileSaved,
}: {
  profile: Profile | null;
  filename?: string;
  parsingStatus?: string;
  extractionStatus?: string;
  documentId?: string;
  onProfileSaved?: (profile: Profile) => void;
}) {
  const [query, setQuery] = useState("");
  const [skillsExpanded, setSkillsExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Profile>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [aiOpen, setAiOpen] = useState(false);
  const [aiModels, setAiModels] = useState<string[]>([]);
  const [aiModel, setAiModel] = useState("");
  const [aiModelsLoading, setAiModelsLoading] = useState(false);
  const [aiJobDescription, setAiJobDescription] = useState("");
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiExporting, setAiExporting] = useState(false);
  const [aiError, setAiError] = useState("");
  const [aiResult, setAiResult] = useState<{ model: string; structured_result: Profile } | null>(null);
  useEffect(() => { setDraft(profile ? structuredClone(profile) : {}); }, [profile]);
  useEffect(() => {
    if (!aiOpen || aiModels.length) return;
    setAiModelsLoading(true);
    api<{ models: string[]; default_model: string }>("/resumes/ai/models")
      .then((result) => { setAiModels(result.models); setAiModel(result.default_model); })
      .catch((error) => setAiError(error instanceof Error ? error.message : "Could not load local Ollama models."))
      .finally(() => setAiModelsLoading(false));
  }, [aiOpen, aiModels.length]);

  function changeAt(path: (string | number)[], next: unknown) {
    setDraft((current) => {
      const copy = structuredClone(current) as Record<string, unknown>;
      let parent: any = copy;
      for (const part of path.slice(0, -1)) parent = parent[part];
      parent[path[path.length - 1]] = next;
      return copy;
    });
  }
  function removeAt(path: (string | number)[]) {
    setDraft((current) => {
      const copy = structuredClone(current) as Record<string, unknown>;
      let parent: any = copy;
      for (const part of path.slice(0, -1)) parent = parent[part];
      const key = path[path.length - 1];
      if (Array.isArray(parent)) parent.splice(Number(key), 1); else delete parent[key];
      return copy;
    });
  }
  async function saveProfile() {
    if (!documentId) return;
    setSaving(true); setSaveError("");
    try {
      const result = await api<{ structured_result: Profile }>(`/resumes/${encodeURIComponent(documentId)}/structured-result`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ structured_result: draft }),
      });
      setDraft(result.structured_result); setEditing(false); onProfileSaved?.(result.structured_result);
    } catch (error) { setSaveError(error instanceof Error ? error.message : "Unable to save profile changes."); }
    finally { setSaving(false); }
  }
  async function generateAIResume() {
    if (!documentId) return;
    setAiGenerating(true); setAiError(""); setAiResult(null);
    try {
      const result = await api<{ model: string; structured_result: Profile }>(`/resumes/${encodeURIComponent(documentId)}/ai-resume`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: aiModel, target_job_description: aiJobDescription.trim() || null }),
      });
      setAiResult(result);
    } catch (error) { setAiError(error instanceof Error ? error.message : "AI resume generation failed."); }
    finally { setAiGenerating(false); }
  }
  async function exportAIResume() {
    if (!documentId || !aiResult) return;
    setAiExporting(true); setAiError("");
    try {
      const blob = await downloadBlob(`/resumes/${encodeURIComponent(documentId)}/ai-resume/export`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ structured_result: aiResult.structured_result }),
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = `${valueText(aiResult.structured_result.full_name).replace(/[^A-Za-z0-9_-]+/g, "-") || "candidate"}-resume.docx`;
      anchor.click(); URL.revokeObjectURL(url);
    } catch (error) { setAiError(error instanceof Error ? error.message : "Could not export the AI resume."); }
    finally { setAiExporting(false); }
  }

  const filteredProfile = useMemo(() => {
    if (!profile || !query.trim()) return profile;
    const term = query.trim().toLowerCase();
    const matching: Profile = {};
    for (const [key, value] of Object.entries(profile)) {
      if (`${label(key)} ${valueText(value)}`.toLowerCase().includes(term)) {
        matching[key] = value;
      } else if (Array.isArray(value)) {
        const children = value.filter((item) => valueText(item).toLowerCase().includes(term));
        if (children.length) matching[key] = children;
      }
    }
    return matching;
  }, [profile, query]);

  const visible = filteredProfile || {};
  const rows = allRows(visible);
  const totalRows = profile ? allRows(profile).length : 0;
  const contact = ["email", "phone", "location"].filter((key) => valueText(visible[key]));
  const links = stringList(visible.websites);
  const skills = stringList(visible.skills);
  const experience = objectList(visible.experience);
  const education = objectList(visible.education);
  const projects = objectList(visible.projects);
  const publications = objectList(visible.publications);
  const volunteer = objectList(visible.volunteer_experience);
  const customSections = objectList(visible.additional_sections);
  const otherSections = Object.entries(visible).filter(([key, value]) =>
    !STANDARD_FIELDS.has(key) && !isMissingValue(value) && !/(?:^|[_\s-])(null|none|undefined|n\/a|na)$/i.test(key.trim()),
  );
  const candidateName = valueText(profile?.full_name) || "Candidate details";

  function exportJson() {
    if (!profile) return;
    const blob = new Blob([JSON.stringify(profile, null, 2)], { type: "application/json" });
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = `${filename?.replace(/\.[^.]+$/, "") || "candidate-profile"}-structured.json`;
    anchor.click();
    URL.revokeObjectURL(objectUrl);
  }

  return <div className="history-structured-profile profile-card card">
    <div className="profile-toolbar history-structured-toolbar">
      <div className="history-profile-title">
        <div className="section-eyebrow">STRUCTURED PROFILE</div>
        <h2>{candidateName}</h2>
        <p>{profile ? `${rows.length} of ${totalRows} extracted details · ${filename || "Resume"}` : filename || "Resume profile"}</p>
        <div className="history-status-pair">
          <span className={`history-status ${parsingStatus === "completed" ? "complete" : "pending"}`}>Text {parsingStatus || "pending"}</span>
          <span className={`history-status ${extractionStatus === "completed" ? "complete" : extractionStatus === "failed" ? "failed" : "pending"}`}>Extraction {extractionStatus || "pending"}</span>
        </div>
      </div>
      <div className="toolbar-actions">
        <label className="profile-search"><Search size={14} /><input aria-label="Search selected resume profile" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search profile" />{query && <button type="button" aria-label="Clear search" onClick={() => setQuery("")}><X size={13} /></button>}</label>
        {documentId && (editing ? <><button className="export-button" type="button" disabled={saving} onClick={() => { setDraft(profile ? structuredClone(profile) : {}); setEditing(false); setSaveError(""); }}>Cancel</button><button className="export-button profile-save-button" type="button" disabled={saving} onClick={saveProfile}>{saving ? "Saving…" : <><Save size={14} /> Save changes</>}</button></> : <><button className="export-button" type="button" disabled={!profile} onClick={() => setEditing(true)} aria-label="Edit structured profile"><Pencil size={14} /> Edit</button><button className="export-button ai-smart-button" type="button" disabled={!profile} onClick={() => { setAiError(""); setAiResult(null); setAiOpen(true); }}><Sparkles size={14} /> AI Smart</button></>)}
        <button className="export-button" type="button" disabled={!profile} onClick={exportJson}><ArrowDownToLine size={15} /> Export JSON</button>
      </div>
    </div>

    {editing && <div className="profile-editor" aria-label="Edit all structured profile fields"><p>Edit any value or link. Use the controls beside lists to add or remove entries.</p><ProfileEditor value={draft} path={[]} onChange={changeAt} onRemove={removeAt} />{saveError && <div className="history-error" role="alert">{saveError}</div>}</div>}

    {aiOpen && <div className="ai-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !aiGenerating && !aiExporting) setAiOpen(false); }}><section className="ai-modal" role="dialog" aria-modal="true" aria-labelledby="ai-modal-title"><header className="ai-modal-header"><div><span className="ai-modal-icon"><Sparkles size={18} /></span><div><span className="section-eyebrow">AI SMART</span><h2 id="ai-modal-title">Create a polished resume</h2><p>Use your structured profile as the source. The generated draft won’t replace it.</p></div></div><button type="button" className="ai-modal-close" aria-label="Close AI Smart" onClick={() => setAiOpen(false)} disabled={aiGenerating || aiExporting}><X size={18} /></button></header><div className="ai-modal-body"><label className="ai-form-field"><span>Writing model</span><select value={aiModel} disabled={aiModelsLoading || aiGenerating || !aiModels.length} onChange={(event) => setAiModel(event.target.value)}>{aiModels.length ? aiModels.map((model) => <option key={model} value={model}>{model}{model === "llama3.1:8b" ? " · Recommended" : ""}</option>) : <option value="">{aiModelsLoading ? "Loading local models…" : "No models available"}</option>}</select><small>Runs locally with one of your installed Ollama models.</small></label><label className="ai-form-field"><span>Target job description <em>Optional</em></span><textarea rows={5} maxLength={12000} value={aiJobDescription} disabled={aiGenerating} onChange={(event) => setAiJobDescription(event.target.value)} placeholder="Paste a job description to tailor emphasis and wording. Leave blank for a general resume polish." /><small>{aiJobDescription.length.toLocaleString()} / 12,000 characters</small></label>{aiError && <div className="ai-error" role="alert">{aiError}</div>}{aiGenerating && <div className="ai-progress"><span className="ai-spinner"><Sparkles size={15} /></span><span><strong>Writing your resume</strong><small>Reviewing and refining the structured profile with Ollama…</small></span></div>}{aiResult && <section className="ai-result-card"><div className="ai-result-heading"><div><span className="history-status complete">Draft ready</span><small>Generated with {aiResult.model}</small></div><strong>{valueText(aiResult.structured_result.full_name) || "Candidate resume"}</strong><p>{valueText(aiResult.structured_result.professional_title)}</p></div>{valueText(aiResult.structured_result.professional_summary) && <p className="ai-result-summary">{valueText(aiResult.structured_result.professional_summary)}</p>}<div className="ai-result-counts"><span>{objectList(aiResult.structured_result.experience).length} experience entries</span><span>{stringList(aiResult.structured_result.skills).length} skills</span><span>{objectList(aiResult.structured_result.education).length} education entries</span></div></section>}</div><footer className="ai-modal-footer"><button className="ai-secondary-button" type="button" onClick={() => setAiOpen(false)} disabled={aiGenerating || aiExporting}>Close</button>{aiResult && <button className="ai-secondary-button" type="button" onClick={exportAIResume} disabled={aiExporting}>{aiExporting ? "Preparing…" : <><ArrowDownToLine size={15} /> Export DOCX</>}</button>}<button className="ai-primary-button" type="button" onClick={generateAIResume} disabled={!aiModel || aiModelsLoading || aiGenerating || aiExporting}>{aiGenerating ? "Generating…" : aiResult ? "Regenerate draft" : <><Sparkles size={15} /> Generate resume</>}</button></footer></section></div>}

    {editing ? null : !profile ? <div className="history-profile-empty">
      <div className="empty-illustration"><div className="illustration-document"><i /><i /><i /><i /></div><span><Sparkles size={16} /></span></div>
      <h3>{extractionStatus === "failed" ? "Extraction needs attention" : "No structured profile yet"}</h3>
      <p>{extractionStatus === "failed" ? "Open Candidate intelligence to retry extraction for this resume." : "This resume has not produced structured candidate details."}</p>
    </div> : <>
      <div className="profile-scroll history-structured-scroll">
        {(contact.length > 0 || links.length > 0) && <section className="profile-section"><SectionHeading title="Contact" count={contact.length + links.length} /><div className="contact-grid">{contact.map((key) => <div className="contact-row" key={key}><span>{label(key)}</span><strong>{valueText(visible[key])}</strong></div>)}{links.length > 0 && <div className="contact-row links-row"><span>Links</span><div className="link-pills">{links.map((link, index) => { const href = safeUrl(link); const text = link.match(/^([^:]+):/)?.[1] || link.replace(/^https?:\/\/(www\.)?/, "").split(/[/?#]/)[0]; return href ? <a href={href} target="_blank" rel="noreferrer" key={`${link}-${index}`}>{text} ↗</a> : <span key={`${link}-${index}`}>{link}</span>; })}</div></div>}</div></section>}
        {valueText(visible.professional_summary) && <section className="profile-section"><SectionHeading title="Summary" icon={<Sparkles size={14} />} /><p className="summary-text">{valueText(visible.professional_summary)}</p></section>}
        {experience.length > 0 && <section className="profile-section"><SectionHeading title="Experience" count={experience.length} />{experience.map((item, index) => <article className="experience-entry" key={`experience-${index}`}><div className="entry-title"><div><strong>{valueText(item.job_title || item.title || item.role) || "Role not specified"}</strong>{valueText(item.company) && <span> · {valueText(item.company)}</span>}</div></div><ItemMeta item={item} /><DetailLines item={item} /></article>)}</section>}
        {education.length > 0 && <section className="profile-section"><SectionHeading title="Education" count={education.length} icon={<GraduationCap size={15} />} /><div className="entry-list">{education.map((item, index) => <article className="compact-entry" key={`education-${index}`}><div className="entry-title"><div><strong>{valueText(item.degree) || "Education"}</strong>{valueText(item.institution) && <span> · {valueText(item.institution)}</span>}</div></div><ItemMeta item={item} /><DetailLines item={item} exclude={["coursework", "honors"]} />{stringList(item.coursework).length > 0 && <div className="detail-line"><span>Coursework</span><strong>{stringList(item.coursework).join(" · ")}</strong></div>}{stringList(item.honors).length > 0 && <div className="detail-line"><span>Honors</span><strong>{stringList(item.honors).join(" · ")}</strong></div>}</article>)}</div></section>}
        {skills.length > 0 && <section className="profile-section"><SectionHeading title="Skills" count={skills.length} /><div className="skill-pills">{(skillsExpanded ? skills : skills.slice(0, 18)).map((skill, index) => <span className="skill-pill" key={`skill-${index}`}>{skill}</span>)}{skills.length > 18 && <button type="button" className="more-pill" onClick={() => setSkillsExpanded((expanded) => !expanded)}>{skillsExpanded ? "Show fewer" : `+ ${skills.length - 18} more`}</button>}</div></section>}
        {projects.length > 0 && <section className="profile-section"><SectionHeading title="Projects" count={projects.length} />{projects.map((item, index) => <article className="project-entry" key={`project-${index}`}><div className="entry-title"><strong>{valueText(item.name) || "Project"}</strong>{valueText(item.role) && <span> · {valueText(item.role)}</span>}</div><ItemMeta item={item} />{valueText(item.description) && <p className="project-description">{valueText(item.description)}</p>}<DetailLines item={item} exclude={["description", "technologies"]} />{stringList(item.technologies).length > 0 && <div className="skill-pills small-pills">{stringList(item.technologies).map((technology, i) => <span className="skill-pill" key={`technology-${i}`}>{technology}</span>)}</div>}</article>)}</section>}
        {stringList(visible.certifications).length > 0 && <section className="profile-section"><SectionHeading title="Certifications" count={stringList(visible.certifications).length} icon={<Award size={14} />} /><ul className="simple-list">{stringList(visible.certifications).map((item, index) => <li key={`certification-${index}`}>{item}</li>)}</ul></section>}
        {publications.length > 0 && <section className="profile-section"><SectionHeading title="Publications" count={publications.length} icon={<BookOpen size={14} />} />{publications.map((item, index) => <article className="publication-entry" key={`publication-${index}`}><strong>{valueText(item.title) || "Publication"}</strong><ItemMeta item={item} />{valueText(item.description) && <p>{valueText(item.description)}</p>}<DetailLines item={item} exclude={["description"]} /></article>)}</section>}
        {volunteer.length > 0 && <section className="profile-section"><SectionHeading title="Volunteer experience" count={volunteer.length} />{volunteer.map((item, index) => <article className="compact-entry" key={`volunteer-${index}`}><div className="entry-title"><strong>{valueText(item.job_title || item.title) || "Volunteer"}</strong>{valueText(item.company) && <span> · {valueText(item.company)}</span>}</div><ItemMeta item={item} /><DetailLines item={item} /></article>)}</section>}
        {(["languages", "awards", "interests", "references"] as const).map((key) => { const values = stringList(visible[key]); return values.length ? <section className="profile-section" key={key}><SectionHeading title={label(key)} count={values.length} />{key === "languages" || key === "interests" ? <div className="skill-pills">{values.map((item, index) => <span className="skill-pill" key={`${key}-${index}`}>{item}</span>)}</div> : <ul className="simple-list">{values.map((item, index) => <li key={`${key}-${index}`}>{item}</li>)}</ul>}</section> : null; })}
        {customSections.length > 0 && <section className="profile-section"><SectionHeading title="Additional information" count={customSections.length} />{customSections.map((item, index) => <article className="publication-entry" key={`custom-${index}`}><strong>{valueText(item.title) || "Additional information"}</strong><DetailLines item={item} /></article>)}</section>}
        {otherSections.length > 0 && <section className="profile-section"><SectionHeading title="Other extracted details" count={allRows(Object.fromEntries(otherSections)).length} />{allRows(Object.fromEntries(otherSections)).map((row, index) => <div className="detail-line raw-detail" key={`other-${index}`}><span>{row.section} · {row.field}</span><strong>{row.value}</strong></div>)}</section>}
        {rows.length === 0 && <div className="no-profile-results">{query ? `No profile details match “${query}”. Clear the search to see all extracted information.` : "No structured profile details were returned from this resume."}</div>}
      </div>
      <div className="profile-footer"><span><ShieldCheck size={13} /> Extracted from the selected resume</span><span>Review for accuracy before use</span></div>
    </>}
  </div>;
}

function ProfileEditor({ value, path, onChange, onRemove }: { value: unknown; path: (string | number)[]; onChange: (path: (string | number)[], value: unknown) => void; onRemove: (path: (string | number)[]) => void }) {
  if (Array.isArray(value)) return <div className="profile-edit-array">{value.map((item, index) => <div className="profile-edit-item" key={index}><ProfileEditor value={item} path={[...path, index]} onChange={onChange} onRemove={onRemove} /><button type="button" className="profile-remove" aria-label="Remove item" onClick={() => onRemove([...path, index])}>Remove</button></div>)}<button type="button" className="profile-add" onClick={() => { const key = String(path[path.length - 1] ?? ""); const empty: Record<string, unknown> = key === "education" ? {} : key === "experience" || key === "volunteer_experience" ? {} : key === "projects" ? { name: "" } : key === "publications" ? { title: "" } : key === "additional_sections" ? { title: "", details: [] } : {}; onChange(path, [...value, value.length || !["education", "experience", "volunteer_experience", "projects", "publications", "additional_sections"].includes(key) ? (value[0] && typeof value[0] === "object" ? empty : "") : empty]); }}>+ Add item</button></div>;
  if (value && typeof value === "object") return <div className={`profile-edit-object ${path.length === 0 ? "profile-edit-root" : ""}`}>{Object.entries(value as Record<string, unknown>).map(([key, child]) => <div className="profile-edit-field" key={key}><label>{label(key)}</label><div className="profile-edit-control"><ProfileEditor value={child} path={[...path, key]} onChange={onChange} onRemove={onRemove} /><button type="button" className="profile-remove" aria-label={`Remove ${label(key)}`} onClick={() => onRemove([...path, key])}>Remove</button></div></div>)}<button type="button" className="profile-add" onClick={() => { const key = window.prompt("New field name"); if (key && !Object.hasOwn(value, key)) onChange(path, { ...value, [key]: "" }); }}>+ Add field</button></div>;
  const key = String(path[path.length - 1] ?? "");
  if (typeof value === "boolean") return <select className="profile-edit-input" aria-label={label(key)} value={String(value)} onChange={(event) => onChange(path, event.target.value === "true")}><option value="true">true</option><option value="false">false</option></select>;
  if (typeof value === "number") return <input className="profile-edit-input" aria-label={label(key)} type="number" value={value} onChange={(event) => onChange(path, event.target.value === "" ? null : Number(event.target.value))} />;
  if (typeof value === "string" && (value.length > 100 || ["professional_summary", "description", "responsibilities", "achievements", "outcomes", "details"].includes(key))) return <textarea className="profile-edit-input profile-edit-textarea" aria-label={label(key)} rows={4} value={value} onChange={(event) => onChange(path, event.target.value)} />;
  return <input className="profile-edit-input" aria-label={label(key)} type="text" value={value == null ? "" : String(value)} placeholder={value === null ? "Not provided" : ""} onChange={(event) => onChange(path, event.target.value === "" && value === null ? null : event.target.value)} />;
}
