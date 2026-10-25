import { useState, type FormEvent } from "react";
import { LoaderCircle, MessageCircle, Save, Send, Sparkles, X } from "lucide-react";
import { api } from "../shared/api";
import type { Profile } from "../shared/resumeFormat";

type ChatMessage = { role: "assistant" | "user"; content: string };
type InterviewResult = { assistant_message: string; ready_to_save: boolean; structured_result: Profile };

export default function RexManualProfile({ onClose, onSaved }: { onClose: () => void; onSaved: (documentId: string, profile: Profile) => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([{ role: "assistant", content: "Hi, I’m REX. Let’s build your candidate profile together. Tell me your name and what you do currently; share details naturally, and I’ll ask focused follow-up questions." }]);
  const [profile, setProfile] = useState<Profile>({});
  const [input, setInput] = useState("");
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const answer = input.trim();
    if (!answer || busy) return;
    const nextMessages = [...messages, { role: "user" as const, content: answer }];
    setMessages(nextMessages); setInput(""); setBusy(true); setError("");
    try {
      const result = await api<InterviewResult>("/resumes/manual-profile/interview", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages, current_profile: profile }),
      });
      setProfile(result.structured_result);
      setReady(result.ready_to_save);
      setMessages([...nextMessages, { role: "assistant", content: result.assistant_message }]);
    } catch (caught) {
      setMessages(nextMessages);
      setInput(answer);
      setError(caught instanceof Error ? caught.message : "REX could not process that answer. Try again.");
    } finally { setBusy(false); }
  }

  async function saveProfile() {
    if (saving) return;
    setSaving(true); setError("");
    try {
      const result = await api<{ document_id: string; structured_result: Profile }>("/resumes/manual-profile", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ structured_result: profile }),
      });
      onSaved(result.document_id, result.structured_result);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not save this profile."); }
    finally { setSaving(false); }
  }

  return <div className="rex-interview-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy && !saving) onClose(); }}><section className="rex-interview" role="dialog" aria-modal="true" aria-labelledby="rex-interview-title">
    <header><span className="rex-interview-mark"><Sparkles size={18} /></span><div><small>REX · PROFILE BUILDER</small><h2 id="rex-interview-title">Create your profile with a conversation</h2><p>Share what you know. REX will ask one follow-up at a time and organize your facts.</p></div><button type="button" aria-label="Close conversation" onClick={onClose} disabled={busy || saving}><X size={18} /></button></header>
    <div className="rex-chat-messages" aria-live="polite">{messages.map((message, index) => <div className={`rex-chat-message ${message.role}`} key={`${message.role}-${index}`}><span>{message.role === "assistant" ? <Sparkles size={13} /> : "You"}</span><p>{message.content}</p></div>)}{busy && <div className="rex-chat-working"><LoaderCircle className="spin" size={14} /> REX is organizing your details…</div>}</div>
    {Object.keys(profile).some((key) => key === "full_name" && profile[key]) && <div className="rex-profile-progress"><MessageCircle size={14} /><span>Profile is taking shape for <strong>{String(profile.full_name)}</strong>. Your answers are saved after you choose Save profile.</span></div>}
    {error && <div className="ai-error" role="alert">{error}</div>}
    <form className="rex-chat-composer" onSubmit={(event) => void sendMessage(event)}><textarea aria-label="Your answer to REX" rows={3} maxLength={5000} value={input} onChange={(event) => setInput(event.target.value)} placeholder="Write naturally — role, company, education, grades, projects, skills…" disabled={busy || saving} /><button className="ai-primary-button" type="submit" disabled={!input.trim() || busy || saving}>{busy ? <LoaderCircle size={15} className="spin" /> : <Send size={15} />} Send</button></form>
    <footer><span>Your profile remains private to your account.</span><div><button className="ai-secondary-button" type="button" onClick={onClose} disabled={busy || saving}>Cancel</button><button className="ai-primary-button" type="button" onClick={() => void saveProfile()} disabled={!ready || saving || busy}>{saving ? <LoaderCircle size={15} className="spin" /> : <Save size={15} />} Save profile</button></div></footer>
  </section></div>;
}
