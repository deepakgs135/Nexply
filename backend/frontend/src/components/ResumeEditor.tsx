import { useEffect, useState, type ReactNode } from "react";
import { ArrowDownToLine, Check, LoaderCircle, Plus, Save, Sparkles, Trash2, X } from "lucide-react";
import { api } from "../shared/api";
import { isMissingFieldName, isMissingValue, label, objectList, stringList, valueText, type Profile, type RecordItem } from "../shared/resumeFormat";

type Path = (string | number)[];
type FieldSpec = { key: string; title?: string; multiline?: boolean; number?: boolean };

export default function ResumeEditor({
  profile, filename, documentId, saving, error, onChange, onSave, onCancel,
}: {
  profile: Profile; filename?: string; documentId: string; saving: boolean; error: string;
  onChange: (path: Path, value: unknown) => void; onSave: () => void; onCancel: () => void;
}) {
  useEffect(() => {
    document.body.classList.add("resume-editor-open");
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape" && !saving) onCancel(); };
    window.addEventListener("keydown", onKey);
    return () => { window.removeEventListener("keydown", onKey); document.body.classList.remove("resume-editor-open"); };
  }, [saving, onCancel]);

  async function rewriteWithRex(path: Path, style: "concise" | "brief" | "elaborate") {
    const result = await api<{ rewritten_text: string }>(`/resumes/${encodeURIComponent(documentId)}/rex/rewrite`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ field_path: path, style }),
    });
    return result.rewritten_text;
  }

  return <div className="resume-editor-overlay">
    <header className="resume-editor-header"><div className="resume-editor-brand"><span className="resume-editor-mark">N</span><div><span className="section-eyebrow">NEXPLY RESUME STUDIO</span><strong>Edit your resume</strong><small title={filename}>{filename || "Structured candidate profile"}</small></div></div><div className="resume-editor-actions"><span className="resume-editor-saved"><Check size={14} /> Changes save to this resume</span><button className="resume-editor-button secondary" type="button" onClick={onCancel} disabled={saving}><X size={15} /> Cancel</button><button className="resume-editor-button secondary" type="button" onClick={() => window.print()} disabled={saving}><ArrowDownToLine size={15} /> Export PDF</button><button className="resume-editor-button primary" type="button" onClick={onSave} disabled={saving}>{saving ? "Saving…" : <><Save size={15} /> Save changes</>}</button></div></header>
    <main className="resume-editor-main">
      <div className="resume-editor-left">
        <div className="resume-editor-intro"><span className="section-eyebrow">MAKE IT YOURS</span><h1>Edit your resume</h1><p>Update each field on the left and review the live resume preview on the right.</p></div>
        <nav className="resume-editor-nav" aria-label="Resume sections">{["profile", "experience", "education", "skills", "projects", "certifications", "publications", "volunteer_experience", "additional_sections"].map((key) => <a href={`#edit-${key}`} key={key}>{key === "additional_sections" ? "Research & Other" : label(key)}</a>)}</nav>
        {error && <div className="ai-error resume-editor-error" role="alert">{error}</div>}
        <section className="resume-edit-section" id="edit-profile"><SectionTitle number="01" title="Profile" /><div className="resume-edit-grid">
          <Field profile={profile} path={["full_name"]} title="Full name" onChange={onChange} onRewrite={rewriteWithRex} />
          <Field profile={profile} path={["professional_title"]} title="Professional headline" onChange={onChange} onRewrite={rewriteWithRex} />
          <Field profile={profile} path={["email"]} title="Email" onChange={onChange} onRewrite={rewriteWithRex} />
          <Field profile={profile} path={["phone"]} title="Phone" onChange={onChange} onRewrite={rewriteWithRex} />
          <Field profile={profile} path={["location"]} title="Location" onChange={onChange} onRewrite={rewriteWithRex} />
          <div className="resume-edit-field full-width"><StringListEditor title="Links and websites" values={editableListValues(profile.websites)} path={["websites"]} onChange={onChange} placeholder="https://…" /></div>
          <Field profile={profile} path={["professional_summary"]} title="Professional summary" multiline onChange={onChange} onRewrite={rewriteWithRex} />
        </div></section>
        <ObjectCollection profile={profile} collection="experience" number="02" title="Experience" fields={[
          { key: "job_title", title: "Job title" }, { key: "company", title: "Company" }, { key: "location", title: "Location" }, { key: "employment_type", title: "Employment type" }, { key: "start_date", title: "Start date" }, { key: "end_date", title: "End date" }, { key: "description", title: "Description", multiline: true },
        ]} lists={[{ key: "responsibilities", title: "Responsibilities", multiline: true }, { key: "achievements", title: "Achievements", multiline: true }, { key: "technologies", title: "Technologies" }]} onChange={onChange} onRewrite={rewriteWithRex} />
        <ObjectCollection profile={profile} collection="education" number="03" title="Education" fields={[
          { key: "degree", title: "Degree" }, { key: "field_of_study", title: "Field of study" }, { key: "institution", title: "Institution" }, { key: "location", title: "Location" }, { key: "start_date", title: "Start date" }, { key: "end_date", title: "End date" }, { key: "graduation_year", title: "Graduation year", number: true }, { key: "cgpa_or_percentage", title: "Grade" },
        ]} lists={[{ key: "coursework", title: "Coursework" }, { key: "honors", title: "Honors" }]} onChange={onChange} onRewrite={rewriteWithRex} />
        <StringSection profile={profile} field="skills" number="04" onChange={onChange} />
        <ObjectCollection profile={profile} collection="projects" number="05" title="Projects" fields={[
          { key: "name", title: "Project name" }, { key: "role", title: "Role" }, { key: "start_date", title: "Start date" }, { key: "end_date", title: "End date" }, { key: "url", title: "Project link" }, { key: "description", title: "Description", multiline: true },
        ]} lists={[{ key: "technologies", title: "Technologies" }, { key: "responsibilities", title: "Responsibilities", multiline: true }, { key: "outcomes", title: "Outcomes", multiline: true }]} onChange={onChange} onRewrite={rewriteWithRex} />
        <StringSection profile={profile} field="certifications" number="06" onChange={onChange} />
        <StringSection profile={profile} field="awards" number="07" onChange={onChange} />
        <ObjectCollection profile={profile} collection="publications" number="08" title="Publications" fields={[
          { key: "title", title: "Publication title" }, { key: "publisher", title: "Publisher / venue" }, { key: "publication_date", title: "Publication date" }, { key: "url", title: "Publication link" }, { key: "description", title: "Description", multiline: true },
        ]} onChange={onChange} onRewrite={rewriteWithRex} />
        <ObjectCollection profile={profile} collection="volunteer_experience" number="09" title="Volunteer experience" fields={[
          { key: "job_title", title: "Role" }, { key: "company", title: "Organization" }, { key: "location", title: "Location" }, { key: "start_date", title: "Start date" }, { key: "end_date", title: "End date" }, { key: "description", title: "Description", multiline: true },
        ]} lists={[{ key: "responsibilities", title: "Responsibilities", multiline: true }, { key: "achievements", title: "Achievements", multiline: true }, { key: "technologies", title: "Skills / tools" }]} onChange={onChange} onRewrite={rewriteWithRex} />
        <StringSection profile={profile} field="languages" number="10" onChange={onChange} />
        <StringSection profile={profile} field="interests" number="11" onChange={onChange} />
        <StringSection profile={profile} field="references" number="12" onChange={onChange} />
        <ObjectCollection profile={profile} collection="additional_sections" number="13" title="Research & Other Sections" fields={[{ key: "title", title: "Section title" }]} lists={[{ key: "details", title: "Details", multiline: true }]} onChange={onChange} onRewrite={rewriteWithRex} addResearch />
      </div>
      <aside className="resume-editor-right"><div className="resume-preview-heading"><div><span className="section-eyebrow">YOUR STORY AT A GLANCE</span><h2>Live preview</h2></div><span>Updates as you type</span></div><div className="resume-paper-wrap"><ResumePreview profile={profile} /></div></aside>
    </main>
  </div>;
}

