# Laptop Lab Store PRD

## Original problem statement
Build a website according to the provided second-hand laptop ecommerce document, with the admin ID and password in separate secret keys so they are easy to change. No payment integration is needed; email order details to the store owner and send an order-placed email to the customer.

## Architecture decisions
- React frontend with FastAPI backend and MongoDB, using the existing environment URLs.
- Admin authentication uses JWT with `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `JWT_SECRET` stored server-side.
- Orders are created without payment and inventory is decremented atomically by quantity validation.
- Transactional emails use Emergent managed Resend proxy with server-side templates and guardrails.
- Store content and owner email are editable from the admin Settings tab.

## Personas
- Shopper looking for a trustworthy refurbished laptop.
- Store owner managing stock, orders, copy, and notification email.

## Core requirements
- Browse, search, filter, inspect and add unique laptops to a bag.
- Required customer email at checkout and no payment step.
- Customer confirmation email and optional owner notification email.
- Protected admin dashboard, product creation, order status updates, and editable settings.

## Implemented (2025-02-14)
- Professional responsive Laptop Lab storefront with sample inventory.
- Product detail, cart, no-payment checkout, confirmation state, and inventory protection.
- Admin login, dashboard, product add flow, order status management, and settings editor.
- Resend managed email integration with customer and owner order templates.

## Prioritized backlog
- P0: Add the real store owner email in Admin > Settings and verify a delivered email.
- P1: Add image upload storage and product edit/archive controls.
- P1: Add customer order lookup and shipping/return policy pages.
- P2: Add coupons, reviews, analytics, and staff roles.