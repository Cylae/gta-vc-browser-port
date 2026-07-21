FROM node:22-alpine

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

ARG PUBLIC_GAME_URL=https://engine.gtavice.city:8443
ENV PUBLIC_GAME_URL=${PUBLIC_GAME_URL}

RUN pnpm build

EXPOSE 4321

HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:4321/ || exit 1

CMD ["pnpm", "preview", "--host"]
