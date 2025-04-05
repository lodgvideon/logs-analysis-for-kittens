package main

import (
	"io"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func main() {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Get("/", homeHandler)
	r.Get("/about", aboutHandler)
	r.Get("/profile/{username}", profileHandler)
	r.Get("/product/{id}", productHandler)
	r.Get("/search", searchHandler)
	r.Post("/post", PostHandler)

	http.ListenAndServe(":8080", r)
}

func homeHandler(w http.ResponseWriter, r *http.Request) {
	html := `<!DOCTYPE html>
<html>
<head>
<title>Home</title>
</head>
<body>
<h1>Welcome to the Home Page</h1>
<p>This is the main page of the site.</p>
</body>
</html>`
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func aboutHandler(w http.ResponseWriter, r *http.Request) {
	html := `<!DOCTYPE html>
<html>
<head>
<title>About</title>
</head>
<body>
<h1>About Us</h1>
<p>This page contains information about our company.</p>
</body>
</html>`
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func profileHandler(w http.ResponseWriter, r *http.Request) {
	username := chi.URLParam(r, "username")
	html := `<!DOCTYPE html>
<html>
<head>
<title>Profile</title>
</head>
<body>
<h1>Profile of ` + username + `</h1>
<p>Details about user ` + username + `.</p>
</body>
</html>`
	w.Header().Set("Content-Type", "text/html")
	time.Sleep(2 * time.Second)
	w.Write([]byte(html))
}

func productHandler(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	html := `<!DOCTYPE html>
<html>
<head>
<title>Product</title>
</head>
<body>
<h1>Product ` + id + `</h1>
<p>Details about product ` + id + `.</p>
</body>
</html>`
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func searchHandler(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	html := `<!DOCTYPE html>
<html>
<head>
<title>Search</title>
</head>
<body>
<h1>Search Results</h1>
<p>You searched for: ` + query + `</p>
</body>
</html>`
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func PostHandler(w http.ResponseWriter, r *http.Request) {
	// 	query := r.URL.Query().Get("q")
	all, err := io.ReadAll(r.Body)
	if err != nil {
		w.Write([]byte(err.Error()))
	}
	w.Write(all)
	defer r.Body.Close()

}
