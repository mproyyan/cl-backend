package handlers_test

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http/httptest"
	"testing"

	"github.com/gofiber/fiber/v3"
	"outfit-recommender/handlers"
	"outfit-recommender/models"
)

type MockOutfitRepository struct {
	Outfits []models.Outfit
}

func (m *MockOutfitRepository) GetAll(ctx context.Context) ([]models.Outfit, error) {
	return m.Outfits, nil
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
