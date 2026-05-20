package repository

import (
	"context"

	"github.com/google/uuid"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"outfit-recommender/models"
)

// OutfitRepository defines the operations to query and manage outfits
type OutfitRepository interface {
	GetAll(ctx context.Context) ([]models.Outfit, error)
	GetByID(ctx context.Context, id string) (*models.Outfit, error)
	Create(ctx context.Context, outfit *models.Outfit) error
	Update(ctx context.Context, id string, outfit *models.Outfit) error
	Delete(ctx context.Context, id string) error
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

// GetByID fetches a single outfit by its ID
func (r *MongoOutfitRepository) GetByID(ctx context.Context, id string) (*models.Outfit, error) {
	var outfit models.Outfit
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&outfit)
	if err != nil {
		return nil, err
	}
	return &outfit, nil
}

// Create inserts a new outfit into MongoDB
func (r *MongoOutfitRepository) Create(ctx context.Context, outfit *models.Outfit) error {
	if outfit.ID == "" {
		// We import "github.com/google/uuid" to generate string ID
		outfit.ID = uuid.NewString()
	}
	_, err := r.collection.InsertOne(ctx, outfit)
	return err
}

// Update updates an existing outfit in MongoDB
func (r *MongoOutfitRepository) Update(ctx context.Context, id string, outfit *models.Outfit) error {
	outfit.ID = id // Ensure ID remains consistent
	filter := bson.M{"_id": id}
	update := bson.M{"$set": outfit}
	res, err := r.collection.UpdateOne(ctx, filter, update)
	if err != nil {
		return err
	}
	if res.MatchedCount == 0 {
		return mongo.ErrNoDocuments
	}
	return nil
}

// Delete removes an outfit from MongoDB
func (r *MongoOutfitRepository) Delete(ctx context.Context, id string) error {
	filter := bson.M{"_id": id}
	res, err := r.collection.DeleteOne(ctx, filter)
	if err != nil {
		return err
	}
	if res.DeletedCount == 0 {
		return mongo.ErrNoDocuments
	}
	return nil
}

