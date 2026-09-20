import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export const SeoSettings = ({ draft, update }) => {
  const [config, setConfig] = useState(null);
  useEffect(() => { api.get("/seo/config", { params: { hostname: window.location.hostname } }).then(({ data }) => setConfig(data)).catch(() => setConfig({ error: true })); }, []);
  return <section className="settings-section seo-settings">
    <h2>Search appearance</h2>
    <p className="status-pill" data-testid="seo-indexing-status">{!config ? "Checking…" : config.error ? "Status unavailable" : config.request_indexable ? "Indexing enabled" : "Preview · Not indexed"}</p>
    <p className="muted" data-testid="seo-domain-status">{config?.site_url || "Final domain pending"}</p>
    <div className="form-grid">
      {[["seo_city", "Target city", "Kolkata"], ["seo_region", "State / region", "West Bengal"]].map(([key, label, placeholder]) => <label key={key}>{label}<input required maxLength={60} value={draft[key] ?? placeholder} onChange={e => update(key, e.target.value)} data-testid={`settings-${key.replaceAll("_", "-")}-input`}/></label>)}
      <label className="wide">Search title (optional override)<input value={draft.seo_title || ""} maxLength={160} placeholder={`${draft.store_name} | Refurbished Laptops in ${draft.seo_city || "Kolkata"}`} onChange={e => update("seo_title", e.target.value)} data-testid="settings-seo-title-input"/></label>
      <label className="wide">Search description (optional override)<textarea value={draft.seo_description || ""} maxLength={320} placeholder={`Shop second-hand and refurbished laptops at ${draft.store_name} in ${draft.seo_city || "Kolkata"}, ${draft.seo_region || "West Bengal"}.`} onChange={e => update("seo_description", e.target.value)} data-testid="settings-seo-description-input"/></label>
    </div>
  </section>;
};