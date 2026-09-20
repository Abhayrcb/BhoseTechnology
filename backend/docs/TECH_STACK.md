# Website Technical Documentation

## 1. Project overview
This is a second-hand/refurbished laptop store, currently named **Bhose Technology**. The owner can change the website name in Admin → Settings without editing source code. Customers browse laptops and place orders without making an online payment. The owner manages inventory and fulfilment in a private admin workspace.

### What is implemented
- Product listing, search, brand/category filters and laptop details.
- Shopping bag, customer/address checkout, order confirmation; no payment gateway.
- Private admin login using server-side environment credentials.
- Add, edit, hide, delete and update stock for laptops.
- Orders with customer details, items, delivery address and fulfilment status.
- Customer and store owner transactional emails, per-recipient send status and manual retry.
- Daily Excel and PDF downloads, using **Asia/Kolkata (IST)** calendar days.
- Editable store name, homepage copy, owner email, phone, address and policies.
- This document is downloadable from Admin → Settings.

## 2. Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 19 | Storefront and admin interface |
| Routing | React Router 7 | Shop, product detail, cart, checkout and admin routes |
| Build | Create React App / react-scripts 5 with CRACO | Development server and optimized frontend build |
| Styling | CSS, Tailwind CSS 3 | Responsive layouts and shared UI styles |
| UI components | shadcn/ui with Radix Dialog | Accessible product editor and confirmation dialogs |
| Icons | lucide-react | Inventory, order, download and navigation icons |
| HTTP client | Axios | Calls to the FastAPI service |
| Backend | Python 3.11, FastAPI | Validated API endpoints and business logic |
| Server | Uvicorn, supervisor | Managed application processes |
| Validation | Pydantic 2, email-validator | Product, stock, order and settings validation |
| Database | MongoDB | Persistent products, orders, settings, login attempts |
| Database driver | Motor / PyMongo | Asynchronous MongoDB operations |
| Authentication | PyJWT, Python hmac | Admin bearer tokens and constant-time secret comparison |
| Email | Managed Resend integration, httpx | Transactional order/test messages |
| Excel | openpyxl | Native .xlsx workbook creation |
| PDF | ReportLab | Printable daily order reports |
| Timezone | zoneinfo / tzdata | Correct India date boundaries |
| Configuration | python-dotenv and environment variables | Server-side secrets and service URLs |
| Tests | pytest, HTTP checks, browser automation | Backend and user-flow verification |

The package manifests contain additional starter-template dependencies. Only actively used technologies are listed above. Exact installed versions are in `frontend/package.json`, `frontend/yarn.lock`, and `backend/requirements.txt`.

## 3. Architecture and files

```text
frontend/src/
  App.js                          Routes, cart state and existing admin login
  App.css, admin.css              Storefront and responsive admin styling
  lib/api.js                     API client, currency/errors/date helpers
  components/StoreContext.jsx     Shared store settings and browser title
  components/Brand.jsx            Dynamic website branding
  components/Shell.jsx            Header and footer
  components/admin/
    AdminPanel.jsx               Workspace navigation and overview
    ProductAdmin.jsx             Inventory actions and stock controls
    ProductForm.jsx              Add/edit form
    OrderTable.jsx               Order details, email status and retry
    OrdersAdmin.jsx              Date filter, Excel/PDF download
    SettingsAdmin.jsx            Settings, test email, document download
  pages/Storefront.jsx            Catalogue and product details
  pages/CartCheckout.jsx          Bag and checkout
backend/
  server.py                      APIs, authentication, database and stock logic
  email_service.py               Fixed order/test templates, sending and send status
  email_guardrails.py            Email content/link safety checks
  reports.py                     IST filters, XLSX/PDF generation
  docs/TECH_STACK.md              This document
```

The browser calls the configured backend URL with `/api` routes. The backend alone connects to MongoDB and the email service. Secrets are never sent to the browser.

## 4. Configuration and secrets

