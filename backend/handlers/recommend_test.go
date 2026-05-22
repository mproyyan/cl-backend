package handlers_test

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http/httptest"
	"testing"

	"github.com/gofiber/fiber/v3"
	"go.mongodb.org/mongo-driver/mongo"
	"outfit-recommender/handlers"
	"outfit-recommender/models"
)

type MockOutfitRepository struct {
	Outfits []models.Outfit
}

func (m *MockOutfitRepository) GetAll(ctx context.Context) ([]models.Outfit, error) {
	return m.Outfits, nil
}

func (m *MockOutfitRepository) GetByID(ctx context.Context, id string) (*models.Outfit, error) {
	for _, o := range m.Outfits {
		if o.ID == id {
			return &o, nil
		}
	}
	return nil, mongo.ErrNoDocuments
}

func (m *MockOutfitRepository) Create(ctx context.Context, outfit *models.Outfit) error {
	m.Outfits = append(m.Outfits, *outfit)
	return nil
}

func (m *MockOutfitRepository) Update(ctx context.Context, id string, outfit *models.Outfit) error {
	for i, o := range m.Outfits {
		if o.ID == id {
			m.Outfits[i] = *outfit
			return nil
		}
	}
	return mongo.ErrNoDocuments
}

func (m *MockOutfitRepository) Delete(ctx context.Context, id string) error {
	for i, o := range m.Outfits {
		if o.ID == id {
			m.Outfits = append(m.Outfits[:i], m.Outfits[i+1:]...)
			return nil
		}
	}
	return mongo.ErrNoDocuments
}

func TestRecommend(t *testing.T) {
	app := fiber.New()
	
	outfits := []models.Outfit{
		{
			ID:     "1",
			Name:   "Test Outfit",
			Gender: "unisex",
			Items: models.Items{
				Top: models.Item{Hex: "#FFFFFF"},
			},
		},
	}
	
	repo := &MockOutfitRepository{Outfits: outfits}
	h := handlers.NewHandler(repo)
	app.Post("/api/v1/recommend", h.Recommend)

	tests := []struct {
		name       string
		reqBody    models.RecommendRequest
		statusCode int
	}{
		{
			name: "Valid request",
			reqBody: models.RecommendRequest{
				BestColors:  []string{"#FFFFFF"},
				AvoidColors: []string{"#000000"},
				Gender:      "unisex",
			},
			statusCode: 200,
		},
		{
			name: "Invalid hex best",
			reqBody: models.RecommendRequest{
				BestColors: []string{"invalid"},
			},
			statusCode: 400,
		},
		{
			name: "Invalid hex avoid",
			reqBody: models.RecommendRequest{
				AvoidColors: []string{"#FFFFF"},
			},
			statusCode: 400,
		},
		{
			name: "Invalid gender",
			reqBody: models.RecommendRequest{
				Gender: "unknown",
			},
			statusCode: 400,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			body, _ := json.Marshal(tt.reqBody)
			req := httptest.NewRequest("POST", "/api/v1/recommend", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			
			resp, err := app.Test(req)
			if err != nil {
				t.Fatalf("Failed to execute request: %v", err)
			}
			if resp.StatusCode != tt.statusCode {
				b, _ := io.ReadAll(resp.Body)
				t.Errorf("Expected status %d, got %d, body: %s", tt.statusCode, resp.StatusCode, string(b))
			}
		})
	}
}

func TestHealth(t *testing.T) {
	app := fiber.New()
	repo := &MockOutfitRepository{Outfits: nil}
	h := handlers.NewHandler(repo)
	app.Get("/health", h.Health)

	req := httptest.NewRequest("GET", "/health", nil)
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("Failed to execute request: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Errorf("Expected 200, got %d", resp.StatusCode)
	}
}

