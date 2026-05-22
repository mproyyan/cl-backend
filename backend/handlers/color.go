package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/textproto"
	"os"

	"github.com/gofiber/fiber/v3"

	"outfit-recommender/models"
)

type ExternalColorAPIResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Data    struct {
		ColorType string `json:"color_type"`
		Undertone string `json:"undertone"`
		Skintone  string `json:"skintone"` // could be "skintone" or "skin_tone" but the prompt showed both
		Contrast  string `json:"contrast"`
	} `json:"data"`
}

func (h *Handler) AnalyzeColor(c fiber.Ctx) error {
	externalURL := os.Getenv("COLOR_DETECTION_API_URL")
	if externalURL == "" {
		return c.Status(500).JSON(fiber.Map{"error": "COLOR_DETECTION_API_URL is not configured on the server"})
	}

	file, err := c.FormFile("image")
	if err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "image file is required"})
	}

	fileContent, err := file.Open()
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to open image file"})
	}
	defer fileContent.Close()

	// Prepare multipart form for external API
	var requestBody bytes.Buffer
	writer := multipart.NewWriter(&requestBody)

	header := make(textproto.MIMEHeader)
	header.Set("Content-Disposition", fmt.Sprintf(`form-data; name="image"; filename="%s"`, file.Filename))
	
	contentType := file.Header.Get("Content-Type")
	if contentType == "" {
		contentType = "image/jpeg"
	}
	header.Set("Content-Type", contentType)

	part, err := writer.CreatePart(header)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to create form file"})
	}

	_, err = io.Copy(part, fileContent)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to copy image content"})
	}

	err = writer.Close()
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to close multipart writer"})
	}

	// Send request to external API
	req, err := http.NewRequest("POST", externalURL, &requestBody)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to create request to external API"})
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": fmt.Sprintf("failed to reach external API: %v", err)})
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		// Try to parse error message if possible
		var errResp map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errResp)
		return c.Status(resp.StatusCode).JSON(fiber.Map{
			"error":    "external API returned an error",
			"response": errResp,
		})
	}

	var extResponse ExternalColorAPIResponse
	if err := json.NewDecoder(resp.Body).Decode(&extResponse); err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to decode response from external API"})
	}

	if !extResponse.Success {
		return c.Status(400).JSON(fiber.Map{"error": extResponse.Message})
	}

	// Map to ColorAnalysisResponse
	analysis := models.ColorAnalysisResponse{
		ColorType: extResponse.Data.ColorType,
		Undertone: models.UndertoneRespone{
			Explanation: models.UndertoneTemplates.Explanation,
			Value:       models.FindUndertoneValue(extResponse.Data.Undertone),
		},
		Skintone: models.SkintoneResponse{
			Explanation: models.SkintoneTemplate.Explanation,
			Value:       models.FindSkintoneValue(extResponse.Data.Skintone),
		},
		Contrast: models.ContrastResponse{
			Explanation: models.ContrastTemplate.Explanation,
			Value:       models.FindContrastValue(extResponse.Data.Contrast),
		},
	}

	palette := models.FindSeasonalPalette(extResponse.Data.ColorType)
	analysis.BestColors = palette.BestColor
	analysis.AvoidColor = palette.AvoidColor

	return c.JSON(analysis)
}
