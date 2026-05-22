package scoring_test

import (
	"testing"
	"outfit-recommender/models"
	"outfit-recommender/scoring"
)

func TestFilterByGender(t *testing.T) {
	outfits := []models.Outfit{
		{ID: "1", Gender: "male"},
		{ID: "2", Gender: "female"},
		{ID: "3", Gender: "unisex"},
	}

	tests := []struct {
		name     string
		gender   string
		expected int
	}{
		{"empty returns all", "", 3},
		{"male returns male and unisex", "male", 2},
		{"female returns female and unisex", "female", 2},
		{"unisex returns only unisex", "unisex", 1},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			res := scoring.FilterByGender(outfits, tt.gender)
			if len(res) != tt.expected {
				t.Errorf("Expected %d outfits, got %d", tt.expected, len(res))
			}
		})
	}
}
