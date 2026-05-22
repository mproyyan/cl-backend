package handlers

import (
	"regexp"

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

	validGenders := map[string]bool{"": true, "male": true, "female": true, "unisex": true}
	if !validGenders[req.Gender] {
		return c.Status(400).JSON(fiber.Map{"error": "invalid gender, must be '', 'male', 'female', or 'unisex'"})
	}

	outfits, err := h.repo.GetAll(c.Context())
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to fetch outfits from database"})
	}

	resp := scoring.Recommend(outfits, req)
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
