package db

import (
	"context"
	"fmt"
	"log"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

var Client *mongo.Client
var Database *mongo.Database

// Connect initializes a connection to MongoDB with retry logic
func Connect(uri, dbName string) error {
	var client *mongo.Client
	var err error
	
	ctx := context.Background()

	// Try to connect up to 5 times with a 2-second delay
	for i := 1; i <= 5; i++ {
		log.Printf("Connecting to MongoDB (attempt %d/5)...", i)
		client, err = mongo.Connect(ctx, options.Client().ApplyURI(uri))
		if err == nil {
			// Ping database to confirm connection
			pingCtx, cancel := context.WithTimeout(ctx, 3*time.Second)
			err = client.Ping(pingCtx, nil)
			cancel()
			if err == nil {
				log.Println("Successfully connected to MongoDB")
				Client = client
				Database = client.Database(dbName)
				return nil
			}
		}
		
		log.Printf("Failed to connect to MongoDB: %v. Retrying in 2 seconds...", err)
		time.Sleep(2 * time.Second)
	}

	return fmt.Errorf("could not connect to MongoDB after 5 attempts: %w", err)
}
