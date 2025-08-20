# Frontend Dockerfile for Zib RSS Reader
FROM node:22-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci --no-audit --no-fund

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:22-alpine AS runtime

# Set working directory
WORKDIR /app

# Copy package files first for production dependencies
COPY --from=builder /app/package*.json ./

# Install only production dependencies for runtime
RUN npm ci --only=production --no-audit --no-fund

# Copy built application from builder stage
COPY --from=builder /app/build ./build

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV ORIGIN=http://localhost:3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Run the application
CMD ["node", "build/index.js"]