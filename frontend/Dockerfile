FROM node:22-alpine AS build
WORKDIR /web
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /web
ENV NODE_ENV=production
COPY --from=build /web/.next ./.next
COPY --from=build /web/node_modules ./node_modules
COPY --from=build /web/package.json ./package.json
COPY --from=build /web/public ./public
EXPOSE 3000
CMD ["npx", "next", "start", "-p", "3000"]
