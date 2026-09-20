# Follow-up verification — 2026-09-20

## Resolved
- Settings native email validation now also sets a deterministic in-app error through the form's invalid event. Browser verification confirmed `settings-error` displays for `invalid-email` and clears after correction. Invalid data was not saved.
- Final frontend build succeeded. Final XLSX export was parsed with all 3 original orders and the expected 3 worksheets; nonempty PDF export returned a valid 2,825-byte PDF.

## Email evidence
- Live provider accepted test customer messages and test owner messages with message IDs, visible in stored notification results and backend HTTP 202 logs.
- Example isolated test order `e1e62d00-b8e2-4b80-aa00-b9f551a09c63`: owner accepted (`01a0bd15-6ea1-763a-ac9e-a95ad6ec4733`), customer accepted (`01a0bd15-6e87-7298-9f8e-47a6cfc963cc`).
- These prove provider acceptance, not real-inbox delivery. The real owner address remains unset and must be supplied in Settings by the owner.

## Data cleanup
- Removed only 6 newly created test orders addressed to delivered@resend.dev and 20 newly created soft-deleted TEST_ products from this iteration.
- Original 6 products and 3 orders preserved; original branding and owner_email=null restored. No real customer test emails were sent.

## Auth/CORS recommendations disposition
- No auth failure was reproduced: login, token authorization and lockout tests passed.
- The bcrypt/seed rotation and httpOnly-cookie recommendations in iteration_3 are architecture recommendations for a different auth model. The project intentionally retains the previously requested environment-secret admin login and existing JWT bearer session in this task; no authentication code or credentials were changed.
- Wildcard CORS is used with allow_credentials=false and bearer tokens, not credentialed cookie authentication. Explicit-origin tightening is recorded as future hardening, not an unresolved failure of the implemented controls.

## Final status
- Requested inventory/stock/reports/branding/documentation controls verified.
- Settings error feedback fixed and verified.
- Owner real-address configuration/inbox verification remains a user action; no flow is mocked.