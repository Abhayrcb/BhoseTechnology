import { useState } from "react";
import { Pencil, Plus, Trash2, Save, Search } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "../ui/dialog";
import { api, errorMessage, money } from "../../lib/api";
import { emptyProduct, ProductForm } from "./ProductForm";

export const ProductAdmin = ({ products, setProducts }) => {
  const [draft, setDraft] = useState(emptyProduct);
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [saving, setSaving] = useState(false);
  const [stock, setStock] = useState({});
  const [busyStock, setBusyStock] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");
  const startEdit = p => { setEditing(p?.product_id || null); setDraft(p ? { ...emptyProduct, ...p, expected_stock: p.stock_quantity, compare_at_price: p.compare_at_price ?? "" } : { ...emptyProduct }); setError(""); setShowForm(true); };
  const replace = p => setProducts(list => list.map(item => item.product_id === p.product_id ? p : item));
  const save = async e => {
    e.preventDefault(); setSaving(true); setError(""); setMessage("");
    try {
      const payload = { ...draft, compare_at_price: draft.compare_at_price === "" ? null : Number(draft.compare_at_price) };
      const { data } = editing ? await api.put(`/admin/products/${editing}`, payload) : await api.post("/admin/products", payload);
      if (editing) replace(data); else setProducts(list => [data, ...list]);
      setStock(values => { const next = { ...values }; delete next[data.product_id]; return next; });
      setShowForm(false); setMessage(editing ? "Product updated." : "Product added.");
    } catch (err) { setError(errorMessage(err)); if (err.response?.status === 409) { try { const { data } = await api.get("/admin/products"); setProducts(data); } catch (_) {} } } finally { setSaving(false); }
  };
  const remove = async () => {
    setSaving(true); setError("");
    try { await api.delete(`/admin/products/${deleting.product_id}`); setProducts(list => list.filter(p => p.product_id !== deleting.product_id)); setDeleting(null); setMessage("Product deleted. Existing order records are unchanged."); }
    catch (err) { setError(errorMessage(err)); } finally { setSaving(false); }
  };
  const saveStock = async p => {
    setBusyStock(p.product_id); setError(""); setMessage("");
    try {
      const { data } = await api.patch(`/admin/products/${p.product_id}/stock`, { stock_quantity: Number(stock[p.product_id]), expected_stock: p.stock_quantity });
      replace(data); setStock(values => { const next = { ...values }; delete next[p.product_id]; return next; }); setMessage(`Stock saved for ${p.title}.`);
    } catch (err) { setError(errorMessage(err)); if (err.response?.status === 409) { try { const { data } = await api.get("/admin/products"); setProducts(data); setStock({}); } catch (_) {} } }
    finally { setBusyStock(""); }
  };
  return <div className="inventory-workspace">
    <div className="inventory-toolbar"><div className="search-box"><Search size={17}/><input placeholder="Search inventory" value={search} onChange={e => setSearch(e.target.value)} data-testid="inventory-search-input"/></div><button className="button button-accent" onClick={() => startEdit(null)} data-testid="inventory-add-button"><Plus size={16}/> Add laptop</button></div>
    {message && <p className="success-message" role="status" data-testid="inventory-success">{message}</p>}
    {error && !showForm && !deleting && <p className="error-message" role="alert" data-testid="inventory-error">{error}</p>}
    <div className="inventory-list managed-inventory">{products.filter(p => `${p.title} ${p.sku}`.toLowerCase().includes(search.toLowerCase())).map(p => <div className="inventory-row" key={p.product_id} data-testid={`inventory-row-${p.product_id}`}>
      <img src={p.image_url} alt={p.title}/><div className="inventory-name"><b data-testid={`inventory-title-${p.product_id}`}>{p.title}</b><small>{p.sku}</small><span className={`status-pill ${p.status === "inactive" ? "muted-pill" : ""}`} data-testid={`inventory-status-${p.product_id}`}>{p.status === "inactive" ? "Hidden" : p.stock_quantity > 0 ? "Active" : "Out of stock"}</span></div>
      <strong data-testid={`inventory-price-${p.product_id}`}>{money(p.price)}</strong>
      <form className="stock-control" onSubmit={e => { e.preventDefault(); saveStock(p); }}><label htmlFor={`stock-${p.product_id}`}>In stock</label><div><input id={`stock-${p.product_id}`} type="number" min="0" step="1" required value={stock[p.product_id] ?? p.stock_quantity} onChange={e => setStock({ ...stock, [p.product_id]: e.target.value })} data-testid={`inventory-stock-${p.product_id}`}/><button className="icon-button" title="Save stock" aria-label={`Save stock for ${p.title}`} disabled={busyStock === p.product_id || stock[p.product_id] === undefined} data-testid={`inventory-save-stock-${p.product_id}`}><Save size={17}/></button></div></form>
      <div className="action-row"><button className="icon-button" title="Edit laptop" aria-label={`Edit ${p.title}`} onClick={() => startEdit(p)} data-testid={`inventory-edit-${p.product_id}`}><Pencil size={17}/></button><button className="icon-button danger" title="Delete laptop" aria-label={`Delete ${p.title}`} onClick={() => { setDeleting(p); setError(""); }} data-testid={`inventory-delete-${p.product_id}`}><Trash2 size={17}/></button></div>
    </div>)}</div>
    {!products.length && <p className="empty" data-testid="inventory-empty">No products yet.</p>}
    <Dialog open={showForm} onOpenChange={open => { if (!saving) setShowForm(open); }}><DialogContent className="product-modal" data-testid="product-edit-modal"><DialogTitle className="sr-only">{editing ? "Edit laptop" : "Add laptop"}</DialogTitle><DialogDescription className="sr-only">Product information and inventory</DialogDescription><ProductForm draft={draft} setDraft={setDraft} editing={editing} saving={saving} onSubmit={save} onCancel={() => setShowForm(false)} error={error}/></DialogContent></Dialog>
    <Dialog open={!!deleting} onOpenChange={open => { if (!open && !saving) setDeleting(null); }}><DialogContent className="confirm-modal" data-testid="product-delete-modal"><DialogTitle>Delete this laptop?</DialogTitle><DialogDescription data-testid="product-delete-description">{deleting?.title} will be removed from inventory and the shop. Past orders will stay unchanged.</DialogDescription>{error && <p className="error-message" data-testid="product-delete-error">{error}</p>}<div className="action-row"><button className="button button-light" disabled={saving} onClick={() => setDeleting(null)} data-testid="product-delete-cancel">Keep product</button><button className="button button-danger" disabled={saving} onClick={remove} data-testid="product-delete-confirm">{saving ? "Deleting…" : "Delete product"}</button></div></DialogContent></Dialog>
  </div>;
};