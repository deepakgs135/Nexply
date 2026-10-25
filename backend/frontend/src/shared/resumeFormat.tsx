import type { ReactNode } from "react";
import { MapPin } from "lucide-react";

export type Profile = Record<string, unknown>;
export type RecordItem = Record<string, unknown>;

const MISSING_TEXT = new Set(["null", "none", "undefined", "n/a", "na", "not available", "not provided", "not specified", "-"]);

export function isMissingValue(value: unknown): boolean {
  if (value === null || value === undefined || value === "") return true;
  if (typeof value === "string") return MISSING_TEXT.has(value.trim().toLowerCase());
  if (Array.isArray(value)) return value.every(isMissingValue);
  if (typeof value === "object") return Object.values(value as RecordItem).every(isMissingValue);
  return false;
}

export function isMissingFieldName(key: string) {
  return /(?:^|[_\s-])(null|none|undefined|n\/a|na)$/i.test(key.trim());
}

export function label(value: string) {
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
export function valueText(value: unknown): string {
  if (isMissingValue(value)) return "";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.map(valueText).filter(Boolean).join(" · ");
  if (typeof value === "object") return Object.entries(value as RecordItem)
    .filter(([key, item]) => key !== "model_config" && !isMissingFieldName(key) && !isMissingValue(item))
    .map(([key, item]) => `${label(key)}: ${valueText(item)}`).join(" · ");
  return "";
}
export function objectList(value: unknown): RecordItem[] {
  return Array.isArray(value) ? value.filter((item): item is RecordItem => Boolean(item) && typeof item === "object" && !Array.isArray(item)) : [];
}
export function stringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map(valueText).filter(Boolean);
}
export function humanDate(item: RecordItem) {
  return [valueText(item.start_date), valueText(item.end_date)].filter(Boolean).join(" – ");
}
export function allRows(profile: Profile) {
  const rows: Array<{ section: string; field: string; value: string }> = [];
  const visit = (section: string, field: string, value: unknown) => {
    if (isMissingFieldName(field) || isMissingValue(value)) return;
    if (Array.isArray(value)) value.forEach((child, index) => visit(section, `${field} ${index + 1}`, child));
    else if (typeof value === "object") Object.entries(value as RecordItem).forEach(([key, child]) => visit(section, `${field} · ${label(key)}`, child));
    else rows.push({ section, field, value: valueText(value) });
  };
  Object.entries(profile).filter(([key]) => !["parsed_text", "raw_text", "document_id", "_id", "model_config"].includes(key))
    .forEach(([key, value]) => visit(label(key), label(key), value));
  return rows;
}
export function formatSize(bytes: number) {
  return bytes < 1048576 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1048576).toFixed(1)} MB`;
}
export function safeUrl(text: string) {
  const match = text.match(/https?:\/\/[^\s]+|www\.[^\s]+/i);
  if (!match) return null;
  const href = match[0].startsWith("www.") ? `https://${match[0]}` : match[0];
  try { const url = new URL(href); return ["http:", "https:"].includes(url.protocol) ? url.href : null; } catch { return null; }
}

export function ItemMeta({ item }: { item: RecordItem }) {
  const parts = [valueText(item.company || item.institution || item.publisher || item.organization), humanDate(item), valueText(item.location)];
  return <div className="entry-meta">{parts.filter(Boolean).map((part, index) => <span key={`${part}-${index}`}>{index === 2 && <MapPin size={12} />}{part}</span>)}</div>;
}
export function DetailLines({ item, exclude = [] }: { item: RecordItem; exclude?: string[] }) {
  const excluded = new Set(["company", "company_name", "institution", "publisher", "organization", "name", "title", "role", "job_title", "degree", "start_date", "end_date", "location", "employment_type", ...exclude]);
  const entries = Object.entries(item).filter(([key, value]) => !excluded.has(key) && !isMissingFieldName(key) && !isMissingValue(value));
  const bulletEntries = entries.filter(([key, value]) => ["responsibilities", "achievements", "outcomes", "details", "coursework", "honors"].includes(key) && Array.isArray(value));
  const remaining = entries.filter(([key]) => !bulletEntries.some(([bulletKey]) => bulletKey === key));
  return <>
    {remaining.map(([key, value]) => <div className="detail-line" key={key}><span>{label(key)}</span><strong>{valueText(value)}</strong></div>)}
    {bulletEntries.map(([key, value]) => <div className="bullet-group" key={key}><strong>{label(key)}</strong><ul>{stringList(value).map((text, index) => <li key={`${key}-${index}`}>{text}</li>)}</ul></div>)}
  </>;
}

export function SectionHeading({ title, count, icon }: { title: string; count?: number; icon?: ReactNode }) {
  return <div className="profile-section-heading">{icon && <span className="section-heading-icon">{icon}</span>}<h3>{title}</h3>{count !== undefined && <span className="section-count">{count}</span>}</div>;
}

