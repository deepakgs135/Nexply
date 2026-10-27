import { useState, type Ref } from "react";
import { LoaderCircle, Plus, Sparkles, Trash2 } from "lucide-react";
import { isMissingFieldName, isMissingValue, label, objectList, valueText, type Profile } from "../shared/resumeFormat";
import RichTextEditor from "./RichTextEditor";

export type Path = (string | number)[];
export type FieldSpec = { key: string; title?: string; multiline?: boolean; number?: boolean };

export function SectionTitle({ number, title, count }: { number: string; title: string; count?: number }) {
  return <div className="resume-edit-title"><span>{number}</span><h2>{title}</h2>{count !== undefined && <small className="flow-section-count">{count}</small>}<i /></div>;
}

function readPath(profile: Profile, path: Path): unknown {
  let value: unknown = profile;
  for (const part of path) value = value && typeof value === "object" ? (value as Record<string | number, unknown>)[part] : undefined;
  return value;
}

export function Field({ profile, path, title, multiline = false, number = false, onChange, onRewrite }: { profile: Profile; path: Path; title: string; multiline?: boolean; number?: boolean; onChange: (path: Path, value: unknown) => void; onRewrite: (path: Path, style: "concise" | "brief" | "detail") => Promise<string> }) {
  const [rewriting, setRewriting] = useState(false);
  const [rewriteError, setRewriteError] = useState("");
  const [showRexOptions, setShowRexOptions] = useState(false);
  const value = readPath(profile, path);
  const text = isMissingValue(value) ? "" : String(value);
  const canRewrite = multiline && (path[0] === "professional_summary" || path[path.length - 1] === "description");
  async function runRex(style: "concise" | "brief" | "detail") {
    setRewriting(true); setRewriteError("");
    setShowRexOptions(false);
    try { onChange(path, await onRewrite(path, style)); }
    catch (error) { setRewriteError(error instanceof Error ? error.message : "REX could not rewrite this field."); }
    finally { setRewriting(false); }
  }
  const fieldKey = String(path[path.length - 1]);
  return <div className={`resume-edit-field field-${fieldKey} ${multiline ? "full-width" : ""}`}><div className="resume-edit-field-heading"><span>{title}</span>{canRewrite && <button className="rex-field-button" type="button" onClick={() => setShowRexOptions((open) => !open)} disabled={rewriting} title="Rewrite or draft this field with REX">{rewriting ? <LoaderCircle size={13} className="spin" /> : <Sparkles size={13} />} {rewriting ? "REX is writing…" : "REX"}</button>}</div>{showRexOptions && <div className="rex-style-options" aria-label="Choose REX writing style"><span>{text.trim() ? "Rewrite style" : "Draft style"}</span>{(["concise", "brief", "detail"] as const).map((style) => <button type="button" key={style} onClick={() => void runRex(style)}>{style[0].toUpperCase() + style.slice(1)}</button>)}</div>}{multiline ? <RichTextEditor value={text} onChange={(next) => onChange(path, next)} placeholder={`Add ${title.toLowerCase()}…`} label={title} /> : <input type={number ? "number" : "text"} value={text} onChange={(event) => onChange(path, number ? (event.target.value ? Number(event.target.value) : null) : event.target.value)} />}{rewriteError && <small className="rex-field-error" role="alert">{rewriteError}</small>}</div>;
}

