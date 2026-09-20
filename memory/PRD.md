# Refurbished Laptop Store PRD — Bhose Technology

## Original problem statement
Build a website according to the provided second-hand laptop ecommerce document, with admin ID and password in separate secret keys so they are easy to change. No payment integration is needed; email order details to the store owner and send an order-placed email to the customer.

## Latest approved request (2026-09-20)
User could add products but not edit/delete them, needed stock management, reported no owner order emails, requested today's orders as Excel/PDF downloads, editable website name, a future custom domain, and full technology documentation. User approved these ahead of the previously pending Claude AI integration. Preferred communication: Hinglish.

### SEO request and confirmed choices (2026-09-20)
User asked to optimize SEO so searching Google for **Bhose Technology** brings the website near the top. Explained ranking cannot be guaranteed. User explicitly chose **Kolkata, West Bengal** as target area and **domain later; prepare SEO now, enable Google indexing only on final domain**.

## Personas
- Shopper looking for a trustworthy refurbished laptop.
- Store owner managing inventory, fulfilment, website branding and order notifications.

## Core requirements
- Browse/search/filter laptops, inspect details, bag and no-payment checkout.
- Required customer email; customer confirmation and owner notification emails.
- Environment-secret admin credentials; protected inventory/orders/settings workspace.
- Editable stock, product details and visibility; delete without losing past order history.
- Daily Excel/PDF downloads, editable store name, technology documentation.