### Backend `.env`
- `MONGO_URL`: MongoDB connection URI.
- `DB_NAME`: Existing database name; do not change it unintentionally.
- `ADMIN_EMAIL`: Admin login ID.
- `ADMIN_PASSWORD`: Admin login secret. Currently compared directly using constant-time `hmac.compare_digest`; it is not a bcrypt hash. Keep the environment private and use a strong password.
- `JWT_SECRET`: Signing secret for admin tokens, which expire after 12 hours.
- `CORS_ORIGINS`: Allowed frontend origins. Explicit trusted origins are recommended for a custom website URL.
- `EMERGENT_EMAIL_KEY`: Server-only managed email integration key.
- `EMAIL_FROM_NAME`: Email sender display name. Currently Bhose Technology. When rebranding, change this secret to the same business name as the website so the sender label remains aligned.
- `EMAIL_REPLY_TO`: Optional owner-controlled reply inbox; saved owner email is used where available.

### Frontend `.env`
- `REACT_APP_BACKEND_URL`: Public backend URL, used by all API calls.

Do not put keys, passwords or database URLs into frontend code or public documentation. Admin account secrets are separate from the owner notification inbox. Changing the owner email does **not** change the admin login. Restart the appropriate service after changing environment variables; normal code changes use hot reload.

## 5. Database records

### products
`product_id`, `sku`, `title`, `brand`, `category`, `price`, `compare_at_price`, `processor`, `ram_gb`, `storage_type`, `storage_gb`, `display`, `gpu`, `battery_health`, `operating_system`, `condition_grade`, `condition_description`, `warranty_months`, `stock_quantity`, `image_url`, `status`, `created_at`, `updated_at`, optional `deleted_at`.

Deletion is a soft delete: the item disappears from inventory and the public shop. Historical order snapshots remain intact. Hidden products remain editable. Zero-stock products are not listed for purchase. Stock edits include the previous stock value to prevent overwriting a simultaneous checkout deduction.

### orders
`order_id`, `order_number`, customer name/email/phone, address/city/pincode, item snapshots (product ID/title/SKU/unit price/quantity), `total`, `status`, `created_at`, `notifications.owner`, `notifications.customer`.

An order saves its item details and prices at checkout. Editing/deleting a laptop later does not change old orders. Checkout validates available stock and decrements quantities atomically per product, with compensating rollback if reservation/order insertion fails. This is not a MongoDB multi-document transaction.

### settings
The `key=store` document stores website content and owner email. Internal email-test timestamps enforce a send cooldown and are not exposed as public settings.

### login_attempts
Tracks failed admin attempts and a temporary lockout after five failed attempts. No customer registration is required.

## 6. Important API routes

| Method | Route | Access / purpose |
|---|---|---|
| POST | `/api/auth/login` | Admin login |
| GET | `/api/auth/me` | Current admin session |
| GET | `/api/products` | Public available laptops |
| GET | `/api/products/{id}` | Public active product details |
| POST | `/api/orders` | Place an order; queue notifications |
| GET | `/api/settings` | Public store settings |
| GET / POST | `/api/admin/products` | List / create inventory |
| PUT | `/api/admin/products/{id}` | Edit product; requires `expected_stock` |
| PATCH | `/api/admin/products/{id}/stock` | Set stock; requires `stock_quantity` and `expected_stock` |
| DELETE | `/api/admin/products/{id}` | Remove product from inventory/shop |
| GET | `/api/admin/orders?date=YYYY-MM-DD` | Orders for an IST date; omit date for all |
| PATCH | `/api/admin/orders/{id}?status=...` | Set order fulfilment status |
| GET | `/api/admin/orders/export?date=YYYY-MM-DD&format=xlsx` | Daily Excel report; `pdf` also supported |
| POST | `/api/admin/orders/{id}/retry-email?recipient=owner` | Retry one stored recipient; customer also supported |
| POST | `/api/admin/email/test` | Fixed test message to saved owner address |
| PUT | `/api/admin/settings` | Save store settings |
| GET | `/api/admin/documentation` | Download this document |

