package main

import (
	"context"
	"log"
	"os"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo/options"

	"outfit-recommender/db"
	"outfit-recommender/loader"
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

	path := os.Getenv("OUTFITS_PATH")
	if path == "" {
		path = "data"
	}

	log.Printf("Reading outfits from %s...", path)
	outfits, err := loader.LoadOutfits(path)
	if err != nil {
		log.Fatalf("failed to load outfits from JSON: %v", err)
	}

	log.Printf("Found %d outfits to seed", len(outfits))

	collection := db.Database.Collection("outfits")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	for _, outfit := range outfits {
		log.Printf("Upserting outfit: %s (%s)", outfit.Name, outfit.ID)
		
		filter := bson.M{"_id": outfit.ID}
		update := bson.M{"$set": outfit}
		opts := options.Update().SetUpsert(true)
		
		_, err := collection.UpdateOne(ctx, filter, update, opts)
		if err != nil {
			log.Fatalf("failed to upsert outfit %s: %v", outfit.ID, err)
		}
	}

	log.Println("Database seeding completed successfully!")
}
