# ==============================================================================
# Annotation Quality Guardian — Frontend Multi-Stage Dockerfile
# Stage 1: Build static React SPA assets with Node 20
# Stage 2: Serve optimized assets with Nginx Alpine
# ==============================================================================

# ── Stage 1: Build ──
FROM node:20-alpine AS builder

WORKDIR /app

# Cache package installation
COPY package*.json ./
RUN npm ci || npm install

# Copy source and build static bundle
COPY . .
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# ── Stage 2: Production Server ──
FROM nginx:1.27-alpine-slim AS runner

# Remove default nginx config
RUN rm -rf /etc/nginx/conf.d/default.conf /usr/share/nginx/html/*

# Copy built frontend assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom reverse proxy and SPA configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Built-in healthcheck for Nginx web server
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
