import type { ReactNode } from "react";
import { MapPin } from "lucide-react";
import { humanDate, isMissingFieldName, isMissingValue, label, stringList, valueText, type RecordItem } from "./resumeFormat";

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

