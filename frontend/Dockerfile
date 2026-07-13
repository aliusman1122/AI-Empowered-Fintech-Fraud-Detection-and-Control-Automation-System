# Stage 1: Build Environment
FROM node:18-alpine AS build

WORKDIR /app

# Enable dynamic injection of the API base URL via Docker build context
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

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
RUN echo "server { \\
    listen 80; \\
    location / { \\
        root /usr/share/nginx/html; \\
        index index.html index.htm; \\
        try_files \$uri \$uri/ /index.html; \\
    } \\
}" > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
