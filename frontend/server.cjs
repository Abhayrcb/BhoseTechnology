require("dotenv").config();
const express = require("express");
const path = require("path");
const fs = require("fs/promises");
const { createSeoMiddleware } = require("./seo-middleware.cjs");

// Optional server for the compiled bundle; uses the same SEO renderer as preview.
// Run after yarn build, with the existing PORT and API URL environment variables.
if (!process.env.PORT) throw new Error("PORT is required");
const app = express();
const build = path.join(__dirname, "build");
app.use(createSeoMiddleware(() => fs.readFile(path.join(build, "index.html"), "utf8")));
app.use(express.static(build, { index: false }));
app.use((req, res) => res.status(404).set("X-Robots-Tag", "noindex").send("Not found"));
app.listen(Number(process.env.PORT), "0.0.0.0");