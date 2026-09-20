import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../lib/api";
import { useStore } from "./StoreContext";

function setMeta(attribute, key, content) {
  const node = document.createElement("meta");
  node.dataset.seoOwned = "true"; node.setAttribute(attribute, key); node.content = content;
  document.head.appendChild(node);
}

export function applySeo(page) {
  document.head.querySelectorAll("[data-seo-owned]").forEach(node => node.remove());
  const title = document.createElement("title"); title.dataset.seoOwned = "true"; title.textContent = page.title;
  document.head.appendChild(title);
  setMeta("name", "description", page.description);
  setMeta("name", "robots", page.robots);
  for (const [key, value] of Object.entries({ "og:title": page.title, "og:description": page.description, "og:type": page.og_type, "og:site_name": page.site_name, "og:locale": "en_IN" })) setMeta("property", key, value);
  for (const [key, value] of Object.entries({ "twitter:card": page.image ? "summary_large_image" : "summary", "twitter:title": page.title, "twitter:description": page.description })) setMeta("name", key, value);
  if (page.canonical) {
    const canonical = document.createElement("link"); canonical.dataset.seoOwned = "true"; canonical.rel = "canonical"; canonical.href = page.canonical; document.head.appendChild(canonical);
    setMeta("property", "og:url", page.canonical);
  }
  if (page.image) { setMeta("property", "og:image", page.image); setMeta("name", "twitter:image", page.image); }
  page.schemas.forEach(schema => { const node = document.createElement("script"); node.dataset.seoOwned = "true"; node.type = "application/ld+json"; node.textContent = JSON.stringify(schema); document.head.appendChild(node); });
}

export const SeoManager = () => {
  const { pathname } = useLocation();
  const { settings } = useStore();
  const settingsVersion = JSON.stringify(settings);
  useEffect(() => {
    let active = true;
    api.get("/seo/page", { params: { path: pathname, hostname: window.location.hostname } }).then(({ data }) => { if (active) applySeo(data); }).catch(() => {
      if (active) { document.head.querySelectorAll('[name="robots"]').forEach(n => n.remove()); setMeta("name", "robots", "noindex, nofollow"); }
    });
    return () => { active = false; };
  }, [pathname, settingsVersion]);
  return null;
};