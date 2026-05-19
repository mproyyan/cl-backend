package handlers

import (
	"regexp"

	"github.com/gofiber/fiber/v3"

	"outfit-recommender/models"
	"outfit-recommender/scoring"
)

type Handler struct {
	Outfits []models.Outfit
}

func NewHandler(outfits []models.Outfit) *Handler {
	return &Handler{Outfits: outfits}
}

func (h *Handler) Recommend(c *fiber.Ctx) error {
	var req models.RecommendRequest
	if err := c.BodyParser(&req); err != nil {
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

	resp := scoring.Recommend(h.Outfits, req)
	return c.JSON(resp)
}

func (h *Handler) GetOutfits(c *fiber.Ctx) error {
	gender := c.Query("gender")
	filtered := scoring.FilterByGender(h.Outfits, gender)
	return c.JSON(filtered)
}

func (h *Handler) Health(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"status": "ok", "service": "outfit-recommender"})
}
