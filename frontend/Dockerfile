# ==============================================================================
# FoodBridge AI - Frontend Dockerfile
# Multi-stage production build for React + Vite application hosted on Nginx
# ==============================================================================

# --- BUILD STAGE ---
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency catalogs
COPY package.json package-lock.json* ./

# Install packages
RUN npm ci

# Copy full application code and build
COPY . .
RUN npm run build

# --- RUN STAGE ---
FROM nginx:stable-alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration for SPA routing
COPY ./docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
