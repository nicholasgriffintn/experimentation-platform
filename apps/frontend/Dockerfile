FROM node:20-slim

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files for workspace
COPY package.json pnpm-workspace.yaml ./
COPY apps/frontend/package.json ./apps/frontend/

# Install dependencies
RUN pnpm install --no-frozen-lockfile

# Copy frontend code
COPY apps/frontend ./apps/frontend

# Set working directory to frontend app
WORKDIR /app/apps/frontend

# Start development server
CMD ["pnpm", "dev", "--host"] 