# Stage 1: Build Environment
FROM node:20-alpine AS build

WORKDIR /app

# Enable dynamic injection of the API base URL via Docker build context
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Leverage layer caching by copying package files first
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Production Server
FROM nginx:alpine

# Copy the generated 'dist' directory from Vite to Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Minimal Nginx configuration with Single Page Application routing fallback
RUN printf 'server {\n\
    listen 80;\n\
    location / {\n\
        root /usr/share/nginx/html;\n\
        index index.html index.htm;\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]