All `/api/admin/*` routes require the existing admin bearer token.

## 7. Owner email setup and troubleshooting

1. Open Admin → Settings.
2. Enter the owner's **real receiving email address** and save.
3. Click **Send test email** and check that inbox.
4. Open Admin → Orders → order details for customer/owner notification status.
5. Use **Retry email** for a missing/failed notification after correcting configuration.

The previous missing-owner-email issue was traced to `owner_email` being empty. The admin now displays a warning rather than silently omitting the notification. The owner receives customer contact information, delivery address, quantities, unit prices and total.

Status meanings:
- `pending`: queued for sending.
- `sending`: a send attempt is in progress.
- `accepted`: the provider returned a message ID. This does **not** prove inbox delivery.
- `not_configured`: no owner email saved.
- `failed`: rejected by provider or content validation.
- `unknown`: provider acceptance could not be confirmed; check the inbox before retrying to avoid duplicates.
- Older orders show **Not tracked** until an explicit send attempt.

Successful accepted messages are not resent by the retry button. Concurrent sends use a database lease. Test messages and failed/unconfirmed retries have a one-minute cooldown. Sending is background work, not a durable external job queue; a stopped process may leave pending/sending notifications requiring an explicit retry. No unsupported delivery webhook or delivery tracking API is fabricated.

Sender email address/domain is managed by the email service. Connecting a website domain does not automatically change that sender address. There is no SMTP integration or payment gateway.

## 8. Daily reports

Admin → Orders defaults to **Today**. Select another date for a previous day's report, then click **Excel** or **PDF**. Reports include all matching orders, including cancelled orders; the summary separately shows non-cancelled value. Cancelled order status does not automatically restock inventory—adjust stock manually after verifying the return/cancellation.

- A day means 00:00 inclusive to the next 00:00 exclusive in **Asia/Kolkata**, not the browser's timezone.
- Excel contains Summary, Orders and Items worksheets.
- PDF contains order number, date/status, customer details, complete delivery address, items, quantities, unit prices and totals.
- Downloading a date with no orders produces a valid empty report.
- Excel text is protected against spreadsheet-formula injection.
- Reports include personal information; only share them with authorized store staff.

## 9. Website name and a future custom domain

Website name is editable in Admin → Settings → Store name. It updates the header, footer, admin branding, browser title and reports. The email sender display name is a separate backend environment setting, `EMAIL_FROM_NAME`, described above.

A website name is not a domain registration or DNS connection. No domain has been purchased or connected by this work. When a real domain is ready, the technical checklist is:
- Retain routing for the frontend and `/api` backend paths.
- Use the actual HTTPS website/API addresses in environment configuration.
- Update allowed CORS origins to trusted website origins.
- Verify HTTPS, product images, login, checkout, order emails and downloads at the new address.
- Follow the hosting platform's current verified domain/DNS instructions; do not guess DNS records.

## 10. Development and maintenance

- Frontend dependencies: use `yarn`, not npm. Run `yarn build` for a production compilation check.
- Backend dependencies: install from `requirements.txt` in a Python virtual environment.
- Keep the existing managed ports: frontend 3000; backend 8001.
- MongoDB access is configured only through the existing environment keys.
- Image URLs are currently used; file uploads/object storage are **not** implemented.
- Cart state is local to the browser, with one unit per distinct laptop in the customer bag. Admin/backend stock can represent multiple units.
- Claude AI product descriptions remain a separate pending feature; no AI generation is currently wired into product editing.
- Payment integration, reviews, coupons, customer accounts and staff roles are not part of this implementation.

## 11. Kolkata SEO setup (2026-09-20)

The owner confirmed **Kolkata, West Bengal** as the target market and said the final domain will be added later. SEO is prepared; this preview is deliberately **not indexable**. No Google first-position promise or submission has been made.

