# Stage 1: Build stage
FROM golang:1.25-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git

WORKDIR /app

# Copy dependency manifests
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the application source code
COPY . .

# Build the API server and the seeder binaries
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o api-server main.go
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o seeder cmd/seed/main.go

# Stage 2: Runtime stage
FROM alpine:latest

RUN apk add --no-cache ca-certificates

WORKDIR /app

# Copy the compiled binaries
COPY --from=builder /app/api-server .
COPY --from=builder /app/seeder .

# Copy static assets and data
COPY public ./public
COPY data ./data

# Expose port
EXPOSE 3000

# Set default env variables (can be overridden by compose)
ENV PORT=3000
ENV MONGO_URI=mongodb://localhost:27017
ENV MONGO_DB=outfit_recommender

# Set the command to run the API server
CMD ["./api-server"]
