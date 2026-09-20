import { useEffect, useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { api, errorMessage, indiaToday, money } from "../../lib/api";
import { OrderTable } from "./OrderTable";

export const downloadBlob = (data, filename) => {
  const url = URL.createObjectURL(data);
  const link = document.createElement("a"); link.href = url; link.download = filename; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
export const OrdersAdmin = ({ onOrdersChanged }) => {
  const [date, setDate] = useState(indiaToday);
  const [all, setAll] = useState(false);
  const [orders, setOrders] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true; setLoading(true); setError("");
    api.get("/admin/orders", { params: all ? {} : { date } }).then(({ data }) => { if (active) setOrders(data); }).catch(err => { if (active) setError(errorMessage(err)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [date, all, reload]);
  const replace = data => { setOrders(list => list.map(o => o.order_id === data.order_id ? data : o)); onOrdersChanged(); };
  const update = async (id, status) => {
    try { await api.patch(`/admin/orders/${id}`, null, { params: { status } }); setOrders(list => list.map(o => o.order_id === id ? { ...o, status } : o)); onOrdersChanged(); }
    catch (err) { setError(errorMessage(err)); }
  };
  const download = async format => {
    setDownloading(format); setError("");
    try { const { data } = await api.get("/admin/orders/export", { params: { date, format }, responseType: "blob" }); downloadBlob(data, `orders-${date}.${format}`); }
    catch (err) { setError("Report download failed. Please try again."); } finally { setDownloading(""); }
  };
  return <div className="orders-workspace">
    <div className="report-toolbar"><label>Report date · India (IST)<input type="date" value={date} onChange={e => { if (e.target.value) { setDate(e.target.value); setAll(false); } }} data-testid="orders-date-input"/></label><button className="button button-light" onClick={() => { setDate(indiaToday()); setAll(false); setReload(v => v + 1); }} data-testid="orders-today-button">Today</button><button className="icon-button" title="Refresh orders" aria-label="Refresh orders" onClick={() => setReload(v => v + 1)} data-testid="orders-refresh-button"><RefreshCw size={18}/></button>
      <div className="report-downloads"><button className="button button-light" disabled={!!downloading} onClick={() => download("xlsx")} data-testid="orders-download-excel"><Download size={16}/>{downloading === "xlsx" ? "Preparing…" : "Excel"}</button><button className="button button-accent" disabled={!!downloading} onClick={() => download("pdf")} data-testid="orders-download-pdf"><Download size={16}/>{downloading === "pdf" ? "Preparing…" : "PDF"}</button></div>
    </div>
    <div className="orders-summary"><p data-testid="report-date-label">Downloads: {date} · IST</p><label className="checkbox-label"><input type="checkbox" checked={all} onChange={e => setAll(e.target.checked)} data-testid="orders-show-all"/> Show all orders in list</label></div>
    {error && <p className="error-message" data-testid="orders-error" role="alert">{error}</p>}
    {loading ? <p className="loading" data-testid="orders-loading">Loading orders…</p> : <><p className="muted" data-testid="orders-summary">{orders.length} orders · {money(orders.reduce((sum, o) => sum + o.total, 0))}</p><OrderTable orders={orders} onUpdate={update} onReplace={replace}/></>}
  </div>;
};