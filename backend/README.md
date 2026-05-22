# Outfit Recommender API

The Outfit Recommender API is a modular REST API built in Go using the [Fiber](https://gofiber.io/) framework. It recommends outfits from a catalog based on a user's gender, color preferences (colors they look best in), and colors they wish to avoid. 

Rather than using simple RGB Euclidean distance, this project employs a **perceptually uniform color difference algorithm (CIEDE2000)** to ensure that the recommendations align closely with human visual perception.

---

## Table of Contents
1. [Project Structure](#project-structure)
2. [Color Decision Mechanism](#color-decision-mechanism)
   - [Hex to RGB Conversion](#1-hex-to-rgb-conversion)
   - [RGB to CIE XYZ Space](#2-rgb-to-cie-xyz-space)
   - [CIE XYZ to CIE L\*a\*b\* Space](#3-cie-xyz-to-cie-la*b*-space)
3. [The Delta Algorithm (CIEDE2000)](#the-delta-algorithm-ciede2000)
   - [Delta E to Score Mapping](#delta-e-to-score-mapping)
   - [Avoid Penalty Mapping](#avoid-penalty-mapping)
4. [Outfit Coherence Calculation](#outfit-coherence-calculation)
5. [Scoring Engine](#scoring-engine)
   - [Item Weights](#item-weights)
   - [Overall Outfit Scoring Formulation](#overall-outfit-scoring-formulation)
6. [API Endpoints](#api-endpoints)
   - [Health Check](#health-check)
   - [Get All Outfits](#get-all-outfits)
   - [Get Outfit Recommendations](#get-outfit-recommendations)
7. [Running the Project](#running-the-project)
8. [Running Tests](#running-tests)

---

## Project Structure

The project follows a clean, modular structure:

```
├── cmd/
│   └── seed/              # Database seeding script
├── color/
│   └── delta_e.go         # Color conversions, Delta E calculation, and coherence scoring
├── data/                  # Outfit catalog (multiple JSON files for seeding)
├── db/                    # MongoDB connection and initialization
├── handlers/              # Fiber HTTP route handlers (API and Azure Storage integration)
├── loader/
│   └── loader.go          # JSON data utility to load outfits from a directory
├── models/
│   └── outfit.go          # Core domain models (Item, Outfit, Request/Response payloads)
├── public/                # Static assets and frontend UI code
├── repository/            # MongoDB data access layer
├── scoring/
│   ├── engine.go          # Recommendation scoring, penalty, and ranking logic
│   └── engine_test.go     # Unit tests for the recommendation engine
├── docker-compose.yml     # Docker Compose configuration for MongoDB and API
├── .env                   # Environment variables for MongoDB and Azure
├── go.mod
├── go.sum
└── main.go                # API entrypoint, server configuration, and router
```

---

## Color Decision Mechanism

Human color perception is non-linear. In the standard RGB color space, the mathematical distance between two color vectors does not represent how similar they look to a human. For example, a small shift in green might look much larger than a similar shift in blue.

To solve this, the API translates Hex colors into the **CIE L\*a\*b\*** color space. CIE L\*a\*b\* is designed to be perceptually uniform, where:
- **$L^*$** represents Lightness ($0$ = black, $100$ = white).
- **$a^*$** represents the green-red axis (negative = green, positive = red).
- **$b^*$** represents the blue-yellow axis (negative = blue, positive = yellow).

The conversion pipeline operates in three steps:

### 1. Hex to RGB Conversion
The input Hex string (e.g., `#F2E7D2`) is parsed into standard red, green, and blue integer values in the $[0, 255]$ range and converted to floats.

### 2. RGB to CIE XYZ Space
Since RGB is device-dependent, it is first converted to the standard CIE XYZ space. This requires removing the gamma correction (linearization) and then applying a transformation matrix:

$$\text{linearize}(C) = \begin{cases} \left(\frac{C + 0.055}{1.055}\right)^{2.4} & \text{if } C > 0.04045 \\ \frac{C}{12.92} & \text{otherwise} \end{cases}$$

Where $C \in \\{R / 255.0, G / 255.0, B / 255.0\\}$. 

The linearized RGB values are multiplied by the standard transformation matrix to obtain XYZ coordinates:
- $X = R_{\text{linear}} \times 0.4124564 + G_{\text{linear}} \times 0.3575761 + B_{\text{linear}} \times 0.1804375$
- $Y = R_{\text{linear}} \times 0.2126729 + G_{\text{linear}} \times 0.7151522 + B_{\text{linear}} \times 0.0721750$
- $Z = R_{\text{linear}} \times 0.0193339 + G_{\text{linear}} \times 0.1191920 + B_{\text{linear}} \times 0.9503041$

### 3. CIE XYZ to CIE L\*a\*b\* Space
The XYZ values are normalized relative to the standard $D_{65}$ white point ($X_n = 0.95047$, $Y_n = 1.00000$, $Z_n = 1.08883$):

$$f(t) = \begin{cases} t^{1/3} & \text{if } t > 0.008856 \\ 7.787 \times t + \frac{16}{116} & \text{otherwise} \end{cases}$$

The $L^*a^*b^*$ coordinates are then calculated as:
- $L^* = 116 \times f\left(\frac{Y}{Y_n}\right) - 16$
- $a^* = 500 \times \left[ f\left(\frac{X}{X_n}\right) - f\left(\frac{Y}{Y_n}\right) \right]$
- $b^* = 200 \times \left[ f\left(\frac{Y}{Y_n}\right) - f\left(\frac{Z}{Z_n}\right) \right]$

---

## The Delta Algorithm (CIEDE2000)

Once colors are represented in $L^*a^*b^*$ coordinates, the perceptual color difference between two colors is calculated using the **CIEDE2000** formula. CIEDE2000 is significantly more accurate than CIE76, particularly for blues and dark colors, making it highly effective for seasonal color analysis.

The API uses the CIEDE2000 calculation to determine the perceptual distance ($\Delta E$) between two colors. A smaller $\Delta E$ implies a closer visual match.

### Delta E to Score Mapping
The API maps the computed $\Delta E$ value to a matching score between $0.0$ and $1.0$. The CIEDE2000 scale is perceptually tighter than CIE76, so the thresholds are recalibrated to reward extremely close matches and taper off strictly:

| $\Delta E$ Range | Score Formula | Visual Matching Quality |
| :--- | :--- | :--- |
| $\Delta E < 3$ | $1.0$ | Near-identical match |
| $3 \le \Delta E < 8$ | $0.90 - (\Delta E - 3) \times 0.030$ | Close match (tapers $0.90 \to 0.75$) |
| $8 \le \Delta E < 18$ | $0.75 - (\Delta E - 8) \times 0.025$ | Similar family but distinct shade (tapers $0.75 \to 0.50$) |
| $18 \le \Delta E < 30$ | $0.50 - (\Delta E - 18) \times 0.020$ | Related but noticeably different (tapers $0.50 \to 0.26$) |
| $30 \le \Delta E < 45$ | $0.26 - (\Delta E - 30) \times 0.010$ | Distant, different color family (tapers $0.26 \to 0.11$) |
| $\Delta E \ge 45$ | $0.0$ | Clashing / No match |

*Note: The score is automatically clamped to the $[0.0, 1.0]$ range.*

### Avoid Penalty Mapping
If an item's color is close to a color the user wants to avoid, a penalty score between $0.0$ and $1.0$ is calculated. The decay is steeper so avoid-colors have a sharp, localized effect:

| $\Delta E$ Range | Penalty Formula | Severity |
| :--- | :--- | :--- |
| $\Delta E < 3$ | $1.0$ | Essentially the same color (full penalty) |
| $3 \le \Delta E < 12$ | $0.90 - (\Delta E - 3) \times 0.055$ | Strong penalty that decays (tapers $0.90 \to 0.405$) |
| $12 \le \Delta E < 25$ | $0.40 - (\Delta E - 12) \times 0.025$ | Moderate residual penalty (tapers $0.40 \to 0.075$) |
| $\Delta E \ge 25$ | $0.0$ | Far enough / no penalty |

---

## Outfit Coherence Calculation

An outfit's quality depends not only on matching individual items to user preferences, but also on how well the pieces in the outfit go together. The API computes an **Outfit Coherence** score primarily focused on undertone consistency and hue spread:

1. **Evaluate Undertones**: Colors are classified as warm (e.g., reds, yellows) or cool (e.g., blues, purples) based on their hue and saturation. Mixing warm and cool undertones receives a severe penalty, as it is the primary violation in seasonal color analysis.
2. **Handle Low Saturation Outfits**: Neutral colors do not clash. If an outfit has fewer than 2 saturated colors, it is considered visually safe and receives a default coherence score of `0.80`.
3. **Calculate Hue Spread**: For saturated items, the average pairwise distance on the $360^\circ$ hue wheel is computed. Analogous or monochromatic palettes ($< 30^\circ$) score perfectly, while wider complementary schemes score progressively lower.
4. **Final Coherence Score**: The coherence blends the **undertone consistency** (weighted at 65%) and the **hue spread** (weighted at 35%) to yield a final score between `0.0` and `1.0`.

---

## Scoring Engine

The scoring engine evaluates each outfit in the catalog by aggregating the match and penalty scores of its individual items, then applying the outfit coherence bonus.

### Item Weights
Not all items in an outfit contribute equally to its overall appearance. The scoring engine applies weights to each clothing item key:
- **`outer`**: $0.35$ (Largest impact on visual area)
- **`top`**: $0.30$
- **`bottom`**: $0.25$
- **`shoes`**: $0.10$ (Smallest impact on visual area)

### Overall Outfit Scoring Formulation
For a given outfit, the scoring engine calculates:

1. **Preferred Color Match ($T_{\text{best}}$)**:
   The API supports a **two-tier** matching system. For each item, it evaluates the match against **Core Hexes** (weight $1.0$) and **Extended Hexes** (weight $0.55$). It chooses the higher of the two weighted scores, ensuring core palette matches outperform extended ones:
   $$T_{\text{best}} = \sum_{i \in \text{Items}} (\text{BestMatch}_i \times \text{Weight}_i)$$

2. **Avoided Color Penalty ($T_{\text{avoid}}$)**:
   For each item, find its minimum Delta E to any of the user's avoided colors (`avoid_colors`), compute the penalty score, and apply a penalty multiplier ($1.4$):
   $$T_{\text{avoid}} = \sum_{i \in \text{Items}} (\text{AvoidPenalty}_i \times \text{Weight}_i \times 1.4)$$

3. **Coherence Bonus ($B_{\text{coherence}}$)**:
   $$\text{Coherence Bonus} = \text{OutfitCoherence}(\text{items}) \times 0.15$$

4. **Final Scoring**:
   $$\text{Raw Score} = T_{\text{best}} - T_{\text{avoid}} + B_{\text{coherence}}$$
   $$\text{Final Score} = \text{clamp}(\text{Raw Score} \times 100, 0.0, 100.0)$$

The final score is rounded to $1$ decimal place. Recommended outfits are returned sorted in descending order of this score.

---

## API Endpoints

### Health Check
Returns the service status.
- **URL**: `/health`
- **Method**: `GET`
- **Response**: `200 OK`
  ```json
  {
    "service": "outfit-recommender",
    "status": "ok"
  }
  ```

### Get All Outfits
Returns all outfits loaded in the system, optionally filtered by gender.
- **URL**: `/api/v1/outfits`
- **Method**: `GET`
- **Query Parameters**:
  - `gender` (optional): `male` | `female` | `unisex`
- **Response**: `200 OK`
  ```json
  [
    {
      "id": "olive-cafe-layers",
      "name": "olive cafe layers",
      "image_url": "https://storage.example.com/outfits/olive-cafe.jpg",
      "gender": "male",
      "style_tag": "casual",
      "harmony_tag": "earthy",
      "undertone": "warm",
      "contrast_level": "low",
      "environments": ["outdoor", "indoor"],
      "weather_support": ["cloudy", "sunny"],
      "items": {
        "top": { "name": "flannel", "color": "cream", "hex": "#F2E7D2" },
        "bottom": { "name": "chinos", "color": "tan", "hex": "#C9AE88" },
        "outer": { "name": "cardigan", "color": "olive green", "hex": "#5A6E34" },
        "shoes": { "name": "boots", "color": "brown", "hex": "#7E603F" }
      }
    }
  ]
  ```

### Create, Update, Delete Outfit
Standard REST endpoints for managing the outfit catalog.
- **POST** `/api/v1/outfits`
- **PUT** `/api/v1/outfits/:id`
- **DELETE** `/api/v1/outfits/:id`

### Upload Image
Uploads an image to Azure Blob Storage and returns the public URL.
- **URL**: `/api/v1/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Body**: form-data with `image` field containing the file.
- **Response**: `200 OK`
  ```json
  {
    "image_url": "https://account.blob.core.windows.net/outfits/uuid.jpg"
  }
  ```

### Analyze Color
Accepts a facial photo and returns a comprehensive personal color analysis, including undertone, skintone, contrast, and recommended seasonal color palettes.
- **URL**: `/api/v1/analyze-color`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Body**: form-data with `image` field containing the photo.
- **Response**: `200 OK`
  ```json
  {
    "color_type": "Light Summer",
    "undertone": {
      "explanation": "Undertone is the natural color...",
      "value": { "name": "Cool", "explanation": "Your skin naturally carries..." }
    },
    "skintone": {
      "explanation": "Skintone refers to...",
      "value": { "name": "Medium Skintone", "explanation": "Your skin has a balanced depth..." }
    },
    "contrast": {
      "explanation": "Contrast describes the level...",
      "value": { "name": "Low Contrast", "explanation": "Your features blend together..." }
    },
    "best_colors": [
      { "name": "soft cool blue-gray", "hex": "#B8CCD8" }
    ],
    "avoid_color": [
      { "name": "warm burnt orange", "hex": "#D4622A" }
    ]
  }
  ```

### Get Outfit Recommendations
Scores and ranks outfits based on user preferences and filters out mismatched genders.
- **URL**: `/api/v1/recommend`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "best_colors": ["#5A6E34", "#C9AE88"],
    "avoid_colors": ["#171717"],
    "gender": "male"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "results": [
      {
        "outfit": {
          "id": "olive-cafe-layers",
          "name": "olive cafe layers",
          "image_url": "https://storage.example.com/outfits/olive-cafe.jpg",
          "gender": "male",
          "style_tag": "casual",
          "harmony_tag": "earthy",
          "undertone": "warm",
          "contrast_level": "low",
          "environments": ["outdoor", "indoor"],
          "weather_support": ["cloudy", "sunny"],
          "items": {
            "top": { "name": "flannel", "color": "cream", "hex": "#F2E7D2" },
            "bottom": { "name": "chinos", "color": "tan", "hex": "#C9AE88" },
            "outer": { "name": "cardigan", "color": "olive green", "hex": "#5A6E34" },
            "shoes": { "name": "boots", "color": "brown", "hex": "#7E603F" }
          }
        },
        "score": 68.3,
        "best_total": 0.5625,
        "avoid_total": 0,
        "coherence": 0.8,
        "item_scores": [
          {
            "key": "outer",
            "name": "cardigan",
            "color": "olive green",
            "hex": "#5A6E34",
            "weight": 0.35,
            "best_delta_e": 0,
            "avoid_delta_e": 999,
            "best_match": 1,
            "avoid_match": 0,
            "contribution": 0.35,
            "penalty": 0
          },
          {
            "key": "top",
            "name": "flannel",
            "color": "cream",
            "hex": "#F2E7D2",
            "weight": 0.3,
            "best_delta_e": 21.05435987178351,
            "avoid_delta_e": 999,
            "best_match": 0.4289128025643298,
            "contribution": 0.12867384076929894,
            "penalty": 0
          },
          {
            "key": "bottom",
            "name": "chinos",
            "color": "tan",
            "hex": "#C9AE88",
            "weight": 0.25,
            "best_delta_e": 0,
            "avoid_delta_e": 999,
            "best_match": 1,
            "avoid_match": 0,
            "contribution": 0.25,
            "penalty": 0
          },
          {
            "key": "shoes",
            "name": "boots",
            "color": "brown",
            "hex": "#7E603F",
            "weight": 0.1,
            "best_delta_e": 28.09355799732789,
            "avoid_delta_e": 999,
            "best_match": 0.2881288400534422,
            "contribution": 0.02881288400534422,
            "penalty": 0
          }
        ],
        "reasons": [
          "cardigan is a strong match for your preferred colors",
          "outfit colors are highly harmonious"
        ],
        "rank": 1
      }
    ],
    "total": 10,
    "filters": {
      "gender": "male",
      "best_colors": ["#5A6E34", "#C9AE88"],
      "avoid_colors": ["#171717"]
    }
  }
  ```

---

## Running the Project

1. Make sure you have Docker and Docker Compose installed.
2. Clone the repository and navigate to the project directory.
3. Create a `.env` file based on your environment. Example:
   ```env
   MONGO_URI=mongodb://mongo:27017
   MONGO_DB=outfit_recommender
   PORT=3000
   AZURE_STORAGE_CONNECTION_STRING=your_connection_string
   AZURE_STORAGE_CONTAINER_NAME=outfits
   ```
4. Start the application using Docker Compose:
   ```bash
   docker-compose up -d --build
   ```
   *The API will be available on port `3000` and MongoDB on `27017`.*

### Database Seeding
To populate the MongoDB database with initial outfit data from the `data/` directory:
```bash
go run cmd/seed/main.go
```

---

## Running Tests

Unit tests are provided for both the color delta calculations, HSL conversions, coherence scoring, and HTTP route handlers.

To run all tests, execute:
```bash
go test -v ./...
```
