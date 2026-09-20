import { useState } from "react";
import { ChevronDown, RotateCw } from "lucide-react";
import { api, errorMessage, money } from "../../lib/api";

const emailLabels = { accepted: "Accepted by email provider", not_configured: "Owner email missing", pending: "Queued", sending: "Sending", failed: "Failed", unknown: "Unconfirmed" };
export const OrderTable = ({ orders, onUpdate, onReplace }) => {
  const [expanded, setExpanded] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const retry = async (order, recipient) => {
    setBusy(`${order.order_id}-${recipient}`); setError("");
    try { const { data } = await api.post(`/admin/orders/${order.order_id}/retry-email`, null, { params: { recipient } }); onReplace(data); }
    catch (err) { setError(errorMessage(err)); } finally { setBusy(""); }
  };
  return <div className="orders-list">
    {error && <p className="error-message" data-testid="order-action-error" role="alert">{error}</p>}
    {!orders.length && <p className="empty" data-testid="orders-empty">No orders for this view.</p>}
    {orders.map(o => <article className="order-row" key={o.order_id} data-testid={`order-row-${o.order_id}`}>
      <div className="order-row-main"><div><b data-testid={`order-number-${o.order_id}`}>{o.order_number}</b><small data-testid={`order-date-${o.order_id}`}>{new Date(o.created_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST</small></div>
        <div><b data-testid={`order-customer-${o.order_id}`}>{o.customer_name}</b><small data-testid={`order-email-${o.order_id}`}>{o.customer_email}</small></div><strong data-testid={`order-total-${o.order_id}`}>{money(o.total)}</strong>
        {onUpdate ? <select aria-label={`Status for ${o.order_number}`} value={o.status} onChange={e => onUpdate(o.order_id, e.target.value)} data-testid={`order-status-${o.order_id}`}>{["PLACED", "PROCESSING", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED"].map(s => <option key={s}>{s}</option>)}</select> : <span className="status-pill" data-testid={`order-status-${o.order_id}`}>{o.status}</span>}
        <button className="icon-button" title="Order details" aria-label={`Details for ${o.order_number}`} aria-expanded={expanded === o.order_id} onClick={() => setExpanded(expanded === o.order_id ? null : o.order_id)} data-testid={`order-expand-${o.order_id}`}><ChevronDown size={18}/></button>
      </div>
      {expanded === o.order_id && <div className="order-details" data-testid={`order-details-${o.order_id}`}><div><h3>Delivery details</h3><p data-testid={`order-address-${o.order_id}`}>{o.customer_name}<br/>{o.customer_phone}<br/>{o.address}<br/>{o.city} – {o.pincode}</p>{o.items.map((item, i) => <p className="order-item-detail" data-testid={`order-item-${o.order_id}-${i}`} key={i}><span>{item.title}<small>{item.sku} · Qty {item.quantity} × {money(item.price)}</small></span><b>{money(item.quantity * item.price)}</b></p>)}</div>
        <div><h3>Email notifications</h3>{["owner", "customer"].map(recipient => { const result = o.notifications?.[recipient]; return <div className="email-result" key={recipient}><b>{recipient === "owner" ? "Store owner" : "Customer"}</b><span data-testid={`email-status-${o.order_id}-${recipient}`}>{emailLabels[result?.status] || "Not tracked (older order)"}</span>{result?.recipient && <small data-testid={`email-recipient-${o.order_id}-${recipient}`}>{result.recipient}</small>}{result?.error && <small className="email-error" data-testid={`email-error-${o.order_id}-${recipient}`}>{result.error}</small>}{onReplace && result?.status !== "accepted" && <button className="button button-light compact" disabled={busy === `${o.order_id}-${recipient}`} onClick={() => retry(o, recipient)} data-testid={`email-retry-${o.order_id}-${recipient}`}><RotateCw size={14}/>{busy === `${o.order_id}-${recipient}` ? "Sending…" : "Retry email"}</button>}</div>; })}<small className="muted" data-testid={`email-delivery-note-${o.order_id}`}>Provider acceptance does not confirm inbox delivery.</small></div>
      </div>}
    </article>)}
  </div>;
};