import { BriefcaseBusiness } from "lucide-react";
import { joined, type Preferences } from "./profile-preferences-model";

type Props = {
  preferences: Preferences; message: string; tableReady: boolean; saving: boolean;
  onChange: (key: keyof Preferences, value: Preferences[keyof Preferences]) => void;
  onSave: () => void;
};

export default function ProfilePreferences({ preferences, message, tableReady, saving, onChange, onSave }: Props) {
  const set = onChange;
  return <section className="profile-preferences-card card">
    <div className="profile-preferences-heading"><span className="heading-icon"><BriefcaseBusiness size={17} /></span><div><span className="section-eyebrow">JOB SEARCH</span><h2>Preferences</h2><p>Set compensation, location, and role preferences for your next opportunity.</p></div></div>
    <div className="preferences-grid">
      <label>Current CTC<div className="preference-input-with-unit"><input value={preferences.current_ctc} onChange={(e) => set("current_ctc", e.target.value)} placeholder="e.g. 8,00,000 per year" /><select value={preferences.currency} onChange={(e) => set("currency", e.target.value)} aria-label="Currency"><option>INR</option><option>USD</option><option>EUR</option><option>GBP</option></select></div></label>
      <label>Expected CTC<input value={preferences.expected_ctc} onChange={(e) => set("expected_ctc", e.target.value)} placeholder="e.g. 12,00,000 per year" /></label>
      <label>Expected CTC range<input value={preferences.expected_ctc_range} onChange={(e) => set("expected_ctc_range", e.target.value)} placeholder="e.g. 10–14 LPA" /></label>
      <label>Minimum expected CTC<input value={preferences.minimum_expected_ctc} onChange={(e) => set("minimum_expected_ctc", e.target.value)} placeholder="e.g. 10,00,000 per year" /></label>
      <label>Preferred locations<input value={joined(preferences.preferred_locations)} onChange={(e) => set("preferred_locations", e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} placeholder="City, region, or remote" /></label>
      <label>Preferred roles<input value={joined(preferences.preferred_job_titles)} onChange={(e) => set("preferred_job_titles", e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} placeholder="Role titles, separated by commas" /></label>
      <label>Work mode<select value={preferences.work_mode} onChange={(e) => set("work_mode", e.target.value)}><option value="">Choose work mode</option><option>On-site</option><option>Hybrid</option><option>Remote</option><option>Flexible</option></select></label>
      <label>Employment type<input value={joined(preferences.employment_types)} onChange={(e) => set("employment_types", e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} placeholder="Full-time, contract, etc." /></label>
      <label>Notice period<input value={preferences.notice_period} onChange={(e) => set("notice_period", e.target.value)} placeholder="e.g. 30 days" /></label>
      <label>Availability<input value={preferences.availability} onChange={(e) => set("availability", e.target.value)} placeholder="e.g. Immediate, from June 2026" /></label>
      <label>Preferred industries<input value={joined(preferences.preferred_industries)} onChange={(e) => set("preferred_industries", e.target.value.split(",").map((x) => x.trim()).filter(Boolean))} placeholder="Industries, separated by commas" /></label>
      <label>Open to relocation<select value={preferences.willing_to_relocate === null ? "" : String(preferences.willing_to_relocate)} onChange={(e) => set("willing_to_relocate", e.target.value === "" ? null : e.target.value === "true")}><option value="">Not specified</option><option value="true">Yes</option><option value="false">No</option></select></label>
    </div>
    <div className="preferences-footer"><span>{message || "Stored in PostgreSQL against your authenticated app_id"}</span><button type="button" className="primary-button" disabled={!tableReady || saving} onClick={onSave}>{saving ? "Saving…" : "Save preferences"}</button></div>
  </section>;
}

