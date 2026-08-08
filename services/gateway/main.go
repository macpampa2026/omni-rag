// Gateway de estado de omni-rag.
//
// Microservicio en Go que agrega la salud del sistema: expone su propia
// liveness y consulta la API de Python (el servicio RAG) para reportar un
// estado combinado. Demuestra comunicación entre servicios Go <-> Python.
//
// Solo usa la librería estándar (sin dependencias externas).
package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// readyResponse refleja el /health/ready de la API de Python.
type readyResponse struct {
	Status           string `json:"status"`
	Ollama           string `json:"ollama"`
	Store            string `json:"store"`
	IndexedDocuments int    `json:"indexed_documents"`
	IndexedChunks    int    `json:"indexed_chunks"`
}

type statusResponse struct {
	Gateway   string         `json:"gateway"`
	API       string         `json:"api"`
	APIDetail *readyResponse `json:"api_detail,omitempty"`
}

func getenv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func main() {
	apiURL := getenv("GATEWAY_API_URL", "http://localhost:8000")
	addr := ":" + getenv("GATEWAY_PORT", "9000")

	client := &http.Client{Timeout: 5 * time.Second}

	mux := http.NewServeMux()

	// Liveness propia del gateway.
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{
			"status": "ok", "service": "gateway",
		})
	})

	// Estado combinado: consulta la API de Python y agrega el resultado.
	mux.HandleFunc("/status", func(w http.ResponseWriter, r *http.Request) {
		resp := statusResponse{Gateway: "up", API: "down"}

		apiResp, err := client.Get(apiURL + "/health/ready")
		if err == nil {
			defer apiResp.Body.Close()
			var rr readyResponse
			if json.NewDecoder(apiResp.Body).Decode(&rr) == nil {
				resp.API = "up"
				resp.APIDetail = &rr
			}
		}

		code := http.StatusOK
		if resp.API != "up" {
			code = http.StatusServiceUnavailable
		}
		writeJSON(w, code, resp)
	})

	srv := &http.Server{Addr: addr, Handler: logRequests(mux)}

	go func() {
		log.Printf("gateway escuchando en %s (api=%s)", addr, apiURL)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("error del servidor: %v", err)
		}
	}()

	// Apagado ordenado ante SIGINT/SIGTERM (buena práctica en contenedores).
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop
	log.Println("apagando gateway...")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func logRequests(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s (%s)", r.Method, r.URL.Path, time.Since(start))
	})
}
