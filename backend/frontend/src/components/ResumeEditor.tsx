import { useEffect, useRef, useState, type ReactNode } from "react";
import { ArrowDownToLine, Check, Plus, Save, X } from "lucide-react";
import { api } from "../shared/api";
import { label, type Profile } from "../shared/resumeFormat";
import { Field, ObjectCollection, SectionTitle, StringListEditor, StringSection, editableListValues, type Path } from "./ResumeEditorFields";
import { ResumePreview } from "./ResumePreview";
import { addContent, exportResume } from "./resumeEditorActions";
export { ResumePreview } from "./ResumePreview";

export default function ResumeEditor({
  profile, filename, documentId, saving, error, onChange, onSave, onCancel, mode = "edit", embedded = false, extraActions,
}: {
  profile: Profile; filename?: string; documentId: string; saving: boolean; error: string; extraActions?: ReactNode;
  onChange: (path: Path, value: unknown) => void; onSave: () => void; onCancel: () => void; mode?: "edit" | "create"; embedded?: boolean;
}) {
  const additionalSectionsRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  useEffect(() => {
    if (embedded) return;
    document.body.classList.add("resume-editor-open");
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape" && !saving) onCancel(); };
    window.addEventListener("keydown", onKey);
    return () => { window.removeEventListener("keydown", onKey); document.body.classList.remove("resume-editor-open"); };
  }, [saving, onCancel, embedded]);

  async function rewriteWithRex(path: Path, style: "concise" | "brief" | "detail") {
    if (!documentId) throw new Error("Save this resume before asking REX to rewrite a field.");
    const result = await api<{ rewritten_text: string }>(`/resumes/${encodeURIComponent(documentId)}/rex/rewrite`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ field_path: path, style }),
    });
    return result.rewritten_text;
  }

  return <div className={embedded ? "resume-editor-embedded" : "resume-editor-overlay"}>
    {embedded ? <header className="profile-fields-toolbar"><div><span className="section-eyebrow">PROFILE DETAILS</span><strong>Build your resume block by block</strong><small>All fields are editable. Save to update your latest profile.</small></div><div className="resume-editor-actions">{extraActions}<button className="resume-editor-button secondary" type="button" onClick={onCancel} disabled={saving || exporting}><X size={15} /> Discard</button><button className="resume-editor-button secondary" type="button" onClick={() => void exportResume(profile, exporting, setExporting, setExportError)} disabled={exporting}>{exporting ? "Exporting…" : <><ArrowDownToLine size={15} /> Export DOCX</>}</button><button className="resume-editor-button primary" type="button" onClick={onSave} disabled={saving || exporting}>{saving ? "Saving…" : <><Save size={15} /> Save profile</>}</button></div></header> : <header className="resume-editor-header"><div className="resume-editor-brand"><span className="resume-editor-mark">N</span><div><span className="section-eyebrow">NEXPLY RESUME STUDIO</span><strong>{mode === "create" ? "Create your resume" : "Edit your resume"}</strong><small title={filename}>{filename || (mode === "create" ? "New resume draft" : "Structured candidate profile")}</small></div></div><div className="resume-editor-actions"><span className="resume-editor-saved"><Check size={14} /> {mode === "create" ? "Draft saves when you finish" : "Changes save to this resume"}</span><button className="resume-editor-button secondary" type="button" onClick={onCancel} disabled={saving || exporting}><X size={15} /> Cancel</button><button className="resume-editor-button secondary" type="button" onClick={() => void exportResume(profile, exporting, setExporting, setExportError)} disabled={exporting}><ArrowDownToLine size={15} /> {exporting ? "Exporting…" : "Export DOCX"}</button><button className="resume-editor-button primary" type="button" onClick={onSave} disabled={saving || exporting}>{saving ? "Saving…" : <><Save size={15} /> {mode === "create" ? "Save resume" : "Save changes"}</>}</button></div></header>}
    <main className={`resume-editor-main ${embedded ? "profile-fields-main" : ""}`}>
      <div className="resume-editor-left">
        <div className="resume-editor-content">
        {!embedded && <div className="resume-editor-intro"><span className="section-eyebrow">MAKE IT YOURS</span><h1>{mode === "create" ? "Build your resume" : "Edit your resume"}</h1><p>Open a section, edit its entries, and review the live resume preview as you work.</p></div>}
        <nav className="resume-editor-nav" aria-label="Resume sections">{["profile", "experience", "education", "skills", "projects", "certifications", "publications", "volunteer_experience"].map((key) => <a href={`#edit-${key}`} key={key} onClick={(event) => { event.preventDefault(); const section = document.getElementById(`edit-${key}`) as HTMLDetailsElement | null; if (section) { section.open = true; section.scrollIntoView({ behavior: "smooth", block: "start" }); } }}>{label(key)}</a>)}</nav>
        {error && <div className="ai-error resume-editor-error" role="alert">{error}</div>}
        {exportError && <div className="ai-error resume-editor-error" role="alert">{exportError}</div>}
        <details className="resume-edit-section flow-section" id="edit-profile" open><summary><SectionTitle number="01" title="Profile" /></summary><div className="resume-edit-grid">
          <Field profile={profile} path={["full_name"]} title="Full name" onChange={onChange} onRewrite={rewriteWithRex} />
          <Field profile={profile} path={["professional_title"]} title="Professional headline" onChange={onChange} onRewrite={rewriteWithRex} />
          <Field profile={profile} path={["email"]} title="Email" onChange={onChange} onRewrite={rewriteWithRex} />
          <Field profile={profile} path={["phone"]} title="Phone" onChange={onChange} onRewrite={rewriteWithRex} />
          <Field profile={profile} path={["location"]} title="Location" onChange={onChange} onRewrite={rewriteWithRex} />
          <div className="resume-edit-field full-width"><StringListEditor title="Links and websites" values={editableListValues(profile.websites)} path={["websites"]} onChange={onChange} placeholder="https://…" /></div>
          <Field profile={profile} path={["professional_summary"]} title="Professional summary" multiline onChange={onChange} onRewrite={rewriteWithRex} />
        </div></details>
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
        <ObjectCollection profile={profile} collection="additional_sections" number="13" title="Additional section" fields={[{ key: "title", title: "Section title" }]} lists={[{ key: "details", title: "Details", multiline: true }]} onChange={onChange} onRewrite={rewriteWithRex} sectionRef={additionalSectionsRef} hideSectionHeader hideCollectionActions />
        <button className="resume-add-content" type="button" onClick={() => addContent(profile, onChange, additionalSectionsRef.current)}><Plus size={22} /> Add Section</button>
        <button className="resume-editor-done-button" type="button" onClick={onSave} disabled={saving}>{saving ? "Saving…" : <><Check size={17} /> Done</>}</button>
        </div>
      </div>
      {!embedded && <aside className="resume-editor-right"><div className="resume-preview-heading"><div><span className="section-eyebrow">YOUR STORY AT A GLANCE</span><h2>Live preview</h2></div><span>Updates as you type</span></div><div className="resume-paper-wrap"><ResumePreview profile={profile} /></div></aside>}
    </main>
  </div>;
}

