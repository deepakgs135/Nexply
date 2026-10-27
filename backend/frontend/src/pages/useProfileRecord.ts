import { useCallback, useEffect, useState } from "react";
import { api } from "../shared/api";
import type { Profile } from "../shared/resumeFormat";
import type { LatestResponse, ResumePhase } from "./profileWorkspaceTypes";

export function useProfileRecord(loadPreferences: () => Promise<void>) {
  const [documentId, setDocumentId] = useState("");
  const [filename, setFilename] = useState("");
  const [sourceProfile, setSourceProfile] = useState<Profile | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [phase, setPhase] = useState<ResumePhase>("idle");
  const [phaseLabel, setPhaseLabel] = useState("");
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);

  const loadLatest = useCallback(async () => {
    try {
      const result = await api<LatestResponse>("/resumes/latest");
      const latest = result.resume;
      setDocumentId(latest?.document_id || "");
      setFilename(latest?.original_filename || "");
      setProfile(latest?.structured_result || null);
      setSourceProfile(latest?.structured_result || null);
      await loadPreferences();
      setPhase("idle"); setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load your latest profile.");
    } finally { setLoaded(true); }
  }, [loadPreferences]);

  useEffect(() => { void loadLatest(); }, [loadLatest]);
  return { documentId, setDocumentId, filename, setFilename, sourceProfile, setSourceProfile, profile, setProfile, phase, setPhase, phaseLabel, setPhaseLabel, error, setError, loaded, loadLatest };
}
