import { useState } from "react";
import { Check, Download, Mail } from "lucide-react";
import { api, errorMessage } from "../../lib/api";
import { downloadBlob } from "./OrdersAdmin";
import { useStore } from "../StoreContext";

export const SettingsAdmin = () => {
  const { settings, setSettings } = useStore();
  const [draft, setDraft] = useState({ ...settings });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const update = (key, value) => { setDraft({ ...draft, [key]: value }); setMessage(""); setError(""); };
  const save = async e => {
    e.preventDefault(); setBusy("save"); setError(""); setMessage("");
    try { const { data } = await api.put("/admin/settings", { ...draft, owner_email: draft.owner_email?.trim() || null }); setSettings(data); setDraft(data); setMessage("Settings saved."); }
    catch (err) { setError(errorMessage(err)); } finally { setBusy(""); }
  };
  const testEmail = async () => {
    setBusy("test"); setError(""); setMessage("");
    try { const { data } = await api.post("/admin/email/test"); if (data.status === "accepted") setMessage(`Test email accepted by provider for ${data.recipient}. Check that inbox.`); else setError(data.error || "Test email failed."); }
    catch (err) { setError(errorMessage(err)); } finally { setBusy(""); }
  };
  const download = async () => {
    setBusy("docs"); setError("");
    try { const { data } = await api.get("/admin/documentation", { responseType: "blob" }); downloadBlob(data, "Website-Tech-Stack.md"); }
    catch (err) { setError("Documentation could not be downloaded."); } finally { setBusy(""); }
  };
  return <div className="settings-workspace"><form className="settings-form" onSubmit={save} onInvalid={event => setError(event.target.type === "email" ? "Please enter a valid store owner email address." : "Please enter your store name.")}>
    <h2>Store identity & contact</h2><div className="form-grid">
      {[["store_name", "Store name", "text", "store-name"], ["owner_email", "Store owner email", "email", "owner-email"], ["phone", "Phone", "tel", "phone"], ["address", "Address", "text", "address"], ["hero_title", "Hero title", "text", "hero-title"]].map(([key, label, type, id]) => <label key={key}>{label}<input type={type} value={draft[key] || ""} required={key === "store_name"} maxLength={key === "store_name" ? 80 : undefined} onChange={e => update(key, e.target.value)} data-testid={`settings-${id}-input`}/></label>)}
      {[["hero_subtitle", "Hero subtitle", "hero-subtitle"], ["shipping_policy", "Shipping policy", "shipping"], ["return_policy", "Return policy", "return"]].map(([key, label, id]) => <label className="wide" key={key}>{label}<textarea value={draft[key] || ""} onChange={e => update(key, e.target.value)} data-testid={`settings-${id}-input`}/></label>)}
    </div><button className="button button-accent" disabled={!!busy} data-testid="settings-save-button"><Check size={16}/>{busy === "save" ? "Saving…" : "Save settings"}</button>
    </form>
    <section className="settings-section"><h2>Order notifications</h2><p className="muted" data-testid="settings-email-recipient">Saved owner email: {settings?.owner_email || "Not configured"}</p><button className="button button-light" disabled={!!busy || !settings?.owner_email} onClick={testEmail} data-testid="settings-test-email-button"><Mail size={16}/>{busy === "test" ? "Sending…" : "Send test email"}</button></section>
    <section className="settings-section"><h2>Website documentation</h2><button className="button button-light" disabled={!!busy} onClick={download} data-testid="settings-download-docs-button"><Download size={16}/>{busy === "docs" ? "Preparing…" : "Download tech-stack document"}</button></section>
    {message && <p className="success-message" role="status" data-testid="settings-saved-message">{message}</p>}{error && <p className="error-message" role="alert" data-testid="settings-error">{error}</p>}
  </div>;
};