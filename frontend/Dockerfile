FROM node:20-alpine AS builder

# Accept build arguments
ARG VITE_API_BASE_URL
ARG VITE_MAPBOX_TOKEN
ARG VITE_GEMINI_API_KEY

# Set as environment variables for the build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN
ENV VITE_GEMINI_API_KEY=$VITE_GEMINI_API_KEY

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]