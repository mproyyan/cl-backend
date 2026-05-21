package handlers

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/Azure/azure-sdk-for-go/sdk/storage/azblob"
	"github.com/gofiber/fiber/v3"
	"github.com/google/uuid"
)

// Azure config
var (
	azureClient   *azblob.Client
	containerName string
)

// InitAzure initializes the azure blob storage client
func InitAzure() error {
	connectionString := os.Getenv("AZURE_STORAGE_CONNECTION_STRING")
	if connectionString == "" {
		fmt.Println("WARNING: AZURE_STORAGE_CONNECTION_STRING is not set. Uploads will fail.")
		return nil
	}

	containerName = os.Getenv("AZURE_STORAGE_CONTAINER_NAME")
	if containerName == "" {
		containerName = "outfits"
	}

	client, err := azblob.NewClientFromConnectionString(connectionString, nil)
	if err != nil {
		return err
	}

	azureClient = client
	return nil
}

// UploadImage handles file upload to Azure
func (h *Handler) UploadImage(c fiber.Ctx) error {
	if azureClient == nil {
		return c.Status(500).JSON(fiber.Map{"error": "Azure storage is not configured"})
	}

	file, err := c.FormFile("image")
	if err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "image file is required"})
	}

	// Open the file
	fileContent, err := file.Open()
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": "failed to open uploaded file"})
	}
	defer fileContent.Close()

	// Generate unique blob name
	ext := filepath.Ext(file.Filename)
	blobName := uuid.NewString() + ext

	// Upload
	_, err = azureClient.UploadStream(c.Context(), containerName, blobName, fileContent, nil)
	if err != nil {
		return c.Status(500).JSON(fiber.Map{"error": fmt.Sprintf("failed to upload to azure: %v", err)})
	}

	// Construct URL. We assume public access.
	baseURL := strings.TrimSuffix(azureClient.URL(), "/")
	fullURL := fmt.Sprintf("%s/%s/%s", baseURL, containerName, blobName)

	return c.JSON(fiber.Map{"image_url": fullURL})
}

// DeleteImageFromAzure deletes a blob by its URL
func DeleteImageFromAzure(ctx context.Context, imageURL string) error {
	if azureClient == nil || imageURL == "" {
		return nil
	}

	// Extract blob name from URL
	parts := strings.Split(imageURL, "/")
	if len(parts) == 0 {
		return nil
	}
	blobName := parts[len(parts)-1]

	_, err := azureClient.DeleteBlob(ctx, containerName, blobName, nil)
	return err
}
