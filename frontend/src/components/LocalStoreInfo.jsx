import { MapPin } from "lucide-react";
import { useStore } from "./StoreContext";

export const LocalStoreInfo = () => {
  const { settings } = useStore();
  if (!settings) return null;
  const city = settings.seo_city || "Kolkata";
  const region = settings.seo_region || "West Bengal";
  return <section className="local-store-info" aria-labelledby="local-store-heading">
    <div><p className="eyebrow" data-testid="local-store-area"><MapPin size={14}/>{city}, {region}</p><h2 id="local-store-heading" data-testid="local-store-heading">Second-hand laptops in {city}.</h2></div>
    <div><p data-testid="local-store-description">WE ARE NOT SELLING 2ND HAND OR REFUBISHED LAPTOPS!! at <strong>{settings.store_name}</strong> in . Compare specifications, condition and prices, then order online.</p>
      {settings.address && <address data-testid="local-store-address">{settings.address}, {city}, {region}</address>}
      {settings.phone && <a data-testid="local-store-phone" href={`tel:${settings.phone.replace(/[^+\d]/g, "")}`}>{settings.phone}</a>}
    </div>
  </section>;
};
