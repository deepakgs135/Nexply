import { useState } from "react";
import { api } from "../shared/api";
import type { Profile } from "../shared/resumeFormat";

type Props = {
  profile: Profile | null; documentId: string; preferencesReady: boolean;
  setProfile: (value: Profile | null | ((current: Profile | null) => Profile)) => void;
  setSourceProfile: (value: Profile | null) => void; setDocumentId: (value: string) => void; setFilename: (value: string) => void;
  persistPreferences: () => Promise<void>;
};

export function useProfileEditor(props: Props) {
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  function updateProfile(path: (string | number)[], value: unknown) {
    props.setProfile((current) => {
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
    const profile = props.profile;
    if (!profile || saving) return;
    setSaving(true); setSaveError("");
    try {
      if (props.documentId) {
        const result = await api<{ structured_result: Profile }>(`/resumes/${encodeURIComponent(props.documentId)}/structured-result`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ structured_result: profile }) });
        props.setProfile(result.structured_result); props.setSourceProfile(result.structured_result);
      } else {
        const result = await api<{ document_id: string; structured_result: Profile }>("/resumes/manual-profile", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ structured_result: profile }) });
        props.setDocumentId(result.document_id); props.setFilename("Manually created resume");
        props.setProfile(result.structured_result); props.setSourceProfile(result.structured_result);
      }
      if (props.preferencesReady) await props.persistPreferences();
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Could not save your profile.");
    } finally { setSaving(false); }
  }
  return { saving, saveError, setSaveError, updateProfile, saveProfile };
}
