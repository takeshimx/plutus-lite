FROM node:24-slim AS build
WORKDIR /app

# NEXT_PUBLIC_* はビルド時に画面のコードへ埋め込まれる。値は Cloud Build のトリガーから渡す
ARG NEXT_PUBLIC_FIREBASE_API_KEY
ARG NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ARG NEXT_PUBLIC_FIREBASE_PROJECT_ID
ARG NEXT_PUBLIC_API_BASE_URL

COPY package.json package-lock.json ./
# 手元のビルドで社内プロキシやウイルス対策ソフトの証明書が必要な場合だけ、--secret id=extra_ca で渡す。
# イメージには残らない。CI と Cloud Build では渡さない
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -f /run/secrets/extra_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/extra_ca; fi; \
    npm ci
COPY . .
RUN npm run build

FROM node:24-slim
WORKDIR /app
ENV NODE_ENV=production PORT=8080 HOSTNAME=0.0.0.0

COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static

USER node
EXPOSE 8080
CMD ["node", "server.js"]
