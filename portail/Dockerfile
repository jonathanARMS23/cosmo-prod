# Portail Cosmo — build Next.js "standalone" en 3 étages.
#
# IMPORTANT (piège déjà rencontré dans ce repo) : Coolify ne synchronise pas
# le dossier de déploiement runtime avec Git pour les ressources Docker
# Compose (seul son contexte de build éphémère l'est). Le code doit donc être
# COPY dans l'image au moment du build — jamais de bind mount du code source
# en volume runtime (voir Dockerfile.frappe à la racine du monorepo pour le
# précédent exact qui a cassé la prod pour cette raison).

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# SESSION_SECRET n'a besoin d'être défini qu'au runtime (lu par process.env
# côté serveur, jamais dans le bundle client) — une valeur factice suffit ici
# uniquement pour que le build (qui exécute next build, donc importe
# lib/session.ts) ne échoue pas sur la validation de longueur minimale.
ENV SESSION_SECRET=build-time-placeholder-not-used-at-runtime-000000
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
