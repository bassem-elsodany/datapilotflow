# DataPilotFlow Dashboard
# Frontend application built with Vite + React
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY datapilotflow-dashboard/package.json datapilotflow-dashboard/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY datapilotflow-dashboard ./

# Build the application
RUN npm run build

# Production stage - serve with lightweight server
FROM node:20-alpine

WORKDIR /app

# Install serve to run the static files
RUN npm install -g serve

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Expose dashboard port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q -O- http://localhost:3000/ || exit 1

# Start the application
CMD ["serve", "-s", "dist", "-l", "3000"]
