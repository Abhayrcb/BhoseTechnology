import { Link } from "react-router-dom";
import { Settings, ShoppingBag } from "lucide-react";
import { Brand } from "./Brand";
import { useStore } from "./StoreContext";

export const Shell = ({ children, cartCount = 0 }) => {
  const { settings } = useStore();
  return <><header className="site-header"><Link to="/" className="brand" data-testid="brand-home-link"><Brand testId="header-store-name"/></Link><nav><Link to="/" data-testid="nav-shop-link">Shop</Link><Link to="/#why" data-testid="nav-why-link">Why us</Link><Link to="/admin" className="nav-admin" data-testid="nav-admin-link"><Settings size={15}/> Admin</Link><Link to="/cart" className="cart-link" data-testid="nav-cart-link"><ShoppingBag size={17}/><span>Bag</span>{cartCount > 0 && <b data-testid="cart-count">{cartCount}</b>}</Link></nav></header>{children}<footer><div className="footer-inner"><div><div className="brand footer-brand"><Brand testId="footer-store-name"/></div><p>Better second-hand tech, without the guesswork.</p></div><div className="footer-note" data-testid="footer-copyright">Checked by people. Chosen by you.<br/>© {new Date().getFullYear()} {settings?.store_name}</div></div></footer></>;
};