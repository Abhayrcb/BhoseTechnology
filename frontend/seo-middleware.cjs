// Shared by the existing preview server and the production bundle server.
// Every visitor receives the same initial content: no user-agent sniffing or cloaking.
const axios = require("axios");

function stripOwnedHead(html) {
  return html
    .replace(/<(title|script)\b[^>]*data-seo-owned[^>]*>[\s\S]*?<\/\1>/gi, "")
    .replace(/<(meta|link)\b[^>]*data-seo-owned[^>]*>/gi, "");
}

function createSeoMiddleware(loadTemplate) {
  const base = process.env.REACT_APP_BACKEND_URL;
  if (!base) throw new Error("REACT_APP_BACKEND_URL is required");
  return async (req, res, next) => {
    if (!["GET", "HEAD"].includes(req.method)) return next();
    const path = req.path;
    const discovery = path === "/robots.txt" || path === "/sitemap.xml";
    if (!discovery && (path.startsWith("/api/") || path.startsWith("/static/") || path.startsWith("/__") || path === "/ws" || path.includes(".") || !req.accepts("html"))) return next();
    try {
      const endpoint = discovery ? `/seo${path}` : "/seo/page";
      const { data, headers } = await axios.get(`${base}/api${endpoint}`, {
        params: { path, hostname: req.hostname }, timeout: 8000,
        responseType: discovery ? "text" : "json",
      });
      res.setHeader("Cache-Control", "no-store");
      res.setHeader("X-Robots-Tag", discovery ? "noindex" : data.robots);
      if (discovery) return res.type(headers["content-type"]).send(data);
      let html = stripOwnedHead(await loadTemplate());
      html = html.replace("</head>", `${data.head}</head>`).replace(/<div id="root"><\/div>/, `<div id="root">${data.body}</div>`);
      return res.status(data.status_code).type("html").send(html);
    } catch (error) {
      console.warn("[seo] Metadata unavailable; serving a non-indexable response.");
      res.setHeader("X-Robots-Tag", "noindex, nofollow");
      res.setHeader("Cache-Control", "no-store");
      if (discovery) return res.status(503).type("text").send("Temporarily unavailable");
      // Do not return a misleading indexable 200/404 when the data service is down.
      try { return res.status(503).type("html").send(await loadTemplate()); } catch (_) { return next(error); }
    }
  };
}

module.exports = { createSeoMiddleware, stripOwnedHead };