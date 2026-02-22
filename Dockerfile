# Build stage
FROM oven/bun:latest AS builder

WORKDIR /app

# Copy package files
COPY package.json bun.lock* ./

# Install dependencies
RUN bun install

# Copy source code
COPY . .

# Build the app
RUN bun run build

# Production stage
FROM oven/bun:latest AS production

WORKDIR /app

# Create non-root user
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Copy built app and production dependencies
COPY --from=builder /app/build ./build
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

# Set ownership
RUN chown -R appuser:appgroup /app

# Expose port
EXPOSE 3000

# Start the app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0
ENV DATABASE_PATH=/app/data/rss.db

# Fix volume permissions at runtime, then drop to non-root user
CMD ["sh", "-c", "chown -R appuser:appgroup /app/data && exec su -s /bin/sh appuser -c 'bun build/index.js'"]
