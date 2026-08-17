# ---------------------------------------------------------------------------
# FleetFlow — Frontend Dockerfile (multi-stage build)
# ---------------------------------------------------------------------------
# Stage 1: Build  — Node.js builds the Vite/React application.
# Stage 2: Serve  — Nginx serves the compiled static assets.
#
# VITE_API_BASE_URL is injected at BUILD TIME by docker-compose so that the
# Vite bundler can bake the correct backend URL into the static bundle.
# VITE_ORS_API_KEY is also accepted for the OpenRouteService integration.
# Do NOT hardcode localhost — use the ARG/ENV mechanism below.
# ---------------------------------------------------------------------------

# ---- Stage 1: Build -------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Accept the backend URL as a build argument; docker-compose passes it via
# the `args:` section of the build config.
# Default is intentionally empty so that a missing variable causes a
# visible problem at runtime (Vite will warn) rather than silently using
# localhost (which breaks in a container environment).
ARG VITE_API_BASE_URL
ARG VITE_ORS_API_KEY

# Expose build args as environment variables so Vite picks them up.
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_ORS_API_KEY=$VITE_ORS_API_KEY

# Install dependencies (using package-lock.json for reproducible installs).
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

# Copy the rest of the frontend source.
COPY . .

# Build the production bundle into /app/dist
RUN npm run build

# ---- Stage 2: Serve -------------------------------------------------------
FROM nginx:1.27-alpine AS production

# Remove the default Nginx welcome page.
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled assets from the build stage.
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy a custom Nginx config that handles React Router (history API fallback).
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
