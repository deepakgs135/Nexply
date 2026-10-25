import { useEffect, useState } from "react";
import { Clock3, FileCheck2, FileText, LoaderCircle, ShieldCheck, Trash2 } from "lucide-react";
import type { ApiRequest } from "../shared/api";
import StructuredProfile from "../components/StructuredProfile";
import type { Profile } from "../shared/resumeFormat";

type HistoryItem = {
  document_id: string;
  original_filename: string;
  original_size_bytes?: number;
  created_at?: string;
  parsing_status?: string;
  llm_status?: string;
  candidate_name?: string | null;
  professional_title?: string | null;
};
type HistoryResponse = { items: HistoryItem[]; total: number; skip: number; limit: number };
type HistoryProfile = HistoryItem & { structured_result?: Profile | null };

export default function ResumeHistoryPage({ request, enabled = true }: { request: ApiRequest; enabled?: boolean }) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedId, setSelectedId] = useState("");
  const [selected, setSelected] = useState<HistoryProfile | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [deletingId, setDeletingId] = useState("");
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!enabled) return;
    let current = true;
    setLoadingList(true);
    setError("");
    request<HistoryResponse>("/resumes/history?skip=0&limit=50")
      .then((result) => {
        if (!current) return;
        setItems(result.items);
        setTotal(result.total);
        setSelectedId((active) => active && result.items.some((item) => item.document_id === active)
          ? active : result.items[0]?.document_id || "");
      })
      .catch((caught) => { if (current) setError(caught instanceof Error ? caught.message : "Unable to load resume history."); })
      .finally(() => { if (current) setLoadingList(false); });
    return () => { current = false; };
  }, [request, refreshKey, enabled]);

  useEffect(() => {
    if (!enabled) return;
    if (!selectedId) { setSelected(null); return; }
    let current = true;
    setLoadingProfile(true);
    setSelected(null);
    request<HistoryProfile>(`/resumes/${encodeURIComponent(selectedId)}/profile`)
      .then((profile) => { if (current) setSelected(profile); })
      .catch((caught) => { if (current) setError(caught instanceof Error ? caught.message : "Unable to load this resume profile."); })
      .finally(() => { if (current) setLoadingProfile(false); });
    return () => { current = false; };
  }, [request, selectedId, refreshKey, enabled]);

  async function loadMore() {
    setLoadingMore(true);
    setError("");
    try {
      const result = await request<HistoryResponse>(`/resumes/history?skip=${items.length}&limit=50`);
      setItems((current) => [...current, ...result.items]);
      setTotal(result.total);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load more resumes.");
    } finally {
      setLoadingMore(false);
    }
  }

  async function deleteItem(item: HistoryItem) {
    const confirmed = window.confirm(`Delete “${item.original_filename}”? This permanently removes the resume record and its stored original file.`);
    if (!confirmed) return;
    setDeletingId(item.document_id);
    setError("");
    try {
      await request<void>(`/resumes/${encodeURIComponent(item.document_id)}`, { method: "DELETE" });
      const remaining = items.filter((entry) => entry.document_id !== item.document_id);
      setItems(remaining);
      setTotal((count) => Math.max(0, count - 1));
      if (selectedId === item.document_id) {
        setSelected(null);
        setSelectedId(remaining[0]?.document_id || "");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to delete this resume.");
    } finally {
      setDeletingId("");
    }
  }

  const selectedSummary = items.find((item) => item.document_id === selectedId);
  const selectedFilename = selected?.original_filename || selectedSummary?.original_filename;

  return <div className="page-wrap history-page">
    <section className="page-intro history-intro">
      <div><div className="eyebrow"><span /> YOUR PRIVATE WORKSPACE</div><h1>Resume History</h1><p>Choose an uploaded resume to review its extracted candidate profile.</p></div>
      <button className="export-button history-refresh" type="button" onClick={() => setRefreshKey((value) => value + 1)}><Clock3 size={14} /> Refresh history</button>
    </section>
    <section className="history-layout">
      <aside className="history-list card">
        <div className="history-list-heading"><div><span className="section-eyebrow">UPLOADED RESUMES</span><h2>Resume library</h2></div><span className="section-count">{total}</span></div>
        {loadingList && items.length === 0 ? <div className="history-state"><LoaderCircle className="spin" size={20} /><span>Loading your resumes…</span></div>
          : items.length === 0 ? <div className="history-state"><FileText size={24} /><strong>No resumes yet</strong><span>Uploaded resumes will appear here.</span></div>
            : <div className="history-items">{items.map((item) => <div className={`history-item-shell ${selectedId === item.document_id ? "active" : ""}`} key={item.document_id}><button type="button" className="history-item" onClick={() => { setError(""); setSelectedId(item.document_id); }}>
              <span className="history-file-icon"><FileCheck2 size={17} /></span>
              <span className="history-item-copy"><strong title={item.original_filename}>{item.original_filename}</strong><small>{item.candidate_name || "Candidate profile"}</small><span className="history-item-meta">{item.created_at ? new Date(item.created_at).toLocaleString() : "Date unavailable"}</span><span className={`history-status ${item.llm_status === "completed" ? "complete" : item.llm_status === "failed" ? "failed" : "pending"}`}>{item.llm_status || "pending"}</span></span>
              <span className="history-item-chevron">›</span>
            </button><button className="history-delete-button" type="button" aria-label={`Delete ${item.original_filename}`} title="Delete resume and original file" disabled={deletingId === item.document_id} onClick={() => void deleteItem(item)}>{deletingId === item.document_id ? <LoaderCircle className="spin" size={15} /> : <Trash2 size={15} />}</button></div>)}</div>}
        {items.length < total && <button type="button" className="history-load-more" disabled={loadingMore} onClick={loadMore}>{loadingMore ? "Loading…" : "Load more resumes"}</button>}
      </aside>
      <article className="history-profile card">
        {!selectedId ? <div className="history-state history-empty-detail"><FileCheck2 size={30} /><strong>Select a resume</strong><span>The structured candidate details will appear here.</span></div>
          : loadingProfile ? <div className="history-state history-empty-detail"><LoaderCircle className="spin" size={22} /><span>Loading structured profile…</span></div>
            : selected ? <StructuredProfile profile={selected.structured_result || null} filename={selectedFilename} parsingStatus={selected.parsing_status} extractionStatus={selected.llm_status} documentId={selected.document_id} onProfileSaved={(profile) => { setSelected((current) => current ? { ...current, structured_result: profile } : current); setItems((current) => current.map((item) => item.document_id === selected.document_id ? { ...item, candidate_name: typeof profile.full_name === "string" ? profile.full_name : null, professional_title: typeof profile.professional_title === "string" ? profile.professional_title : null } : item)); }} />
              : <div className="history-state history-empty-detail"><FileText size={24} /><strong>Could not load this resume</strong><span>Select another resume or refresh your history.</span></div>}
        {error && <div className="history-error" role="alert">{error}</div>}
      </article>
    </section>
    <footer className="app-footer"><span>© 2026 NEXPLY AI</span><span>Resume history is private to your account.</span><span><ShieldCheck size={12} /> Owner protected</span></footer>
  </div>;
}
