import { Check, Plus } from "lucide-react";

export const emptyProduct = { title: "", brand: "Lenovo", category: "Business", price: "", compare_at_price: "", processor: "", ram_gb: 8, storage_type: "SSD", storage_gb: 256, stock_quantity: 1, image_url: "", condition_grade: "A", condition_description: "Professionally checked and ready to use.", display: "14-inch Full HD", gpu: "Integrated", battery_health: "Tested", operating_system: "Windows 11 Pro", warranty_months: 3, status: "active" };
const fields = [
  ["title", "Title", "text"], ["brand", "Brand", "text"], ["price", "Price (INR)", "number", 1], ["compare_at_price", "Original price (optional)", "number", 1],
  ["processor", "Processor", "text"], ["ram_gb", "RAM (GB)", "number", 1], ["storage_gb", "Storage (GB)", "number", 1], ["stock_quantity", "Stock quantity", "number", 0],
  ["display", "Display", "text"], ["gpu", "Graphics", "text"], ["battery_health", "Battery health", "text"], ["operating_system", "Operating system", "text"], ["warranty_months", "Warranty (months)", "number", 0], ["image_url", "Image URL", "url"]
];
const ids = { ram_gb: "ram", storage_gb: "storage", image_url: "image", stock_quantity: "stock" };
export const ProductForm = ({ draft, setDraft, editing, saving, onSubmit, onCancel, error }) => {
  const update = (key, value) => setDraft(d => ({ ...d, [key]: value }));
  return <form className="settings-form product-editor" onSubmit={onSubmit} data-testid="product-form">
    <div className="section-title"><h2 data-testid="product-form-title">{editing ? "Edit laptop" : "Add a laptop"}</h2></div>
    <div className="form-grid">{fields.map(([key, label, type, min]) => <label key={key}>{label}<input type={type} min={min} step={type === "number" ? 1 : undefined} value={draft[key] ?? ""} required={key !== "compare_at_price"} maxLength={type !== "number" ? 1000 : undefined} onChange={e => update(key, type === "number" && e.target.value !== "" ? Number(e.target.value) : e.target.value)} data-testid={`product-${ids[key] || key.replaceAll("_", "-")}-input`}/></label>)}
      {[["category", "Category", ["Business", "Student", "Gaming"]], ["condition_grade", "Condition grade", ["A", "B", "C"]], ["storage_type", "Storage type", ["SSD", "NVMe SSD", "HDD"]], ["status", "Visibility", ["active", "inactive"]]].map(([key, label, options]) => <label key={key}>{label}<select value={draft[key]} onChange={e => update(key, e.target.value)} data-testid={`product-${key.replaceAll("_", "-")}-select`}>{[...new Set([...options, draft[key]])].filter(Boolean).map(v => <option key={v} value={v}>{v}</option>)}</select></label>)}
      <label className="wide">Condition & description<textarea value={draft.condition_description} onChange={e => update("condition_description", e.target.value)} required maxLength={5000} data-testid="product-description-input"/></label>
    </div>
    {error && <p className="error-message" role="alert" data-testid="product-add-error">{error}</p>}
    <div className="action-row"><button className="button button-accent" disabled={saving} data-testid={editing ? "product-update-button" : "product-add-button"}>{saving ? "Saving…" : editing ? <><Check size={16}/> Save changes</> : <><Plus size={16}/> Add laptop</>}</button><button type="button" className="button button-light" onClick={onCancel} disabled={saving} data-testid="product-cancel-button">Cancel</button></div>
  </form>;
};