import ProfilePreferences from "./ProfilePreferences";
import { ProfileFields, ProfileFooter, ProfileHeading } from "./ProfileWorkspacePanels";
import ResumeSourceCard from "./ResumeSourceCard";
import { useApiAvailability } from "./useApiAvailability";
import { useJobPreferences } from "./useJobPreferences";
import { useProfileEditor } from "./useProfileEditor";
import { useProfileRecord } from "./useProfileRecord";
import { useResumeExtraction } from "./useResumeExtraction";
import { useResumeFile } from "./useResumeFile";

export default function ProfilePage() {
  const availability = useApiAvailability();
  const preferences = useJobPreferences();
  const record = useProfileRecord(preferences.load);
  const editor = useProfileEditor({
    profile: record.profile,
    documentId: record.documentId,
    preferencesReady: preferences.tableReady,
    persistPreferences: preferences.persist,
    setProfile: record.setProfile,
    setSourceProfile: record.setSourceProfile,
    setDocumentId: record.setDocumentId,
    setFilename: record.setFilename,
  });
  const resumeFile = useResumeFile({
    maxSizeMb: availability.maxSizeMb,
    setDocumentId: record.setDocumentId,
    setFilename: record.setFilename,
    setProfile: record.setProfile,
    setSourceProfile: record.setSourceProfile,
    setPhase: record.setPhase,
    setPhaseLabel: record.setPhaseLabel,
    setError: record.setError,
    setSaveError: editor.setSaveError,
    loadLatest: record.loadLatest,
  });
  const extraction = useResumeExtraction({
    file: resumeFile.file,
    requestId: resumeFile.requestId,
    documentId: record.documentId,
    filename: record.filename,
    setDocumentId: record.setDocumentId,
    setFilename: record.setFilename,
    setSourceProfile: record.setSourceProfile,
    setProfile: record.setProfile,
    setPhase: record.setPhase,
    setPhaseLabel: record.setPhaseLabel,
    setError: record.setError,
  });
  return <main className="page-wrap profile-page">
    <ProfileHeading online={availability.online} />
    <section className="profile-workspace">
      <aside className="profile-source-column">
        <ResumeSourceCard
          file={resumeFile.file} documentId={record.documentId} filename={record.filename}
          sourceProfile={record.sourceProfile} fileUrl={resumeFile.fileUrl}
          textPreview={resumeFile.textPreview} apiOnline={availability.online}
          maxSizeMb={availability.maxSizeMb} busy={extraction.busy}
          phaseLabel={record.phaseLabel} phase={record.phase} error={record.error}
          dragging={resumeFile.dragging} inputRef={resumeFile.inputRef}
          onDragging={resumeFile.setDragging} onChooseFile={resumeFile.chooseFile}
          onAnalyze={() => void extraction.analyze()} onReset={() => void resumeFile.reset()}
        />
        <ProfilePreferences
          preferences={preferences.preferences} message={preferences.message}
          tableReady={preferences.tableReady} saving={preferences.saving}
          onChange={preferences.setPreference} onSave={() => void preferences.save()}
        />
      </aside>
      <ProfileFields record={record} editor={editor} resumeFile={resumeFile} />
    </section>
    <ProfileFooter online={availability.online} />
  </main>;
}
