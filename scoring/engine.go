package scoring

import (
	"math"
	"sort"

	"outfit-recommender/color"
	"outfit-recommender/models"
)

const (
	penaltyMultiplier = 1.6
	coherenceWeight   = 0.15
)

var (
	itemWeights = map[string]float64{
		"outer":  0.35,
		"top":    0.30,
		"bottom": 0.25,
		"shoes":  0.10,
	}
	itemOrder = []string{"outer", "top", "bottom", "shoes"}
)

func getItemByKey(items models.Items, key string) models.Item {
	switch key {
	case "outer":
		return items.Outer
	case "top":
		return items.Top
	case "bottom":
		return items.Bottom
	case "shoes":
		return items.Shoes
	default:
		return models.Item{}
	}
}

func scoreItem(item models.Item, key string, bestHexes, avoidHexes []string) models.ItemScore {
	weight := itemWeights[key]

	bestMatch := 0.0
	bestDeltaE := 999.0
	if len(bestHexes) > 0 {
		for _, hex := range bestHexes {
			dE, err := color.DeltaE(item.Hex, hex)
			if err == nil {
				if dE < bestDeltaE {
					bestDeltaE = dE
				}
			}
		}
		if bestDeltaE != 999.0 {
			bestMatch = color.DeltaEToScore(bestDeltaE)
		}
	}

	avoidMatch := 0.0
	avoidDeltaE := 999.0
	if len(avoidHexes) > 0 {
		for _, hex := range avoidHexes {
			dE, err := color.DeltaE(item.Hex, hex)
			if err == nil {
				if dE < avoidDeltaE {
					avoidDeltaE = dE
				}
			}
		}
		if avoidDeltaE != 999.0 {
			avoidMatch = color.AvoidPenalty(avoidDeltaE)
		}
	}

	var contribution float64
	if len(bestHexes) > 0 {
		contribution = bestMatch * weight
	}

	penalty := avoidMatch * weight * penaltyMultiplier

	return models.ItemScore{
		Key:          key,
		Name:         item.Name,
		Color:        item.Color,
		Hex:          item.Hex,
		Weight:       weight,
		BestDeltaE:   bestDeltaE,
		AvoidDeltaE:  avoidDeltaE,
		BestMatch:    bestMatch,
		AvoidMatch:   avoidMatch,
		Contribution: contribution,
		Penalty:      penalty,
	}
}

func generateReasons(itemScores []models.ItemScore, coherence float64) []string {
	var reasons []string

	var bestOuterTopScore models.ItemScore
	maxOuterTopScore := -1.0
	for _, sc := range itemScores {
		if sc.Key == "outer" || sc.Key == "top" {
			if sc.BestMatch > maxOuterTopScore {
				maxOuterTopScore = sc.BestMatch
				bestOuterTopScore = sc
			}
		}
	}

	if maxOuterTopScore > 0.70 {
		reasons = append(reasons, bestOuterTopScore.Name+" is a strong match for your preferred colors")
	} else if maxOuterTopScore > 0.40 {
		reasons = append(reasons, bestOuterTopScore.Name+" is close to your preferred colors")
	}

	for _, sc := range itemScores {
		if sc.AvoidMatch > 0.60 {
			reasons = append(reasons, sc.Name+" is close to a color you want to avoid")
		}
	}

	if coherence > 0.85 {
		reasons = append(reasons, "outfit colors are highly harmonious")
	} else if coherence < 0.50 {
		reasons = append(reasons, "outfit color combination is less cohesive")
	}

	if len(reasons) > 3 {
		reasons = reasons[:3]
	}
	if reasons == nil {
		reasons = []string{}
	}

	return reasons
}

func clamp(v, min, max float64) float64 {
	if v < min {
		return min
	}
	if v > max {
		return max
	}
	return v
}

func ScoreOutfit(outfit models.Outfit, bestHexes, avoidHexes []string) models.OutfitScore {
	var itemScores []models.ItemScore
	totalBest := 0.0
	totalAvoid := 0.0
	var hexSlice []string

	for _, key := range itemOrder {
		item := getItemByKey(outfit.Items, key)
		sc := scoreItem(item, key, bestHexes, avoidHexes)
		itemScores = append(itemScores, sc)
		totalBest += sc.Contribution
		totalAvoid += sc.Penalty
		hexSlice = append(hexSlice, item.Hex)
	}

	coherence := color.OutfitCoherence(hexSlice)
	coherenceBonus := coherence * coherenceWeight
	rawScore := totalBest - totalAvoid + coherenceBonus

	finalScore := math.Round(clamp(rawScore*100.0, 0.0, 100.0)*10.0) / 10.0
	reasons := generateReasons(itemScores, coherence)

	return models.OutfitScore{
		Outfit:     outfit,
		Score:      finalScore,
		BestTotal:  totalBest,
		AvoidTotal: totalAvoid,
		Coherence:  coherence,
		ItemScores: itemScores,
		Reasons:    reasons,
		Rank:       0,
	}
}

func FilterByGender(outfits []models.Outfit, gender string) []models.Outfit {
	if gender == "" {
		return outfits
	}
	var filtered []models.Outfit
	for _, o := range outfits {
		if gender == "male" && (o.Gender == "male" || o.Gender == "unisex") {
			filtered = append(filtered, o)
		} else if gender == "female" && (o.Gender == "female" || o.Gender == "unisex") {
			filtered = append(filtered, o)
		} else if gender == "unisex" && o.Gender == "unisex" {
			filtered = append(filtered, o)
		}
	}
	if filtered == nil {
		return []models.Outfit{}
	}
	return filtered
}

func Recommend(outfits []models.Outfit, req models.RecommendRequest) models.RecommendResponse {
	filtered := FilterByGender(outfits, req.Gender)

	var results []models.OutfitScore
	for _, o := range filtered {
		results = append(results, ScoreOutfit(o, req.BestColors, req.AvoidColors))
	}

	sort.SliceStable(results, func(i, j int) bool {
		return results[i].Score > results[j].Score
	})

	for i := range results {
		results[i].Rank = i + 1
	}

	if results == nil {
		results = []models.OutfitScore{}
	}

	resp := models.RecommendResponse{
		Results: results,
		Total:   len(results),
	}
	resp.Filters.Gender = req.Gender
	resp.Filters.BestColors = req.BestColors
	resp.Filters.AvoidColors = req.AvoidColors
	if resp.Filters.BestColors == nil {
		resp.Filters.BestColors = []string{}
	}
	if resp.Filters.AvoidColors == nil {
		resp.Filters.AvoidColors = []string{}
	}

	return resp
}
