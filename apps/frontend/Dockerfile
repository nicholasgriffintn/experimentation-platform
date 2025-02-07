FROM node:20-slim

# Set working directory to frontend app from the start
WORKDIR /app/apps/frontend

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-workspace.yaml /app/
COPY apps/frontend/package.json ./

# Install workspace dependencies
WORKDIR /app
RUN pnpm install --no-frozen-lockfile

# Copy frontend code
COPY apps/frontend /app/apps/frontend

# Generate SvelteKit types
WORKDIR /app/apps/frontend
RUN pnpm svelte-kit sync

# Start development server
CMD ["pnpm", "dev", "--host"] 