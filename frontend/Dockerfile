# ---------------------------------------------------------------------------
# FleetFlow — Frontend Dockerfile (multi-stage build)
# ---------------------------------------------------------------------------
# Stage 1: Build  — Node.js builds the Vite/React application.
# Stage 2: Serve  — Nginx serves the compiled static assets and reverse-proxies
#                   API + WebSocket traffic to the backend service.
#
# VITE_API_URL is injected at BUILD TIME. Leave it empty for Docker/production
# so the browser uses same-origin URLs (Nginx proxies to FastAPI).
# For local Vite dev, frontend/.env still uses http://127.0.0.1:8000.
# ---------------------------------------------------------------------------

# ---- Stage 1: Build -------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Same-origin by default. Override only if the API is on a separate public URL.
ARG VITE_API_URL=
ARG VITE_API_BASE_URL=

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

COPY . .

RUN npm run build

# ---- Stage 2: Serve -------------------------------------------------------
FROM nginx:1.27-alpine AS production

RUN rm -rf /usr/share/nginx/html/*

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
