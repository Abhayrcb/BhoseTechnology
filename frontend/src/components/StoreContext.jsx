import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../lib/api";

const StoreContext = createContext(null);
export const StoreProvider = ({ children }) => {
  const [settings, setSettings] = useState(null);
  useEffect(() => { api.get("/settings").then(({ data }) => setSettings(data)).catch(() => {}); }, []);
  useEffect(() => { if (settings?.store_name) document.title = `${settings.store_name} | Refurbished laptops`; }, [settings?.store_name]);
  return <StoreContext.Provider value={{ settings, setSettings }}>{children}</StoreContext.Provider>;
};
export const useStore = () => useContext(StoreContext);