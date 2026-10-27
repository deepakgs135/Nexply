import { useCallback, useState } from "react";
import { api } from "../shared/api";
import { EMPTY_PREFERENCES, type Preferences } from "./profile-preferences-model";

export function useJobPreferences() {
  const [preferences, setPreferences] = useState<Preferences>(EMPTY_PREFERENCES);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [tableReady, setTableReady] = useState(false);

  const load = useCallback(async () => {
    try {
      const result = await api<{ job_preferences: Partial<Preferences>; configured: boolean }>("/resumes/preferences");
      const stored = result.job_preferences || {};
      const text = (value: unknown) => typeof value === "string" ? value : "";
      setTableReady(result.configured);
      setMessage(result.configured ? "" : "Run the preferences SQL file to enable saving.");
      setPreferences({
        ...EMPTY_PREFERENCES, current_ctc: text(stored.current_ctc), expected_ctc: text(stored.expected_ctc),
        expected_ctc_range: text(stored.expected_ctc_range), minimum_expected_ctc: text(stored.minimum_expected_ctc),
        currency: text(stored.currency) || "INR", work_mode: text(stored.work_mode),
        notice_period: text(stored.notice_period), availability: text(stored.availability),
        willing_to_relocate: typeof stored.willing_to_relocate === "boolean" ? stored.willing_to_relocate : null,
        preferred_locations: Array.isArray(stored.preferred_locations) ? stored.preferred_locations : [],
        preferred_job_titles: Array.isArray(stored.preferred_job_titles) ? stored.preferred_job_titles : [],
        employment_types: Array.isArray(stored.employment_types) ? stored.employment_types : [],
        preferred_industries: Array.isArray(stored.preferred_industries) ? stored.preferred_industries : [],
      });
    } catch {
      setTableReady(false); setMessage("Could not load preferences from PostgreSQL.");
    }
  }, []);

  function setPreference<K extends keyof Preferences>(key: K, value: Preferences[K]) {
    setPreferences((current) => ({ ...current, [key]: value }));
    setMessage("");
  }

  async function persist() {
    await api("/resumes/preferences", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_preferences: preferences }) });
  }

  async function save() {
    if (!tableReady || saving) return;
    setSaving(true); setMessage("");
    try { await persist(); setMessage("Preferences saved"); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Could not save preferences."); }
    finally { setSaving(false); }
  }

  return { preferences, saving, message, tableReady, load, persist, save, setPreference };
}