func TestGetOutfits(t *testing.T) {
	app := fiber.New()
	outfits := []models.Outfit{
		{ID: "1", Gender: "male"},
		{ID: "2", Gender: "female"},
	}
	repo := &MockOutfitRepository{Outfits: outfits}
	h := handlers.NewHandler(repo)
	app.Get("/outfits", h.GetOutfits)

	req := httptest.NewRequest("GET", "/outfits?gender=male", nil)
	resp, err := app.Test(req)
	if err != nil {
		t.Fatalf("Failed to execute request: %v", err)
	}
	
	if resp.StatusCode != 200 {
		t.Errorf("Expected 200, got %d", resp.StatusCode)
	}
	
	var resOutfits []models.Outfit
	body, _ := io.ReadAll(resp.Body)
	json.Unmarshal(body, &resOutfits)
	
	if len(resOutfits) != 1 {
		t.Errorf("Expected 1 outfit, got %d", len(resOutfits))
	}
	if resOutfits[0].ID != "1" {
		t.Errorf("Expected ID 1, got %s", resOutfits[0].ID)
	}
}

func TestOutfitCRUD(t *testing.T) {
	app := fiber.New()
	outfits := []models.Outfit{
		{ID: "1", Name: "Casual Summer", Gender: "male"},
	}
	repo := &MockOutfitRepository{Outfits: outfits}
	h := handlers.NewHandler(repo)

	app.Get("/api/v1/outfits/:id", h.GetOutfit)
	app.Post("/api/v1/outfits", h.CreateOutfit)
	app.Put("/api/v1/outfits/:id", h.UpdateOutfit)
	app.Delete("/api/v1/outfits/:id", h.DeleteOutfit)

	// 1. Get existing outfit
	req := httptest.NewRequest("GET", "/api/v1/outfits/1", nil)
	resp, _ := app.Test(req)
	if resp.StatusCode != 200 {
		t.Errorf("Expected GetOutfit 200, got %d", resp.StatusCode)
	}

	// 2. Get non-existing outfit
	req = httptest.NewRequest("GET", "/api/v1/outfits/999", nil)
	resp, _ = app.Test(req)
	if resp.StatusCode != 404 {
		t.Errorf("Expected GetOutfit 404, got %d", resp.StatusCode)
	}

	// 3. Create outfit
	newOutfit := models.Outfit{
		ID:     "2",
		Name:   "Winter Cozy",
		Gender: "female",
	}
	body, _ := json.Marshal(newOutfit)
	req = httptest.NewRequest("POST", "/api/v1/outfits", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	resp, _ = app.Test(req)
	if resp.StatusCode != 201 {
		t.Errorf("Expected CreateOutfit 201, got %d", resp.StatusCode)
	}

	// 4. Update outfit
	updatedOutfit := models.Outfit{
		ID:     "1",
		Name:   "Casual Summer Updated",
		Gender: "unisex",
	}
	body, _ = json.Marshal(updatedOutfit)
	req = httptest.NewRequest("PUT", "/api/v1/outfits/1", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	resp, _ = app.Test(req)
	if resp.StatusCode != 200 {
		t.Errorf("Expected UpdateOutfit 200, got %d", resp.StatusCode)
	}

	// Verify update
	req = httptest.NewRequest("GET", "/api/v1/outfits/1", nil)
	resp, _ = app.Test(req)
	var gotOutfit models.Outfit
	respBody, _ := io.ReadAll(resp.Body)
	json.Unmarshal(respBody, &gotOutfit)
	if gotOutfit.Name != "Casual Summer Updated" {
		t.Errorf("Expected updated name 'Casual Summer Updated', got %s", gotOutfit.Name)
	}

	// 5. Delete outfit
	req = httptest.NewRequest("DELETE", "/api/v1/outfits/1", nil)
	resp, _ = app.Test(req)
	if resp.StatusCode != 200 {
		t.Errorf("Expected DeleteOutfit 200, got %d", resp.StatusCode)
	}

	// Verify delete
	req = httptest.NewRequest("GET", "/api/v1/outfits/1", nil)
	resp, _ = app.Test(req)
	if resp.StatusCode != 404 {
		t.Errorf("Expected GetOutfit 404 after delete, got %d", resp.StatusCode)
	}
}
