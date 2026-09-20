import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, Check, ChevronLeft, Package, Search, ShieldCheck, ShoppingBag } from "lucide-react";
import { api, money } from "../lib/api";
import { Shell } from "../components/Shell";
import { useStore } from "../components/StoreContext";

export default function Storefront({ cartCount }) {
  const [products, setProducts] = useState([]);
  const { settings } = useStore();
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState("");
  const [category, setCategory] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true; setLoading(true);
    api.get("/products", { params: { search: query, brand, category } }).then(r => { if (active) { setProducts(r.data); setError(""); } }).catch(() => { if (active) setError("Laptops could not be loaded. Please try again shortly."); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [query, brand, category]);
  const brands = [...new Set([brand, ...products.map(p => p.brand)])].filter(Boolean);
  return <Shell cartCount={cartCount}><main><section className="hero"><div className="hero-copy"><p className="eyebrow">REFURBISHED • READY FOR MORE</p><h1 data-testid="home-hero-title">{settings?.hero_title || "Good tech. Better value."}</h1><p className="hero-subtitle" data-testid="home-hero-subtitle">{settings?.hero_subtitle}</p><a href="#collection" className="button button-dark" data-testid="hero-shop-button">Explore the collection <ArrowRight size={17}/></a></div><div className="hero-art"><img src="https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?auto=format&fit=crop&w=1400&q=85" alt="Silver laptop on a bright desk"/><div className="hero-stamp"><ShieldCheck size={17}/><span>30+ point<br/><b>quality check</b></span></div></div></section>
    <section className="trust-strip" id="why"><div><ShieldCheck/><span><b>Tested inside out</b><small>Every unit gets a real check</small></span></div><div><Package/><span><b>Honest condition</b><small>Clear grades. No surprises.</small></span></div><div><Check/><span><b>Store warranty</b><small>Support beyond checkout</small></span></div></section>
    <section className="collection" id="collection"><div className="section-heading"><div><p className="eyebrow">THE COLLECTION</p><h2>Find your next machine.</h2></div><p className="muted">Inspected laptops.<br/>Priced fairly.</p></div><div className="toolbar"><div className="search-box"><Search size={17}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search by model or brand" data-testid="product-search-input"/></div><select value={brand} onChange={e => setBrand(e.target.value)} data-testid="brand-filter"><option value="">All brands</option>{brands.map(b => <option key={b}>{b}</option>)}</select><select value={category} onChange={e => setCategory(e.target.value)} data-testid="category-filter"><option value="">All uses</option><option>Business</option><option>Student</option><option>Gaming</option></select><span className="result-count" data-testid="product-result-count">{products.length} available</span></div>
    {error && <p className="error-message" data-testid="collection-error" role="alert">{error}</p>}{loading ? <p className="loading" data-testid="collection-loading">Loading laptops…</p> : <><div className="product-grid">{products.map(p => <ProductCard key={p.product_id} product={p}/>)}</div>{!products.length && !error && <div className="empty" data-testid="collection-empty">No laptops match that search.</div>}</>}</section></main></Shell>;
}

export const ProductCard = ({ product: p }) => <Link to={`/product/${p.product_id}`} className="product-card" data-testid={`product-card-${p.product_id}`}><div className="product-image"><img src={p.image_url} alt={p.title}/><span className="condition-badge" data-testid={`product-grade-${p.product_id}`}>Grade {p.condition_grade}</span></div><div className="product-info"><div className="product-meta"><span>{p.brand}</span><span>{p.category}</span></div><h3 data-testid={`product-title-${p.product_id}`}>{p.title}</h3><p>{p.processor} · {p.ram_gb}GB RAM · {p.storage_gb}GB {p.storage_type}</p><div className="price-row"><strong data-testid={`product-price-${p.product_id}`}>{money(p.price)}</strong>{p.compare_at_price && <del data-testid={`product-original-price-${p.product_id}`}>{money(p.compare_at_price)}</del>}<ArrowRight size={18}/></div></div></Link>;

export const ProductDetail = ({ addToCart, cartCount }) => {
  const [product, setProduct] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const { id } = useParams();
  useEffect(() => { api.get(`/products/${id}`).then(r => setProduct(r.data)).catch(() => setError("This laptop is unavailable right now.")); }, [id]);
  if (error) return <Shell cartCount={cartCount}><main className="loading error-state"><p className="error-message" data-testid="product-detail-error">{error}</p><Link to="/" className="button button-dark" data-testid="product-detail-error-back">Back to collection</Link></main></Shell>;
  if (!product) return <Shell><div className="loading" data-testid="product-detail-loading">Loading laptop…</div></Shell>;
  const p = product;
  return <Shell cartCount={cartCount}><main className="detail-page"><Link to="/" className="back-link" data-testid="product-back-link"><ChevronLeft size={16}/> Back to collection</Link><div className="detail-layout"><div className="detail-image"><img src={p.image_url} alt={p.title}/><span className="condition-badge" data-testid="product-detail-grade">Grade {p.condition_grade}</span></div><div className="detail-copy"><p className="eyebrow">{p.brand} / {p.category}</p><h1 data-testid="product-detail-title">{p.title}</h1><p className="detail-description" data-testid="product-detail-description">{p.condition_description}</p><div className="detail-price"><strong data-testid="product-detail-price">{money(p.price)}</strong>{p.compare_at_price && <del data-testid="product-detail-original-price">{money(p.compare_at_price)}</del>}</div><div className="spec-grid">{[["Processor", p.processor], ["Memory", `${p.ram_gb}GB RAM`], ["Storage", `${p.storage_gb}GB ${p.storage_type}`], ["Display", p.display], ["Battery", p.battery_health], ["Warranty", `${p.warranty_months} months`]].map(([a, b]) => <div key={a} data-testid={`product-spec-${a.toLowerCase()}`}><span>{a}</span><b>{b}</b></div>)}</div><button className="button button-accent" disabled={p.stock_quantity < 1} onClick={() => { addToCart(p); setMessage("Added to your bag"); }} data-testid="add-to-cart-button"><ShoppingBag size={17}/>{p.stock_quantity > 0 ? "Add to bag" : "Out of stock"}</button>{message && <p className="success-message" data-testid="add-to-cart-success"><Check size={15}/>{message}</p>}<p className="stock-note" data-testid="product-detail-stock"><ShieldCheck size={15}/>{p.stock_quantity} {p.stock_quantity === 1 ? "unit" : "units"} in stock · inspected before dispatch</p></div></div></main></Shell>;
};