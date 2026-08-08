# --- Build: compila un binario estático ---
FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY main.go ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /gateway .

# --- Runtime: imagen mínima sin shell (distroless) ---
FROM gcr.io/distroless/static-debian12
COPY --from=build /gateway /gateway
EXPOSE 9000
ENTRYPOINT ["/gateway"]
