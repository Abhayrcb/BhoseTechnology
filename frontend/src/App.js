import { useEffect, useState } from "react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import axios from "axios";
import { LogIn } from "lucide-react";
import { StoreProvider } from "./components/StoreContext";
import { Brand } from "./components/Brand";
import { SeoManager } from "./components/SeoManager";
import { Shell } from "./components/Shell";
import { AdminPanel } from "./components/admin/AdminPanel";
import Storefront, { ProductDetail } from "./pages/Storefront";
import { Cart, Checkout } from "./pages/CartCheckout";
import "@/App.css";
import "./admin.css";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function Admin(){const [logged,setLogged]=useState(!!localStorage.getItem("admin_token")); const [tab,setTab]=useState("overview"); const [email,setEmail]=useState(""); const [password,setPassword]=useState(""); const [error,setError]=useState(""); const login=async e=>{e.preventDefault();try{const r=await axios.post(`${API}/auth/login`,{email,password});localStorage.setItem("admin_token",r.data.token);setLogged(true);}catch(e){setError(e.response?.data?.detail||"Login failed");}}; if(!logged)return <div className="admin-login"><Link to="/" className="brand" data-testid="admin-login-home-link"><Brand testId="admin-login-store-name"/></Link><form onSubmit={login}><p className="eyebrow">PRIVATE WORKSPACE</p><h1>Good to see you.</h1><p className="muted">Sign in to keep the storefront up to date.</p><label>Admin email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required data-testid="admin-email-input"/></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required data-testid="admin-password-input"/></label>{error&&<p className="error-message" data-testid="admin-login-error">{error}</p>}<button className="button button-accent full" data-testid="admin-login-button"><LogIn size={17}/> Sign in</button></form></div>; return <AdminPanel tab={tab} setTab={setTab} logout={()=>{localStorage.removeItem("admin_token");setLogged(false)}}/>}

function App() {
  const [cart, setCart] = useState(() => { try { return JSON.parse(localStorage.getItem("cart") || "[]"); } catch { return []; } });
  useEffect(() => localStorage.setItem("cart", JSON.stringify(cart)), [cart]);
  const add = p => setCart(items => [...items.filter(x => x.product_id !== p.product_id), p]);
  return <StoreProvider><BrowserRouter><SeoManager/><Routes>
    <Route path="/" element={<Storefront cartCount={cart.length}/>}/>
    <Route path="/product/:id" element={<ProductDetail addToCart={add} cartCount={cart.length}/>}/>
    <Route path="/cart" element={<Cart cart={cart} setCart={setCart}/>}/>
    <Route path="/checkout" element={<Checkout cart={cart} setCart={setCart}/>}/>
    <Route path="/admin" element={<Admin/>}/>
    <Route path="*" element={<Shell><main className="empty"><h1 data-testid="not-found-title">Page not found</h1><Link className="button button-dark" to="/" data-testid="not-found-home-link">Back to shop</Link></main></Shell>}/>
  </Routes></BrowserRouter></StoreProvider>;
}
export default App;