### Implemented SEO
- Brand + Kolkata-focused home title and description; unique product titles/descriptions.
- Initial HTML metadata and readable home/product content served before JavaScript, identically for every visitor. This is an HTML-shell renderer, not a full React SSR/hydration migration.
- Open Graph and Twitter sharing metadata, product images on product pages.
- JSON-LD Organization / WebSite (when final URL exists), Product offers in INR, real stock availability and used condition. No fake ratings, reviews, business hours or street addresses.
- Organization uses Kolkata/West Bengal service area; ComputerStore with PostalAddress is emitted only after a real street address is saved. Missing contact/address data must be provided truthfully for stronger local-business eligibility.
- Root `/robots.txt` and `/sitemap.xml`, plus canonical URLs and breadcrumbs prepared for the real domain. The preview sitemap is intentionally empty: no preview or placeholder URLs.
- Admin/cart/checkout/missing products are noindex. Direct missing product/page requests return HTTP 404; SEO-service outages return 503 + noindex rather than a false indexable success.
- Settings → Search appearance: city, state, optional search-title/description overrides and indexing status.
- Visible local business copy plus saved address/phone on the storefront.

### SEO configuration
- Backend `PUBLIC_SITE_URL`: empty until a real domain is ready; later set to the bare HTTPS origin (no path/query/port).
- Backend `SEO_INDEXING_ENABLED`: currently `false`. Set to `true` only after the final domain is live and validated.
- Both flags and the **actual request hostname** must match for a page to be indexable. Visiting a preview hostname remains noindex even if final-domain indexing is enabled.
- Do not remove noindex only using JavaScript: Google may skip rendering pages that already have noindex in their initial HTML.
- Preview robots allows fetching the noindex response; blocking crawl entirely can prevent Google from seeing noindex and can leave URL-only entries. The HTTP `X-Robots-Tag` and initial HTML robots meta both prohibit preview indexing.

### SEO files and runtime
- `backend/seo_content.py`: metadata, escaped initial HTML and structured data.
- `backend/seo_routes.py`: `/api/seo/config`, `/api/seo/page`, `/api/seo/robots.txt`, `/api/seo/sitemap.xml`.
- `frontend/seo-middleware.cjs`: initial HTML/discovery-file renderer using only the configured backend URL.
- `frontend/craco.config.js`: same renderer attached to the existing frontend server.
- `frontend/server.cjs`: renderer for an already compiled frontend bundle (`yarn build`, then `node server.cjs`, using existing `PORT` and `REACT_APP_BACKEND_URL`). It is provided but does not replace the current supervisor service automatically.
- `frontend/src/components/SeoManager.jsx`: updates metadata during React navigation and saved-branding changes.
- `LocalStoreInfo.jsx`, `admin/SeoSettings.jsx`: local content and admin search settings.
- Do not serve `build/index.html` from a plain static server without this renderer: it intentionally contains a noindex fallback, and direct dynamic metadata/sitemap/HTTP-status behavior would be lost.

### Steps once the final domain is ready
1. Confirm the domain resolves correctly with HTTPS, frontend routes and `/api` routes working.
2. Configure the final origin and enable indexing, restart backend, then inspect actual HTML and robots/sitemap on that hostname. Check that admin/checkout stay noindex and product stock data is correct.
3. Verify ownership in Google Search Console and submit the root sitemap. Use URL Inspection for the home page and representative products; no account integration is currently installed.
4. If the business is eligible (real in-person customer contact), create/verify its Google Business Profile with consistent real business name, address, phone and website. Online-only businesses are not eligible merely because a service area was entered.
5. Publish accurate laptop photos/descriptions and earn genuine customer reviews and reputable local mentions. Do not create fake ratings or paid-link schemes.
6. Track branded queries (Bhose Technology) and local queries (refurbished laptops Kolkata) in Search Console. Google controls crawl timing, indexing, snippets, rich-result eligibility and ranking; results are not guaranteed.

Sitemap currently supports up to 49,999 active product URLs plus the home page. Add sitemap-index pagination if inventory grows beyond that.