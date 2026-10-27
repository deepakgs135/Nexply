import { downloadBlob } from "../shared/api";
import { objectList, valueText, type Profile } from "../shared/resumeFormat";
import type { Path } from "./ResumeEditorFields";

export function addContent(
  profile: Profile,
  onChange: (path: Path, value: unknown) => void,
  section: HTMLDivElement | null,
) {
  onChange(["additional_sections"], [...objectList(profile.additional_sections), { title: "New section", details: [""] }]);
  window.requestAnimationFrame(() => {
    const entry = section?.querySelectorAll<HTMLDetailsElement>(".flow-entry");
    const last = entry?.[entry.length - 1];
    if (!last) return;
    last.open = true;
    last.scrollIntoView({ behavior: "smooth", block: "center" });
    last.querySelector<HTMLInputElement>("input")?.focus();
  });
}

export async function exportResume(
  profile: Profile,
  exporting: boolean,
  setExporting: (value: boolean) => void,
  setExportError: (value: string) => void,
) {
  if (exporting) return;
  setExporting(true);
  setExportError("");
  try {
    const blob = await downloadBlob("/resumes/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ structured_result: profile }),
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${valueText(profile.full_name).replace(/[^A-Za-z0-9_-]+/g, "-") || "candidate"}-resume.docx`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (caught) {
    setExportError(caught instanceof Error ? caught.message : "Could not export the resume.");
  } finally {
    setExporting(false);
  }
}
