# syntax=docker/dockerfile:1
FROM node:22-slim AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite inlines VITE_* variables into the built JS at build time, not at
# container start -- they have to arrive as build args, not runtime env.
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_DASHBOARD_REPOSITORY=secureops
ARG VITE_DASHBOARD_GATE_MODE=advisory
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_DASHBOARD_REPOSITORY=$VITE_DASHBOARD_REPOSITORY \
    VITE_DASHBOARD_GATE_MODE=$VITE_DASHBOARD_GATE_MODE

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