function SectionTitle({ number, title }: { number: string; title: string }) {
  return <div className="resume-edit-title"><span>{number}</span><h2>{title}</h2><i /></div>;
}

function readPath(profile: Profile, path: Path): unknown {
  let value: unknown = profile;
  for (const part of path) value = value && typeof value === "object" ? (value as Record<string | number, unknown>)[part] : undefined;
  return value;
}

function Field({ profile, path, title, multiline = false, number = false, onChange, onRewrite }: { profile: Profile; path: Path; title: string; multiline?: boolean; number?: boolean; onChange: (path: Path, value: unknown) => void; onRewrite: (path: Path, style: "concise" | "brief" | "elaborate") => Promise<string> }) {
  const [rewriting, setRewriting] = useState(false);
  const [rewriteError, setRewriteError] = useState("");
  const [showRexOptions, setShowRexOptions] = useState(false);
  const value = readPath(profile, path);
  const text = isMissingValue(value) ? "" : String(value);
  const canRewrite = multiline && (path[0] === "professional_summary" || path[path.length - 1] === "description");
  async function runRex(style: "concise" | "brief" | "elaborate") {
    setRewriting(true); setRewriteError("");
    setShowRexOptions(false);
    try { onChange(path, await onRewrite(path, style)); }
    catch (error) { setRewriteError(error instanceof Error ? error.message : "REX could not rewrite this field."); }
    finally { setRewriting(false); }
  }
  return <div className={`resume-edit-field ${multiline ? "full-width" : ""}`}><div className="resume-edit-field-heading"><span>{title}</span>{canRewrite && <button className="rex-field-button" type="button" onClick={() => setShowRexOptions((open) => !open)} disabled={rewriting} title="Rewrite or draft this field with REX">{rewriting ? <LoaderCircle size={13} className="spin" /> : <Sparkles size={13} />} {rewriting ? "REX is writing…" : "REX"}</button>}</div>{showRexOptions && <div className="rex-style-options" aria-label="Choose REX writing style"><span>{text.trim() ? "Rewrite style" : "Draft style"}</span>{(["concise", "brief", "elaborate"] as const).map((style) => <button type="button" key={style} onClick={() => void runRex(style)}>{style[0].toUpperCase() + style.slice(1)}</button>)}</div>}{multiline ? <textarea rows={4} value={text} onChange={(event) => onChange(path, event.target.value)} /> : <input type={number ? "number" : "text"} value={text} onChange={(event) => onChange(path, number ? (event.target.value ? Number(event.target.value) : null) : event.target.value)} />}{rewriteError && <small className="rex-field-error" role="alert">{rewriteError}</small>}</div>;
}

