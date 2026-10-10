import { Check, Plus } from "lucide-react";

export const emptyVideo = { title: "", platform: "YouTube", video_url: "", description: "", status: "active" };
const fields = [
  ["title", "Title", "text"], ["video_url", "Video link (public URL)", "url"]
];
export const VideoForm = ({ draft, setDraft, editing, saving, onSubmit, onCancel, error }) => {
  const update = (key, value) => setDraft(d => ({ ...d, [key]: value }));
  return <form className="settings-form product-editor" onSubmit={onSubmit} data-testid="video-form">
    <div className="section-title"><h2 data-testid="video-form-title">{editing ? "Edit video" : "Add a promo video"}</h2></div>
    <div className="form-grid">{fields.map(([key, label, type]) => <label key={key} className={key === "video_url" ? "wide" : undefined}>{label}<input type={type} value={draft[key] ?? ""} required maxLength={type === "url" ? 2000 : 200} onChange={e => update(key, e.target.value)} data-testid={`video-${key.replaceAll("_", "-")}-input`}/></label>)}
      {[["platform", "Platform", ["YouTube", "Instagram", "Facebook", "WhatsApp", "Other"]], ["status", "Visibility", ["active", "inactive"]]].map(([key, label, options]) => <label key={key}>{label}<select value={draft[key]} onChange={e => update(key, e.target.value)} data-testid={`video-${key}-select`}>{options.map(v => <option key={v} value={v}>{v}</option>)}</select></label>)}
      <label className="wide">Description (optional)<textarea value={draft.description} onChange={e => update("description", e.target.value)} maxLength={1000} data-testid="video-description-input"/></label>
    </div>
    {error && <p className="error-message" role="alert" data-testid="video-add-error">{error}</p>}
    <div className="action-row"><button className="button button-accent" disabled={saving} data-testid={editing ? "video-update-button" : "video-add-button"}>{saving ? "Saving…" : editing ? <><Check size={16}/> Save changes</> : <><Plus size={16}/> Add video</>}</button><button type="button" className="button button-light" onClick={onCancel} disabled={saving} data-testid="video-cancel-button">Cancel</button></div>
  </form>;
};
