# Use the official Golang image as the base image
FROM golang:1.23.1 as builder

# Set the working directory
WORKDIR /app

# Copy the Go modules manifests
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the application source code
COPY . ./

# Build the application
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o chi_app

# Use a minimal image for the final build
FROM debian:bullseye-slim

# Set the working directory
WORKDIR /app

# Copy the binary from the builder
COPY --from=builder ./app/chi_app ./

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["./chi_app"]