function editableListValues(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function StringListEditor({ title, values, path, onChange, placeholder = "Add a detail" }: { title: string; values: unknown[]; path: Path; onChange: (path: Path, value: unknown) => void; placeholder?: string }) {
  const visible = values.map((value, index) => ({ value, index })).filter(({ value }) => value === "" || !isMissingValue(value));
  return <div className="resume-list-editor"><span className="resume-list-title">{title}</span>{visible.map(({ value, index }) => <div className="resume-list-row" key={index}><input aria-label={`${title} ${index + 1}`} value={isMissingValue(value) ? "" : String(value)} placeholder={placeholder} onChange={(event) => onChange([...path, index], event.target.value)} /><button type="button" title="Remove item" aria-label={`Remove ${title} ${index + 1}`} onClick={() => onChange(path, values.filter((_, current) => current !== index))}><Trash2 size={14} /></button></div>)}<button className="resume-add-button" type="button" onClick={() => onChange(path, [...values, ""])}><Plus size={15} /> Add {title.toLowerCase().replace(/s$/, "")}</button></div>;
}

function StringSection({ profile, field, number, onChange }: { profile: Profile; field: string; number: string; onChange: (path: Path, value: unknown) => void }) {
  return <section className="resume-edit-section" id={`edit-${field}`}><SectionTitle number={number} title={label(field)} /><StringListEditor title={label(field)} values={editableListValues(profile[field])} path={[field]} onChange={onChange} /></section>;
}

function ObjectCollection({ profile, collection, number, title, fields, lists = [], onChange, onRewrite, addResearch = false }: { profile: Profile; collection: string; number: string; title: string; fields: FieldSpec[]; lists?: Array<{ key: string; title: string; multiline?: boolean }>; onChange: (path: Path, value: unknown) => void; onRewrite: (path: Path, style: "concise" | "brief" | "elaborate") => Promise<string>; addResearch?: boolean }) {
  const items = objectList(profile[collection]);
  const defaults: Record<string, Record<string, unknown>> = {
    experience: {}, education: {}, projects: { name: "" }, publications: { title: "" },
    volunteer_experience: {}, additional_sections: { title: "", details: [""] },
  };
  return <section className="resume-edit-section" id={`edit-${collection}`}><SectionTitle number={number} title={title} />{items.map((item, index) => {
    const known = new Set([...fields.map((field) => field.key), ...lists.map((list) => list.key)]);
    const extras = Object.entries(item).filter(([key, value]) => !known.has(key) && key !== "model_config" && !isMissingFieldName(key) && !isMissingValue(value));
    return <article className="resume-entry-editor" key={index}><header><div className="resume-entry-grip">⠿</div><strong>{title} {String(index + 1).padStart(2, "0")}</strong><button type="button" aria-label={`Remove ${title} ${index + 1}`} onClick={() => onChange([collection], items.filter((_, current) => current !== index))}><Trash2 size={15} /></button></header><div className="resume-edit-grid">{fields.map((field) => <Field key={field.key} profile={profile} path={[collection, index, field.key]} title={field.title || label(field.key)} multiline={field.multiline} number={field.number} onChange={onChange} onRewrite={onRewrite} />)}{lists.map((list) => <div className="resume-edit-field full-width" key={list.key}><StringListEditor title={list.title} values={editableListValues(item[list.key])} path={[collection, index, list.key]} onChange={onChange} /></div>)}{extras.map(([key, value]) => <Field key={key} profile={profile} path={[collection, index, key]} title={label(key)} multiline={typeof value === "string" && value.length > 100} onChange={onChange} onRewrite={onRewrite} />)}</div></article>;
  })}<div className="resume-collection-actions">{addResearch && <button className="resume-add-button research-add-button" type="button" onClick={() => onChange([collection], [...items, { title: "Research", details: [""] }])}><Plus size={16} /> Add research</button>}<button className="resume-add-button collection-add" type="button" onClick={() => onChange([collection], [...items, structuredClone(defaults[collection] || {})])}><Plus size={16} /> {addResearch ? "Add custom field" : `Add ${title.toLowerCase().replace(/s$/, "")}`}</button></div></section>;
}

function PreviewSection({ title, children }: { title: string; children: ReactNode }) {
  return <section className="resume-preview-section"><h3>{title}</h3>{children}</section>;
}

function ExtraPreviewRows({ item, known }: { item: RecordItem; known: string[] }) {
  const omitted = new Set([...known, "model_config"]);
  const extras = Object.entries(item).filter(([key, value]) => !omitted.has(key) && !isMissingFieldName(key) && !isMissingValue(value));
  return <>{extras.map(([key, value]) => <p key={key}><b>{label(key)}:</b> {valueText(value)}</p>)}</>;
}

export function ResumePreview({ profile }: { profile: Profile }) {
  const experiences = objectList(profile.experience);
  const education = objectList(profile.education);
  const projects = objectList(profile.projects);
  const publications = objectList(profile.publications);
  const volunteer = objectList(profile.volunteer_experience);
  const additional = objectList(profile.additional_sections);
  const text = (value: unknown) => valueText(value);
  const dateRange = (item: RecordItem) => [text(item.start_date), text(item.end_date)].filter(Boolean).join(" – ");
  const bulletList = (values: unknown) => stringList(values).map((entry, index) => <li key={index}>{entry}</li>);
  const contact = [text(profile.email), text(profile.phone), text(profile.location), ...stringList(profile.websites)].filter(Boolean);
  return <article className="resume-paper" aria-label="Resume live preview"><header className="resume-paper-header"><h1>{text(profile.full_name) || "Your name"}</h1>{text(profile.professional_title) && <p className="resume-paper-title">{text(profile.professional_title)}</p>}<p className="resume-paper-contact">{contact.map((item, index) => <span key={index}>{item}</span>)}</p></header>
    {text(profile.professional_summary) && <PreviewSection title="Profile"><p>{text(profile.professional_summary)}</p></PreviewSection>}
    {experiences.length > 0 && <PreviewSection title="Experience">{experiences.map((item, index) => <div className="resume-preview-entry" key={index}><div className="resume-preview-entry-heading"><strong>{[text(item.job_title || item.title), text(item.company)].filter(Boolean).join(" · ") || "Role"}</strong><time>{dateRange(item)}</time></div>{[text(item.location), text(item.employment_type)].filter(Boolean).length > 0 && <small>{[text(item.location), text(item.employment_type)].filter(Boolean).join(" · ")}</small>}{text(item.description) && <p>{text(item.description)}</p>}{[...stringList(item.responsibilities), ...stringList(item.achievements)].length > 0 && <ul>{bulletList([...stringList(item.responsibilities), ...stringList(item.achievements)])}</ul>}{stringList(item.technologies).length > 0 && <p><b>Technologies:</b> {stringList(item.technologies).join(", ")}</p>}<ExtraPreviewRows item={item} known={["job_title", "title", "company", "location", "employment_type", "start_date", "end_date", "description", "responsibilities", "achievements", "technologies"]} /></div>)}</PreviewSection>}
    {education.length > 0 && <PreviewSection title="Education">{education.map((item, index) => <div className="resume-preview-entry" key={index}><div className="resume-preview-entry-heading"><strong>{[text(item.degree), text(item.field_of_study)].filter(Boolean).join(", ") || "Education"}</strong><time>{dateRange(item) || text(item.graduation_year)}</time></div><p>{[text(item.institution), text(item.location), text(item.cgpa_or_percentage)].filter(Boolean).join(" · ")}</p>{stringList(item.coursework).length > 0 && <p><b>Coursework:</b> {stringList(item.coursework).join(", ")}</p>}{stringList(item.honors).length > 0 && <p><b>Honors:</b> {stringList(item.honors).join(", ")}</p>}<ExtraPreviewRows item={item} known={["degree", "field_of_study", "institution", "location", "start_date", "end_date", "graduation_year", "cgpa_or_percentage", "coursework", "honors"]} /></div>)}</PreviewSection>}
    {stringList(profile.skills).length > 0 && <PreviewSection title="Skills"><p>{stringList(profile.skills).join(" · ")}</p></PreviewSection>}
    {projects.length > 0 && <PreviewSection title="Projects">{projects.map((item, index) => <div className="resume-preview-entry" key={index}><div className="resume-preview-entry-heading"><strong>{text(item.name) || "Project"}</strong><time>{dateRange(item)}</time></div>{text(item.role) && <small>{text(item.role)}</small>}{text(item.description) && <p>{text(item.description)}</p>}{[...stringList(item.responsibilities), ...stringList(item.outcomes)].length > 0 && <ul>{bulletList([...stringList(item.responsibilities), ...stringList(item.outcomes)])}</ul>}{stringList(item.technologies).length > 0 && <p><b>Technologies:</b> {stringList(item.technologies).join(", ")}</p>}{text(item.url) && <p>{text(item.url)}</p>}<ExtraPreviewRows item={item} known={["name", "role", "start_date", "end_date", "description", "responsibilities", "outcomes", "technologies", "url"]} /></div>)}</PreviewSection>}
    {stringList(profile.certifications).length > 0 && <PreviewSection title="Certifications"><ul>{bulletList(profile.certifications)}</ul></PreviewSection>}
    {stringList(profile.awards).length > 0 && <PreviewSection title="Awards"><ul>{bulletList(profile.awards)}</ul></PreviewSection>}
    {stringList(profile.languages).length > 0 && <PreviewSection title="Languages"><p>{stringList(profile.languages).join(" · ")}</p></PreviewSection>}
    {publications.length > 0 && <PreviewSection title="Research & Publications">{publications.map((item, index) => <div className="resume-preview-entry" key={index}><strong>{text(item.title)}</strong><p>{[text(item.publisher), text(item.publication_date), text(item.url)].filter(Boolean).join(" · ")}</p>{text(item.description) && <p>{text(item.description)}</p>}<ExtraPreviewRows item={item} known={["title", "publisher", "publication_date", "url", "description"]} /></div>)}</PreviewSection>}
    {volunteer.length > 0 && <PreviewSection title="Volunteer Experience">{volunteer.map((item, index) => <div className="resume-preview-entry" key={index}><strong>{[text(item.job_title), text(item.company)].filter(Boolean).join(" · ")}</strong><p>{[dateRange(item), text(item.location)].filter(Boolean).join(" · ")}</p>{text(item.description) && <p>{text(item.description)}</p>}{[...stringList(item.responsibilities), ...stringList(item.achievements)].length > 0 && <ul>{bulletList([...stringList(item.responsibilities), ...stringList(item.achievements)])}</ul>}{stringList(item.technologies).length > 0 && <p><b>Skills / tools:</b> {stringList(item.technologies).join(", ")}</p>}<ExtraPreviewRows item={item} known={["job_title", "company", "location", "employment_type", "start_date", "end_date", "description", "responsibilities", "achievements", "technologies"]} /></div>)}</PreviewSection>}
    {stringList(profile.interests).length > 0 && <PreviewSection title="Interests"><p>{stringList(profile.interests).join(" · ")}</p></PreviewSection>}
    {stringList(profile.references).length > 0 && <PreviewSection title="References"><ul>{bulletList(profile.references)}</ul></PreviewSection>}
    {additional.map((item, index) => <PreviewSection title={text(item.title) || `Additional section ${index + 1}`} key={index}>{stringList(item.details).length > 0 && <ul>{bulletList(item.details)}</ul>}<ExtraPreviewRows item={item} known={["title", "details"]} /></PreviewSection>)}
  </article>;
}
