# syntax=docker/dockerfile:1

# ---------- 1) Build the React bundle ----------
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json yarn.lock* ./
# Emergent's dev-only packages (overlay / visual-edits) are not needed for a production build
RUN node -e "const fs=require('fs');const p=JSON.parse(fs.readFileSync('package.json'));for(const k of ['@emergentbase/overlay','@emergentbase/visual-edits'])delete p.devDependencies[k];fs.writeFileSync('package.json',JSON.stringify(p,null,2))" \
 && yarn install --network-timeout 100000

COPY . .
# Public URL of the site: the browser calls  <this>/api/...  (baked into the bundle at build time)
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL \
    GENERATE_SOURCEMAP=false \
    CI=false \
    NODE_ENV=production
RUN test -n "$REACT_APP_BACKEND_URL" && yarn build

# ---------- 2) Tiny runtime: Express server with SEO middleware ----------
FROM node:20-alpine
ENV NODE_ENV=production PORT=3000
WORKDIR /srv

RUN npm init -y >/dev/null && npm install --omit=dev express@4 axios@1.18.0 dotenv@16.4.5 && npm cache clean --force
COPY --from=build /app/build ./build
COPY server.cjs seo-middleware.cjs ./

USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('net').connect(3000,'127.0.0.1').on('connect',()=>process.exit(0)).on('error',()=>process.exit(1))"

# At runtime REACT_APP_BACKEND_URL must point at the backend (set in docker-compose: http://backend:8001)
CMD ["node", "server.cjs"]
