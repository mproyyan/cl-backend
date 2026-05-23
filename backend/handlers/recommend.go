package handlers

import (
	"regexp"
	"strconv"

	"github.com/gofiber/fiber/v3"

	"outfit-recommender/models"
	"outfit-recommender/repository"
	"outfit-recommender/scoring"
)

type Handler struct {
	repo repository.OutfitRepository
}

func NewHandler(repo repository.OutfitRepository) *Handler {
	return &Handler{repo: repo}
}

func (h *Handler) Recommend(c fiber.Ctx) error {
	var req models.RecommendRequest
	if err := c.Bind().Body(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "malformed JSON body"})
	}

	hexRegex := regexp.MustCompile(`^#[0-9a-fA-F]{6}$`)

	for _, hex := range req.BestColors {
		if !hexRegex.MatchString(hex) {
			return c.Status(400).JSON(fiber.Map{"error": "invalid hex format in best_colors, must match ^#[0-9a-fA-F]{6}$"})
		}
	}
	for _, hex := range req.AvoidColors {
		if !hexRegex.MatchString(hex) {
			return c.Status(400).JSON(fiber.Map{"error": "invalid hex format in avoid_colors, must match ^#[0-9a-fA-F]{6}$"})
		}
	}

	gender := c.Query("gender")
	if gender != "" {
		req.Gender = gender
	}

	validGenders := map[string]bool{"": true, "male": true, "female": true, "unisex": true}
	if !validGenders[req.Gender] {
		return c.Status(400).JSON(fiber.Map{"error": "invalid gender, must be '', 'male', 'female', or 'unisex'"})
	}

	style := c.Query("style")
	validStyles := map[string]bool{"": true, "casual": true, "smart_casual": true, "formal": true, "minimalist": true, "streetwear": true}
	if !validStyles[style] {
		return c.Status(400).JSON(fiber.Map{"error": "invalid style, must be '', 'casual', 'smart_casual', 'formal', 'minimalist', or 'streetwear'"})
	}

	minScoreStr := c.Query("minScore")
	var minScore float64
	if minScoreStr != "" {
		if ms, err := strconv.ParseFloat(minScoreStr, 64); err == nil {
			minScore = ms
		} else {
			return c.Status(400).JSON(fiber.Map{"error": "invalid minScore, must be a number"})
		}
	}

	limitStr := c.Query("limit")
	var limit int
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil {
			limit = l
		} else {
			return c.Status(400).JSON(fiber.Map{"error": "invalid limit, must be an integer"})
		}
	}

	outfits, err := h.repo.GetAll(c.Context())
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to fetch outfits from database"})
	}

	if style != "" {
		var filtered []models.Outfit
		for _, o := range outfits {
			if o.StyleTag == style {
				filtered = append(filtered, o)
			}
		}
		outfits = filtered
	}

	resp := scoring.Recommend(outfits, req)

	if minScore > 0 || limit > 0 {
		var filteredResults []models.OutfitScore
		for _, r := range resp.Results {
			if minScore == 0 || r.Score >= minScore {
				filteredResults = append(filteredResults, r)
			}
		}
		if limit > 0 && len(filteredResults) > limit {
			filteredResults = filteredResults[:limit]
		}
		if filteredResults == nil {
			filteredResults = []models.OutfitScore{}
		}
		resp.Results = filteredResults
		resp.Total = len(resp.Results)
	}

	return c.JSON(resp)
}

func (h *Handler) GetOutfits(c fiber.Ctx) error {
	gender := c.Query("gender")
	outfits, err := h.repo.GetAll(c.Context())
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to fetch outfits from database"})
	}
	filtered := scoring.FilterByGender(outfits, gender)
	return c.JSON(filtered)
}

func (h *Handler) Health(c fiber.Ctx) error {
	return c.JSON(fiber.Map{"status": "ok", "service": "outfit-recommender"})
}