## Architecture
- React frontend, FastAPI backend and MongoDB using existing environment URLs.
- Existing admin authentication: JWT bearer tokens with `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `JWT_SECRET` server-side. Password is currently an environment secret checked with constant-time hmac, not a bcrypt hash. Auth logic/credentials were not changed in this work.
- Checkout validates stock and decrements quantities atomically per product with compensating rollback on reservation/insertion failure; not a multi-document transaction.
- Product deletion: `deleted_at` plus inactive status. Removed from inventory/store; order item snapshots remain intact.
- Stock/edit writes require `expected_stock` to avoid overwriting a concurrent checkout deduction.
- Managed Resend proxy through httpx with fixed server templates and content guardrails.
- Notifications run independently per recipient in FastAPI background tasks. Status/recipient/provider ID/error persisted in MongoDB; retries use a per-recipient lease. No durable external job queue or inbox-delivery API implemented.
- Shared React settings context updates header/footer/admin branding and browser title.
- Native XLSX via openpyxl; PDF via ReportLab. Asia/Kolkata day boundaries; authenticated downloads.

## Previously implemented
- Responsive storefront with sample inventory, product details, search/filters and local browser cart.
- Customer/address checkout without online payments; order confirmation and stock protection.
- Existing admin login with lockout, overview, product creation, order status and settings.
- Initial managed email integration. Owner address was not configured.

## Implemented (2026-09-20)
- Full add/edit modal, edit/delete buttons, delete confirmation, inline stock controls, visibility/condition/specification fields and validation/error feedback.
- Concurrent-stock conflicts, zero-stock availability, actual stock counts on product detail pages.
- Backend delete reports missing IDs and hides deleted products from admin and shop. Past order snapshots unchanged.
- Confirmed owner-email root cause: `owner_email` is null. Added persistent admin warning, fixed-template test email, per-order notification status and explicit owner/customer retries.
- Emails include customer contact, delivery address, SKU, quantity, unit price, subtotal and total. Accepted messages are not resent. Failed/unconfirmed retries and tests have a one-minute cooldown. Checkout no longer claims messages were already delivered.
- Orders defaults to today (IST); date selection, Today/Refresh/all-orders list. Downloads always correspond to selected date, independent of all-orders list toggle.
- Excel Summary / Orders / Items worksheets, filters/frozen headings and formula-text escaping. PDF wrapped order/address/item content and pagination. Valid empty-day reports, no 200-order export cap.
- Website rename updates header/footer/admin/login branding, browser tab and reports. Email sender display name remains separate `EMAIL_FROM_NAME` secret per integration playbook; documentation explains keeping it aligned during rebrand.
- Refactored monolithic frontend into public/shared/admin components; existing visual identity/login flow preserved. Responsive inventory, forms, modals, report toolbar and order details.
- Added authenticated `/api/admin/documentation` and Admin → Settings download. Source `/app/backend/docs/TECH_STACK.md` covers stack, architecture, environment keys (no secret values), schemas, APIs, email setup, reports and future domain checklist.
- Updated stale `/app/memory/test_credentials.md` to match existing environment. Credentials themselves were not changed.

## Verification (2026-09-20)
- `/app/test_reports/iteration_3.json`: 12/12 backend tests passed; frontend critical flows/responsive checks passed.
- Testing agent changed only test/report files; regression suite reviewed.
- Fixed actionable frontend finding: invalid owner email now triggers deterministic `settings-error`. Browser self-retest passed and correcting field clears error.
- Managed email returned 202 with message IDs for customer and owner test notifications. Provider acceptance verified, not real-inbox delivery.
- Final `yarn build`, Python compilation and API checks passed. Final real-data XLSX parsed with original 3 orders; nonempty PDF returned valid bytes.
- Removed 6 new test orders and 20 new deleted test products; original 6 products/3 orders preserved. Store name Bhose Technology and owner_email=null restored.
- No mocked application APIs. Follow-up findings: `/app/test_reports/iteration_3_followup.md`.
- Testing agent recommended bcrypt/cookie auth migration and CORS hardening. No login failure was reproduced; these are architectural hardening recommendations. Existing environment-secret + JWT bearer model retained; no auth migration requested/performed.

## Current file map
- Backend: `server.py` (routes/models/database/auth), `email_service.py`, `email_guardrails.py`, `reports.py`, `docs/TECH_STACK.md`.
- Frontend: `App.js` (routes/cart/existing login), `lib/api.js`, `components/StoreContext.jsx`, `Brand.jsx`, `Shell.jsx`.
- Admin: `components/admin/AdminPanel.jsx`, `ProductAdmin.jsx`, `ProductForm.jsx`, `OrdersAdmin.jsx`, `OrderTable.jsx`, `SettingsAdmin.jsx`.
- Public: `pages/Storefront.jsx`, `pages/CartCheckout.jsx`; styles `App.css`, `admin.css`.
- Tests: `backend/tests/test_store_api.py`, external preview URL from current frontend env; credentials file is current.

## SEO implemented and verified (2026-09-20)
- Home title/description focused on Bhose Technology and Kolkata; unique product metadata, Open Graph/Twitter cards and Product JSON-LD with actual price, SKU, stock, INR and used condition.
- Truthful Organization service area; ComputerStore/PostalAddress only if an actual street address is configured. No fake reviews, ratings, opening hours, map coordinates or business profile claims.
- Initial HTML head and readable home/product content served identically to all visitors before React loads. This is an HTML-shell renderer, not a full React SSR/hydration rewrite. Client navigation refreshes metadata without duplicate tags or StoreContext title overrides.
- `/robots.txt` plain text and `/sitemap.xml` XML root routes supported. Preview sitemap intentionally empty, no placeholder/preview canonicals. Future domain enables canonical URLs, WebSite/Breadcrumb schema and sitemap of active nondeleted products (including out-of-stock pages).
- Preview noindex in initial meta and HTTP header; root robots permits fetching noindex instead of hiding it behind Disallow. Admin/cart/checkout/missing pages remain noindex. Direct missing/inactive/deleted product/page returns 404, metadata outage safely returns 503 + noindex.
- Server-only `PUBLIC_SITE_URL` is empty and `SEO_INDEXING_ENABLED=false`. Both environment settings plus matching request hostname are required for indexing; do not enable for preview. Invalid preview/local URL configuration rejected early.
- Admin Settings → Search appearance: target city/region, optional title/description overrides, current indexing/domain status. Visible local store content in storefront, real saved address/phone displayed when provided.
- Tech-stack document section 11 explains SEO configuration/runtime and final-domain/Search Console/local-business checklist.
- New files: `backend/seo_content.py`, `backend/seo_routes.py`, `frontend/seo-middleware.cjs`, `frontend/server.cjs`, `components/SeoManager.jsx`, `LocalStoreInfo.jsx`, `admin/SeoSettings.jsx`.
- Shared Node renderer attached to existing CRACO server. `frontend/server.cjs` also provides the renderer for compiled bundles using existing PORT/API URL environment variables; current supervisor startup/ports unchanged. A plain static server loses dynamic metadata/404/discovery behavior and preserves fallback noindex—use the renderer.
- Added explicit Express dependency using yarn. Backend/frontend restarted only for dependency/environment changes.
- `/app/test_reports/iteration_4.json`: all 12 dedicated SEO tests passed, 12 existing ecommerce regression tests passed, browser metadata navigation/settings/responsive checks passed. Python compilation and production build passed. Production-template stripping/root replacement and 503 fallback tested by agent without changing running ports.
- Testing agent wrote only dedicated test/report files, reviewed by main agent. Test-only fake database/environment values confined to unit tests; NO mocked application APIs.
- Cleaned 2 new regression test orders and 8 new deleted test products; original 6 products and 3 orders preserved. Original branding restored, owner_email null, Kolkata/West Bengal saved, SEO overrides blank; preview indexing remains disabled.
- No Google Search Console submission, ownership verification, actual indexing, rank gain or Google Business Profile creation has occurred. Those require the final domain/owner action.

## Prioritized backlog / next actions
### P0 — Owner verification
- User must save the real owner email in Admin → Settings, send a test and confirm inbox receipt. Retry older owner notifications as needed. Do not assume admin login email is owner inbox. Never leave delivered@resend.dev configured.
### P1 — Requested but deferred
- Claude AI product descriptions (prior request, postponed behind current fixes); obtain current integration playbook when resuming.
- Custom domain when user is ready. No domain purchased/connected; technical checklist documented, no guessed DNS records.
- SEO launch: configure final HTTPS origin, enable indexing only on that hostname, verify initial HTML/headers/canonicals/sitemap, then verify ownership and submit sitemap in Google Search Console. Eligible in-person business can verify Google Business Profile with real address/phone.
### P2 — Future enhancements
- Low-stock alerts (suggestion, not implemented).
- Image upload storage, customer order lookup, shipping/return policy pages.
- Auth hardening: hashed-secret rotation and explicit trusted CORS origins; any cookie migration requires deliberate design and auth playbook.
- Durable notification jobs; provider-supported delivery tracking if available.
- Coupons, reviews, analytics and staff roles.

## Known scope limitations
- Customer bag is one unit per distinct laptop; backend/admin support larger quantities.
- Cancelling changes order status only; restock manually after verifying return/cancellation.
- Sender From address is provider-managed and does not automatically change with a future website domain.
- Google decides ranking, crawl/indexing timing, snippets and rich-result eligibility. SEO does not guarantee first position. Preview is intentionally not indexable.
- Sitemap supports 49,999 product URLs plus home; add sitemap-index pagination if inventory exceeds this.