export function editableListValues(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

export function StringListEditor({ title, values, path, onChange, placeholder = "Add a detail", multiline = false }: { title: string; values: unknown[]; path: Path; onChange: (path: Path, value: unknown) => void; placeholder?: string; multiline?: boolean }) {
  const visible = values.map((value, index) => ({ value, index })).filter(({ value }) => value === "" || !isMissingValue(value));
  return <div className="resume-list-editor"><span className="resume-list-title">{title}</span>{visible.map(({ value, index }) => <div className={`resume-list-row ${multiline ? "rich-list-row" : ""}`} key={index}>{multiline ? <RichTextEditor label={`${title} ${index + 1}`} value={isMissingValue(value) ? "" : String(value)} placeholder={placeholder} onChange={(next) => onChange([...path, index], next)} /> : <input aria-label={`${title} ${index + 1}`} value={isMissingValue(value) ? "" : String(value)} placeholder={placeholder} onChange={(event) => onChange([...path, index], event.target.value)} />}<button type="button" title="Remove item" aria-label={`Remove ${title} ${index + 1}`} onClick={() => onChange(path, values.filter((_, current) => current !== index))}><Trash2 size={14} /></button></div>)}<button className="resume-add-button" type="button" onClick={() => onChange(path, [...values, ""])}><Plus size={15} /> Add {title.toLowerCase().replace(/s$/, "")}</button></div>;
}

export function StringSection({ profile, field, number, onChange }: { profile: Profile; field: string; number: string; onChange: (path: Path, value: unknown) => void }) {
  const values = editableListValues(profile[field]);
  return <details className="resume-edit-section flow-section" id={`edit-${field}`}><summary><SectionTitle number={number} title={label(field)} count={values.filter((item) => !isMissingValue(item)).length} /></summary><StringListEditor title={label(field)} values={values} path={[field]} onChange={onChange} /></details>;
}

export function ObjectCollection({ profile, collection, number, title, fields, lists = [], onChange, onRewrite, sectionRef, hideSectionHeader = false, hideCollectionActions = false }: { profile: Profile; collection: string; number: string; title: string; fields: FieldSpec[]; lists?: Array<{ key: string; title: string; multiline?: boolean }>; onChange: (path: Path, value: unknown) => void; onRewrite: (path: Path, style: "concise" | "brief" | "detail") => Promise<string>; sectionRef?: Ref<HTMLDivElement>; hideSectionHeader?: boolean; hideCollectionActions?: boolean }) {
  const items = objectList(profile[collection]);
  const defaults: Record<string, Record<string, unknown>> = {
    experience: {}, education: {}, projects: { name: "" }, publications: { title: "" },
    volunteer_experience: {}, additional_sections: { title: "Custom section", details: [""] },
  };
  const entries = items.map((item, index) => {
    const known = new Set([...fields.map((field) => field.key), ...lists.map((list) => list.key)]);
    const legacyAliases = new Set(["start_date_string", "end_date_string", "location_string", "location_text", "honors_or_awards"]);
    const extras = Object.entries(item).filter(([key, value]) => !known.has(key) && !legacyAliases.has(key) && key !== "model_config" && !isMissingFieldName(key) && !isMissingValue(value));
    const entryTitle = collection === "additional_sections" ? valueText(item.title) || "Custom section" : valueText(item.job_title || item.degree || item.name || item.title || item.full_name) || `${title} entry`;
    const entrySubtitle = valueText(item.company || item.institution || item.publisher || item.role);
    return <details className={`resume-entry-editor flow-entry flow-entry-${collection}`} key={index}><summary><span className="resume-entry-grip">⠿</span><span className="flow-entry-title"><strong>{entryTitle}</strong><span className="flow-entry-edit-label">Edit Entry</span>{entrySubtitle && <small>{entrySubtitle}</small>}</span><button type="button" className="flow-entry-delete" aria-label={`Remove ${title} ${index + 1}`} onClick={(event) => { event.preventDefault(); event.stopPropagation(); onChange([collection], items.filter((_, current) => current !== index)); }}><Trash2 size={15} /></button></summary><div className="resume-edit-grid">{fields.map((field) => <Field key={field.key} profile={profile} path={[collection, index, field.key]} title={field.title || label(field.key)} multiline={field.multiline} number={field.number} onChange={onChange} onRewrite={onRewrite} />)}{lists.map((list) => <div className="resume-edit-field full-width" key={list.key}><StringListEditor title={list.title} multiline={list.multiline} values={editableListValues(item[list.key])} path={[collection, index, list.key]} onChange={onChange} /></div>)}{extras.map(([key, value]) => <Field key={key} profile={profile} path={[collection, index, key]} title={label(key)} multiline={typeof value === "string" && value.length > 100} onChange={onChange} onRewrite={onRewrite} />)}</div></details>;
  });
  const collectionActions = !hideCollectionActions && <div className="resume-collection-actions"><button className="resume-add-button collection-add" type="button" onClick={() => onChange([collection], [...items, structuredClone(defaults[collection] || {})])}><Plus size={16} /> Add entry</button></div>;
  if (hideSectionHeader) return <div ref={sectionRef} className="custom-content-sections" id={`edit-${collection}`}>{entries}</div>;
  return <details className="resume-edit-section flow-section" id={`edit-${collection}`}><summary><SectionTitle number={number} title={title} count={items.length} /></summary>{entries}{collectionActions}</details>;
}

