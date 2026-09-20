import { Laptop } from "lucide-react";
import { useStore } from "./StoreContext";

export const Brand = ({ testId = "store-brand-name" }) => {
  const { settings } = useStore();
  return <><span className="brand-mark"><Laptop size={20}/></span><span className="brand-name" data-testid={testId}>{settings?.store_name || "Store"}</span></>;
};