# Production image for the SafetyMAIN Next.js frontend.
#
# Build context: frontend/
#   docker build -f infrastructure/production/frontend.Dockerfile ./frontend
#
# NEXT_PUBLIC_* values are inlined by `next build`, so they are build arguments,
# not runtime environment. Never pass a secret through them: everything under
# NEXT_PUBLIC_* is visible to browser users.

FROM node:20.11.1-bookworm-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_APP_URL
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_APP_ENV=production
ENV NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL} \
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_APP_ENV=${NEXT_PUBLIC_APP_ENV} \
    NEXT_TELEMETRY_DISABLED=1

# `npm run build` runs tokens:build before next build (design tokens are generated).
RUN npm run build


FROM node:20.11.1-bookworm-slim AS runner

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./next.config.ts

USER node

EXPOSE 3100

CMD ["npm", "run", "start"]
