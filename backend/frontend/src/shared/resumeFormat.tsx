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
  return /\b(null|none|undefined|n\/a|not available|not provided)\b/i.test(key.trim());
}

export function removeMalformedFields(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(removeMalformedFields);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value as RecordItem)
      .filter(([key]) => !isMissingFieldName(key))
      .map(([key, child]) => [key, removeMalformedFields(child)]));
  }
  return value;
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
  if (typeof value === "string") {
    const text = value.replace(/<br\s*\/?\s*>/gi, "\n").replace(/<\/(?:p|div|li)>/gi, "\n").replace(/<[^>]*>/g, "").replace(/&nbsp;/gi, " ").replace(/&amp;/gi, "&").replace(/&lt;/gi, "<").replace(/&gt;/gi, ">").replace(/&quot;/gi, '"').replace(/&#39;/gi, "'");
    return text.trim();
  }
  if (typeof value === "number") return String(value);
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

