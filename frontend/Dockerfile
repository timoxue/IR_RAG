# syntax=docker/dockerfile:1
FROM node:20-alpine AS base
WORKDIR /app
COPY frontend/package*.json ./
# Use lockfile if present; otherwise fall back to npm install
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY frontend .
RUN npm run build

FROM nginx:alpine
COPY --from=base /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
