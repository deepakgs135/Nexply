import { FileText, Upload, UserRound } from "lucide-react";
import ResumeEditor from "../components/ResumeEditor";
import RexResumeBuilder from "../components/RexResumeBuilder";
import type { useProfileRecord } from "./useProfileRecord";
import type { useProfileEditor } from "./useProfileEditor";
import type { useResumeFile } from "./useResumeFile";

type RecordState = ReturnType<typeof useProfileRecord>;
type EditorState = ReturnType<typeof useProfileEditor>;
type FileState = ReturnType<typeof useResumeFile>;

export function ProfileHeading({ online }: { online: boolean }) {
  return <section className="page-intro profile-page-intro">
    <div><div className="eyebrow"><span /> YOUR PRIVATE WORKSPACE</div><h1>Profile</h1>
      <p>Upload a resume or build your profile block by block. Your latest resume stays in this workspace.</p></div>
    <span className={`api-status ${online ? "online" : "offline"}`}><i />{online ? "API connected" : "API unavailable"}</span>
  </section>;
}

export function ProfileFields({ record, editor, resumeFile }: { record: RecordState; editor: EditorState; resumeFile: FileState }) {
  return <section className="profile-fields-column card">
    {record.profile ? <ResumeEditor embedded mode={record.documentId ? "edit" : "create"}
      profile={record.profile} filename={record.filename} documentId={record.documentId}
      saving={editor.saving} error={editor.saveError} onChange={editor.updateProfile}
      onSave={() => void editor.saveProfile()}
      onCancel={() => record.setProfile(record.sourceProfile ? structuredClone(record.sourceProfile) : null)}
      extraActions={<RexResumeBuilder profile={record.profile} documentId={record.documentId} />}
    /> : <ProfileStart record={record} resumeFile={resumeFile} />}
  </section>;
}

function ProfileStart({ record, resumeFile }: { record: RecordState; resumeFile: FileState }) {
  return <div className="profile-start-state">
    <span className="profile-start-icon"><UserRound size={24} /></span>
    <span className="section-eyebrow">CANDIDATE PROFILE</span>
    <h2>{record.loaded && !record.documentId ? "Start your profile" : "Your profile blocks appear here"}</h2>
    <p>{record.sourceProfile ? "Extracted details are loaded into editable profile blocks." : "Choose how you want to begin. Upload a resume or fill each profile section yourself."}</p>
    {!record.sourceProfile && <div className="profile-start-actions">
      <button className="primary-button" type="button" onClick={() => resumeFile.inputRef.current?.click()}><Upload size={15} /> Upload a resume</button>
      <button className="export-button" type="button" onClick={() => startManual(record, resumeFile)}><FileText size={15} /> Fill in manually</button>
    </div>}
  </div>;
}

function startManual(record: RecordState, resumeFile: FileState) {
  resumeFile.clear(); record.setDocumentId(""); record.setFilename("Manual profile");
  record.setSourceProfile(null); record.setProfile({}); record.setPhase("idle");
  record.setPhaseLabel(""); record.setError("");
}

export function ProfileFooter({ online }: { online: boolean }) {
  return <footer className="app-footer"><span>© 2026 NEXPLY AI</span>
    <span>One current resume. Complete, editable profile blocks.</span>
    <span className={online ? "footer-online" : "footer-offline"}><i />{online ? "All systems operational" : "API unavailable"}</span>
  </footer>;
}
