package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"outfit-recommender/models"
)

// OutfitRepository defines the operations to query outfits
type OutfitRepository interface {
	GetAll(ctx context.Context) ([]models.Outfit, error)
}

// MongoOutfitRepository is a MongoDB implementation of OutfitRepository
type MongoOutfitRepository struct {
	collection *mongo.Collection
}

// NewMongoOutfitRepository creates a new MongoOutfitRepository
func NewMongoOutfitRepository(db *mongo.Database) *MongoOutfitRepository {
	return &MongoOutfitRepository{
		collection: db.Collection("outfits"),
	}
}

// GetAll fetches all outfits from MongoDB
func (r *MongoOutfitRepository) GetAll(ctx context.Context) ([]models.Outfit, error) {
	cursor, err := r.collection.Find(ctx, bson.M{})
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var outfits []models.Outfit
	if err := cursor.All(ctx, &outfits); err != nil {
		return nil, err
	}
	if outfits == nil {
		outfits = []models.Outfit{}
	}
	return outfits, nil
}
