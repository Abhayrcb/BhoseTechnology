import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Laptop, Package, Settings, SlidersHorizontal, AlertCircle } from "lucide-react";
import { api, errorMessage, money } from "../../lib/api";
import { Brand } from "../Brand";
import { useStore } from "../StoreContext";
import { ProductAdmin } from "./ProductAdmin";
import { OrderTable } from "./OrderTable";
import { OrdersAdmin } from "./OrdersAdmin";
import { SettingsAdmin } from "./SettingsAdmin";

export const AdminPanel = ({ tab, setTab, logout }) => {
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const { settings, setSettings } = useStore();
  const refreshOrders = useCallback(() => { api.get("/admin/orders").then(({ data }) => setOrders(data)).catch(err => setError(errorMessage(err))); }, []);
  useEffect(() => {
    Promise.all([api.get("/admin/products"), api.get("/admin/orders"), api.get("/settings")]).then(([p, o, s]) => { setProducts(p.data); setOrders(o.data); setSettings(s.data); }).catch(err => { if (err.response?.status === 401) logout(); else setError(errorMessage(err)); }).finally(() => setLoading(false));
    // Load once per workspace session; logout is supplied by the login screen.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <div className="admin-shell"><aside><Link to="/" className="brand" data-testid="admin-brand-home-link"><Brand testId="admin-brand-name"/></Link><p className="admin-label">CONTROL ROOM</p>{[["overview", "Overview", SlidersHorizontal], ["products", "Products", Laptop], ["orders", "Orders", Package], ["settings", "Settings", Settings]].map(([key, label, Icon]) => <button className={tab === key ? "active" : ""} onClick={() => setTab(key)} key={key} data-testid={`admin-tab-${key}`}><Icon size={17}/>{label}</button>)}<button className="logout" onClick={logout} data-testid="admin-logout-button">Sign out</button></aside>
    <section className="admin-main"><div className="admin-top"><div><p className="eyebrow">{tab.toUpperCase()}</p><h1 data-testid="admin-page-title">{{ overview: "The shop at a glance.", products: "Your inventory.", orders: "Orders to take care of.", settings: "Store settings." }[tab]}</h1></div><Link to="/" className="button button-light" data-testid="view-store-button">View store <ArrowRight size={16}/></Link></div>
      {!loading && !settings?.owner_email && <div className="owner-warning" role="alert" data-testid="owner-email-warning"><AlertCircle size={20}/><span>Owner email is missing. New order emails cannot reach your store.</span><button onClick={() => setTab("settings")} data-testid="configure-owner-email-button">Add owner email <ArrowRight size={15}/></button></div>}
      {error && <p className="error-message" data-testid="admin-load-error" role="alert">{error}</p>}
      {loading ? <p className="loading" data-testid="admin-loading">Loading workspace…</p> : <>
        {tab === "overview" && <><div className="stat-grid"><div><span>Units in stock</span><b data-testid="admin-stat-products">{products.filter(p => p.status === "active").reduce((sum, p) => sum + p.stock_quantity, 0)}</b></div><div><span>Orders placed</span><b data-testid="admin-stat-orders">{orders.length}</b></div><div><span>Order value</span><b data-testid="admin-stat-value">{money(orders.reduce((s, o) => s + o.total, 0))}</b></div></div><section className="admin-table-block"><h2>Latest orders</h2><OrderTable orders={orders.slice(0, 5)}/></section></>}
        {tab === "products" && <ProductAdmin products={products} setProducts={setProducts}/>}
        {tab === "orders" && <OrdersAdmin onOrdersChanged={refreshOrders}/>}
        {tab === "settings" && <SettingsAdmin/>}
      </>}
    </section></div>;
};