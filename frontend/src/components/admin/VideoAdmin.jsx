import { useEffect, useState } from "react";
import { Pencil, Plus, Trash2, Search, PlayCircle } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "../ui/dialog";
import { api, errorMessage } from "../../lib/api";
import { emptyVideo, VideoForm } from "./VideoForm";

export const VideoAdmin = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [draft, setDraft] = useState(emptyVideo);
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => { api.get("/admin/promo-videos").then(({ data }) => setVideos(data)).catch(err => setError(errorMessage(err))).finally(() => setLoading(false)); }, []);

  const startEdit = v => { setEditing(v?.video_id || null); setDraft(v ? { ...emptyVideo, ...v } : { ...emptyVideo }); setError(""); setShowForm(true); };
  const replace = v => setVideos(list => list.map(item => item.video_id === v.video_id ? v : item));
  const save = async e => {
    e.preventDefault(); setSaving(true); setError(""); setMessage("");
    try {
      const { data } = editing ? await api.put(`/admin/promo-videos/${editing}`, draft) : await api.post("/admin/promo-videos", draft);
      if (editing) replace(data); else setVideos(list => [data, ...list]);
      setShowForm(false); setMessage(editing ? "Video updated." : "Video added.");
    } catch (err) { setError(errorMessage(err)); } finally { setSaving(false); }
  };
  const remove = async () => {
    setSaving(true); setError("");
    try { await api.delete(`/admin/promo-videos/${deleting.video_id}`); setVideos(list => list.filter(v => v.video_id !== deleting.video_id)); setDeleting(null); setMessage("Video deleted."); }
    catch (err) { setError(errorMessage(err)); } finally { setSaving(false); }
  };

  const filtered = videos.filter(v => `${v.title} ${v.platform}`.toLowerCase().includes(search.toLowerCase()));

  return <div className="inventory-workspace">
    <div className="inventory-toolbar"><div className="search-box"><Search size={17}/><input placeholder="Search videos" value={search} onChange={e => setSearch(e.target.value)} data-testid="video-search-input"/></div><button className="button button-accent" onClick={() => startEdit(null)} data-testid="video-add-button-open"><Plus size={16}/> Add video</button></div>
    {message && <p className="success-message" role="status" data-testid="video-success">{message}</p>}
    {error && !showForm && !deleting && <p className="error-message" role="alert" data-testid="video-error">{error}</p>}
    {loading ? <p className="loading" data-testid="video-loading">Loading videos…</p> : <div className="inventory-list video-list">
      {filtered.map(v => <div className="inventory-row video-row" key={v.video_id} data-testid={`video-row-${v.video_id}`}>
        <span className="video-icon"><PlayCircle size={22}/></span>
        <div className="inventory-name"><b data-testid={`video-title-${v.video_id}`}>{v.title}</b><small>{v.platform}</small><span className={`status-pill ${v.status === "inactive" ? "muted-pill" : ""}`} data-testid={`video-status-${v.video_id}`}>{v.status === "inactive" ? "Hidden" : "Active"}</span></div>
        <a href={v.video_url} target="_blank" rel="noreferrer" className="video-link-preview" data-testid={`video-link-${v.video_id}`}>{v.video_url}</a>
        <div className="action-row"><button className="icon-button" title="Edit video" aria-label={`Edit ${v.title}`} onClick={() => startEdit(v)} data-testid={`video-edit-${v.video_id}`}><Pencil size={17}/></button><button className="icon-button danger" title="Delete video" aria-label={`Delete ${v.title}`} onClick={() => { setDeleting(v); setError(""); }} data-testid={`video-delete-${v.video_id}`}><Trash2 size={17}/></button></div>
      </div>)}
    </div>}
    {!loading && !filtered.length && <p className="empty" data-testid="video-empty">No promo videos yet.</p>}
    <Dialog open={showForm} onOpenChange={open => { if (!saving) setShowForm(open); }}><DialogContent className="product-modal" data-testid="video-edit-modal"><DialogTitle className="sr-only">{editing ? "Edit video" : "Add video"}</DialogTitle><DialogDescription className="sr-only">Promo video link details</DialogDescription><VideoForm draft={draft} setDraft={setDraft} editing={editing} saving={saving} onSubmit={save} onCancel={() => setShowForm(false)} error={error}/></DialogContent></Dialog>
    <Dialog open={!!deleting} onOpenChange={open => { if (!open && !saving) setDeleting(null); }}><DialogContent className="confirm-modal" data-testid="video-delete-modal"><DialogTitle>Delete this video?</DialogTitle><DialogDescription data-testid="video-delete-description">{deleting?.title} will be removed from the promo videos page.</DialogDescription>{error && <p className="error-message" data-testid="video-delete-error">{error}</p>}<div className="action-row"><button className="button button-light" disabled={saving} onClick={() => setDeleting(null)} data-testid="video-delete-cancel">Keep video</button><button className="button button-danger" disabled={saving} onClick={remove} data-testid="video-delete-confirm">{saving ? "Deleting…" : "Delete video"}</button></div></DialogContent></Dialog>
  </div>;
};
