# DataPilotFlow Dashboard
# Frontend application built with Vite + React
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY datapilotflow-dashboard/package.json datapilotflow-dashboard/package-lock.json ./

# Install dependencies
# Use --legacy-peer-deps to handle Vite version conflicts with Storybook
RUN npm ci --legacy-peer-deps

# Copy source code
COPY datapilotflow-dashboard ./

# Copy Dashboard service configuration
COPY docker/services/dashboard/.env .env

# Build the application
RUN npx tsc && npx vite build

# Production stage - serve with lightweight server
FROM node:20-alpine

WORKDIR /app

# Install serve to run the static files
RUN npm install -g serve

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Regenerates runtime-config.js from API_BASE_URL at container startup, so
# one image works against any API host without a rebuild — see the script
# for details.
COPY docker/services/dashboard/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose dashboard port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q -O- http://localhost:3000/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["serve", "-s", "dist", "-l", "3000"]
