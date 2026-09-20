# Authentication Testing Playbook

1. POST `/api/auth/login` with the admin email and password from `/app/memory/test_credentials.md`.
2. Confirm the response includes a bearer token and `role: admin`.
3. Call `/api/auth/me` with `Authorization: Bearer <token>` and confirm the admin identity.
4. Call `/api/admin/products` without a token and confirm a 401 response.
5. Call `/api/admin/products` with the token and confirm the product list is returned.