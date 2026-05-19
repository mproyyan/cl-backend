package main

import (
	"encoding/json"
	"log"
	"os"

	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/middleware/cors"
	"github.com/gofiber/fiber/v3/middleware/logger"

	"outfit-recommender/handlers"
	"outfit-recommender/loader"
)

func main() {
	path := os.Getenv("OUTFITS_JSON")
	if path == "" {
		path = "data/outfits.json"
	}

	outfits, err := loader.LoadOutfits(path)
	if err != nil {
		log.Fatalf("failed to load outfits: %v", err)
	}
	log.Printf("Loaded %d outfits from %s", len(outfits), path)

	h := handlers.NewHandler(outfits)

	app := fiber.New(fiber.Config{
		AppName:     "Outfit Recommender API",
		JSONEncoder: json.Marshal,
		JSONDecoder: json.Unmarshal,
	})

	app.Use(logger.New())
	app.Use(cors.New(cors.Config{
		AllowOrigins: []string{"*"},
		AllowMethods: []string{"GET", "POST", "OPTIONS"},
		AllowHeaders: []string{"Content-Type"},
	}))

	app.Get("/health", h.Health)
	app.Get("/api/v1/outfits", h.GetOutfits)
	app.Post("/api/v1/recommend", h.Recommend)

	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}
	log.Printf("Outfit Recommender API running on :%s", port)
	log.Fatal(app.Listen(":" + port))
}
