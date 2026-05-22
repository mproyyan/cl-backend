package scoring

import (
	"math"
	"sort"

	"outfit-recommender/color"
	"outfit-recommender/models"
)

const (
	// penaltyMultiplier tuned so that a single full-penalty item (avoidMatch=1.0)
	// on the heaviest piece (outer, weight=0.35) costs 0.35*1.4 = 0.49 points,
	// leaving the score still differentiable above zero rather than clamping flat.
	// Previous value of 1.6 allowed totalAvoid to exceed totalBest ceiling (1.0),
	// causing many outfits to collapse to 0 and lose ranking granularity.
	penaltyMultiplier = 1.4

	coherenceWeight = 0.15

	// Palette zone weights.
	// Core hexes are the most representative colors for a seasonal type.
	// Extended hexes are valid but shared across multiple types — they
	// should reward less so type-specific colors rank higher.
	coreWeight     = 1.0
	extendedWeight = 0.55
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

// bestMatchScore computes a weighted match score against two hex tiers.
// Core hexes contribute at full weight; extended hexes at extendedWeight.
// Using the minimum DeltaE across all hexes in each tier keeps the
// computation O(n) and naturally rewards exact palette matches.
func bestMatchScore(itemHex string, coreHexes, extendedHexes []string) (score float64, bestDeltaE float64) {
	bestDeltaE = 999.0

	coreBest := 999.0
	for _, hex := range coreHexes {
		dE, err := color.DeltaE(itemHex, hex)
		if err == nil && dE < coreBest {
			coreBest = dE
		}
	}

	extBest := 999.0
	for _, hex := range extendedHexes {
		dE, err := color.DeltaE(itemHex, hex)
		if err == nil && dE < extBest {
			extBest = dE
		}
	}

	// Use the overall closest match for the DeltaE field (for display/debug).
	if coreBest < extBest {
		bestDeltaE = coreBest
	} else if extBest < 999.0 {
		bestDeltaE = extBest
	}

	// Blend scores from both tiers, choosing the better weighted result.
	coreScore := 0.0
	if coreBest < 999.0 {
		coreScore = color.DeltaEToScore(coreBest) * coreWeight
	}
	extScore := 0.0
	if extBest < 999.0 {
		extScore = color.DeltaEToScore(extBest) * extendedWeight
	}

	// Take the higher of the two weighted scores. This means a perfect
	// core match outperforms an extended match, but a great extended match
	// still beats a mediocre core match.
	if coreScore >= extScore {
		score = coreScore
	} else {
		score = extScore
	}
	return score, bestDeltaE
}

// scoreItem scores one clothing item against the user's palette preferences.
// Signature change: accepts coreHexes + extendedHexes instead of a single
// bestHexes slice. Callers that only pass bestHexes can pass nil for extendedHexes
// and the behaviour degrades gracefully to the original single-tier logic.
func scoreItem(item models.Item, key string, coreHexes, extendedHexes, avoidHexes []string) models.ItemScore {
	weight := itemWeights[key]

	matchScore := 0.0
	bestDeltaE := 999.0
	if len(coreHexes) > 0 || len(extendedHexes) > 0 {
		matchScore, bestDeltaE = bestMatchScore(item.Hex, coreHexes, extendedHexes)
	}

	avoidMatch := 0.0
	avoidDeltaE := 999.0
	for _, hex := range avoidHexes {
		dE, err := color.DeltaE(item.Hex, hex)
		if err == nil && dE < avoidDeltaE {
			avoidDeltaE = dE
		}
	}
	if avoidDeltaE < 999.0 {
		avoidMatch = color.AvoidPenalty(avoidDeltaE)
	}

	contribution := matchScore * weight
	penalty := avoidMatch * weight * penaltyMultiplier

	return models.ItemScore{
		Key:          key,
		Name:         item.Name,
		Color:        item.Color,
		Hex:          item.Hex,
		Weight:       weight,
		BestDeltaE:   bestDeltaE,
		AvoidDeltaE:  avoidDeltaE,
		BestMatch:    matchScore,
		AvoidMatch:   avoidMatch,
		Contribution: contribution,
		Penalty:      penalty,
	}
}

// generateReasons produces up to 3 human-readable explanations for a score.
// Improved: reasons now cover undertone conflict and score tier context,
// giving the user more actionable feedback than threshold-only strings.
// Signature unchanged — called externally.
func generateReasons(itemScores []models.ItemScore, coherence float64) []string {
	var reasons []string

	// Best-matching outer or top
	bestKey := ""
	bestScore := -1.0
	for _, sc := range itemScores {
		if (sc.Key == "outer" || sc.Key == "top") && sc.BestMatch > bestScore {
			bestScore = sc.BestMatch
			bestKey = sc.Name
		}
	}
	if bestScore > 0.75 {
		reasons = append(reasons, bestKey+" matches your palette very well")
	} else if bestScore > 0.45 {
		reasons = append(reasons, bestKey+" is a reasonable palette match")
	}

	// Avoid-color warnings — report all flagged items, not just the first
	for _, sc := range itemScores {
		if sc.AvoidMatch > 0.55 {
			reasons = append(reasons, sc.Name+" is close to a color you want to avoid")
		}
	}

	// Coherence feedback
	switch {
	case coherence > 0.85:
		reasons = append(reasons, "outfit colors are highly harmonious")
	case coherence > 0.65:
		reasons = append(reasons, "outfit has a balanced color combination")
	case coherence < 0.50:
		// Try to be specific about why coherence is low
		warmItems, coolItems := 0, 0
		for _, sc := range itemScores {
			h, s, l, err := color.HexToHSL(sc.Hex)
			if err != nil || s < 0.08 || l < 0.08 || l > 0.95 {
				continue
			}
			// Reuse the same warm/cool heuristic as OutfitCoherence
			radH := h * math.Pi / 180.0
			axis := math.Cos(radH-30*math.Pi/180.0) * s
			if axis > 0.15 {
				warmItems++
			} else if axis < -0.15 {
				coolItems++
			}
		}
		if warmItems > 0 && coolItems > 0 {
			reasons = append(reasons, "outfit mixes warm and cool tones — consider staying in one undertone family")
		} else {
			reasons = append(reasons, "outfit color combination is less cohesive")
		}
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

// ScoreOutfit scores a single outfit against best and avoid hex lists.
//
// Signature unchanged — called externally.
// Internally now routes bestHexes through the two-tier scorer. Callers
// that do not need the extended-hex distinction can leave extendedHexes
// empty; the function behaves identically to before for those callers.
func ScoreOutfit(outfit models.Outfit, bestHexes, avoidHexes []string) models.OutfitScore {
	// For backward compatibility, treat the incoming bestHexes as core hexes.
	// Callers that want extended-hex support should use ScoreOutfitTiered.
	return ScoreOutfitTiered(outfit, bestHexes, nil, avoidHexes)
}

// ScoreOutfitTiered is the extended entry point that accepts separate
// core and extended palette hex slices. Use this when the caller can
// distinguish core palette colors from extended/shared ones.
func ScoreOutfitTiered(outfit models.Outfit, coreHexes, extendedHexes, avoidHexes []string) models.OutfitScore {
	var itemScores []models.ItemScore
	totalBest := 0.0
	totalAvoid := 0.0
	var hexSlice []string

	for _, key := range itemOrder {
		item := getItemByKey(outfit.Items, key)
		sc := scoreItem(item, key, coreHexes, extendedHexes, avoidHexes)
		itemScores = append(itemScores, sc)
		totalBest += sc.Contribution
		totalAvoid += sc.Penalty
		hexSlice = append(hexSlice, item.Hex)
	}

	coherence := color.OutfitCoherence(hexSlice)
	coherenceBonus := coherence * coherenceWeight

	// rawScore ceiling analysis:
	// totalBest max  = 1.0 * (0.35+0.30+0.25+0.10) = 1.00
	// coherenceBonus max = 1.0 * 0.15              = 0.15
	// totalAvoid max = 1.0 * 1.0 * 1.4             = 1.40 (one item, full penalty)
	// In practice all-item full penalty = 1.4, but totalBest would also be high
	// for a color close to both best and avoid, so the net is rarely extreme.
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

// FilterByGender filters outfits by gender.
// Signature unchanged — called externally.
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

// Recommend returns ranked outfit recommendations for a request.
// Signature unchanged — called externally.
func Recommend(outfits []models.Outfit, req models.RecommendRequest) models.RecommendResponse {
	filtered := FilterByGender(outfits, req.Gender)

	var results []models.OutfitScore
	for _, o := range filtered {
		// Use ScoreOutfitTiered if the request carries extended hexes,
		// otherwise fall back to ScoreOutfit (which calls ScoreOutfitTiered
		// with nil extendedHexes internally — same behaviour as before).
		if len(req.ExtendedColors) > 0 {
			results = append(results, ScoreOutfitTiered(o, req.BestColors, req.ExtendedColors, req.AvoidColors))
		} else {
			results = append(results, ScoreOutfit(o, req.BestColors, req.AvoidColors))
		}
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
