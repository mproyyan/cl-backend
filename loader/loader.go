package loader

import (
	"encoding/json"
	"os"

	"outfit-recommender/models"
)

func LoadOutfits(path string) ([]models.Outfit, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var outfitData models.OutfitData
	err = json.Unmarshal(data, &outfitData)
	if err != nil {
		return nil, err
	}

	return outfitData.Outfits, nil
}
