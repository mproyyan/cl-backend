package handlers

import (
	"errors"
	"regexp"

	"github.com/gofiber/fiber/v3"
	"go.mongodb.org/mongo-driver/mongo"

	"outfit-recommender/models"
)

var hexRegex = regexp.MustCompile(`^#[0-9a-fA-F]{6}$`)

func validateOutfit(outfit *models.Outfit) error {
	// Validate Gender
	validGenders := map[string]bool{"": true, "male": true, "female": true, "unisex": true}
	if !validGenders[outfit.Gender] {
		return errors.New("invalid gender, must be '', 'male', 'female', or 'unisex'")
	}

	// Validate Items Hexes
	items := []*models.Item{&outfit.Items.Top, &outfit.Items.Bottom, &outfit.Items.Outer, &outfit.Items.Shoes}
	itemNames := []string{"top", "bottom", "outer", "shoes"}
	for i, item := range items {
		if item.Hex != "" {
			if !hexRegex.MatchString(item.Hex) {
				return errors.New("invalid hex format in " + itemNames[i] + ", must match ^#[0-9a-fA-F]{6}$")
			}
		}
	}

	if outfit.Name == "" {
		return errors.New("outfit name is required")
	}

	return nil
}

// GetOutfit fetches a single outfit by ID
func (h *Handler) GetOutfit(c fiber.Ctx) error {
	id := c.Params("id")
	if id == "" {
		return c.Status(400).JSON(fiber.Map{"error": "id parameter is required"})
	}

	outfit, err := h.repo.GetByID(c.Context(), id)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return c.Status(404).JSON(fiber.Map{"error": "outfit not found"})
		}
		return c.Status(500).JSON(fiber.Map{"error": "failed to fetch outfit"})
	}

	return c.JSON(outfit)
}

// CreateOutfit creates a new outfit
func (h *Handler) CreateOutfit(c fiber.Ctx) error {
	var outfit models.Outfit
	if err := c.Bind().Body(&outfit); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "malformed JSON body"})
	}

	if err := validateOutfit(&outfit); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": err.Error()})
	}

	if err := h.repo.Create(c.Context(), &outfit); err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to create outfit"})
	}

	return c.Status(201).JSON(outfit) // Created status
}

// UpdateOutfit updates an existing outfit
func (h *Handler) UpdateOutfit(c fiber.Ctx) error {
	id := c.Params("id")
	if id == "" {
		return c.Status(400).JSON(fiber.Map{"error": "id parameter is required"})
	}

	var outfit models.Outfit
	if err := c.Bind().Body(&outfit); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "malformed JSON body"})
	}

	if err := validateOutfit(&outfit); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": err.Error()})
	}

	if err := h.repo.Update(c.Context(), id, &outfit); err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return c.Status(404).JSON(fiber.Map{"error": "outfit not found"})
		}
		return c.Status(500).JSON(fiber.Map{"error": "failed to update outfit"})
	}

	return c.JSON(outfit)
}

// DeleteOutfit deletes an outfit
func (h *Handler) DeleteOutfit(c fiber.Ctx) error {
	id := c.Params("id")
	if id == "" {
		return c.Status(400).JSON(fiber.Map{"error": "id parameter is required"})
	}

	if err := h.repo.Delete(c.Context(), id); err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return c.Status(404).JSON(fiber.Map{"error": "outfit not found"})
		}
		return c.Status(500).JSON(fiber.Map{"error": "failed to delete outfit"})
	}

	return c.JSON(fiber.Map{"message": "outfit deleted successfully"})
}
