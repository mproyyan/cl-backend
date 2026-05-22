package main

import (
	"encoding/json"
	"log"
	"os"

	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/middleware/cors"
	"github.com/gofiber/fiber/v3/middleware/logger"
	"github.com/gofiber/fiber/v3/middleware/static"

	"outfit-recommender/db"
	"outfit-recommender/handlers"
	"outfit-recommender/repository"
)

func main() {
	mongoURI := os.Getenv("MONGO_URI")
	if mongoURI == "" {
		mongoURI = "mongodb://localhost:27017"
	}

	mongoDB := os.Getenv("MONGO_DB")
	if mongoDB == "" {
		mongoDB = "outfit_recommender"
	}

	// Connect to MongoDB
	if err := db.Connect(mongoURI, mongoDB); err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}

	// Initialize Azure Storage
	if err := handlers.InitAzure(); err != nil {
		log.Fatalf("failed to initialize azure storage: %v", err)
	}

	repo := repository.NewMongoOutfitRepository(db.Database)
	h := handlers.NewHandler(repo)

	app := fiber.New(fiber.Config{
		AppName:     "Outfit Recommender API",
		JSONEncoder: json.Marshal,
		JSONDecoder: json.Unmarshal,
	})

	app.Use(logger.New())

	app.Use(cors.New(cors.Config{
		AllowOrigins: []string{"*"},
		AllowMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders: []string{"Content-Type"},
	}))

	// PAGE ENDPOINTS
	app.Get("/", func(c fiber.Ctx) error {
		return c.SendFile("./public/index.html")
	})
	app.Get("/outfits", func(c fiber.Ctx) error {
		return c.SendFile("./public/outfits.html")
	})
	app.Get("/analyzer", func(c fiber.Ctx) error {
		return c.SendFile("./public/analyzer.html")
	})
	app.Get("/outfits/create", func(c fiber.Ctx) error {
		return c.SendFile("./public/create.html")
	})
	app.Get("/outfits/edit", func(c fiber.Ctx) error {
		return c.SendFile("./public/edit.html")
	})

	// STATIC FILES
	app.Get("/*", static.New("./public"))

	app.Get("/health", h.Health)
	app.Get("/api/v1/outfits", h.GetOutfits)
	app.Get("/api/v1/outfits/:id", h.GetOutfit)
	app.Post("/api/v1/outfits", h.CreateOutfit)
	app.Put("/api/v1/outfits/:id", h.UpdateOutfit)
	app.Delete("/api/v1/outfits/:id", h.DeleteOutfit)
	app.Post("/api/v1/recommend", h.Recommend)
	app.Post("/api/v1/upload", h.UploadImage)
	app.Post("/api/v1/analyze-color", h.AnalyzeColor)

	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}

	log.Printf("Outfit Recommender API running on :%s", port)
	log.Fatal(app.Listen(":" + port))
}
