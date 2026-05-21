package loader

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"outfit-recommender/models"
)

func LoadOutfits(path string) ([]models.Outfit, error) {
	var allOutfits []models.Outfit

	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}

	if info.IsDir() {
		files, err := os.ReadDir(path)
		if err != nil {
			return nil, err
		}

		for _, file := range files {
			if !file.IsDir() && strings.HasSuffix(file.Name(), ".json") {
				filePath := filepath.Join(path, file.Name())
				data, err := os.ReadFile(filePath)
				if err != nil {
					return nil, err
				}

				var outfitData models.OutfitData
				err = json.Unmarshal(data, &outfitData)
				if err != nil {
					return nil, err
				}

				allOutfits = append(allOutfits, outfitData.Outfits...)
			}
		}
	} else {
		data, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}

		var outfitData models.OutfitData
		err = json.Unmarshal(data, &outfitData)
		if err != nil {
			return nil, err
		}

		allOutfits = append(allOutfits, outfitData.Outfits...)
	}

	return allOutfits, nil
}
