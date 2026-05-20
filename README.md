# Outfit Recommender API

The Outfit Recommender API is a modular REST API built in Go using the [Fiber](https://gofiber.io/) framework. It recommends outfits from a catalog based on a user's gender, color preferences (colors they look best in), and colors they wish to avoid. 

Rather than using simple RGB Euclidean distance, this project employs a **perceptually uniform color difference algorithm (CIE76 Delta E)** to ensure that the recommendations align closely with human visual perception.

---

## Table of Contents
1. [Project Structure](#project-structure)
2. [Color Decision Mechanism](#color-decision-mechanism)
   - [Hex to RGB Conversion](#1-hex-to-rgb-conversion)
   - [RGB to CIE XYZ Space](#2-rgb-to-cie-xyz-space)
   - [CIE XYZ to CIE L\*a\*b\* Space](#3-cie-xyz-to-cie-la*b*-space)
3. [The Delta Algorithm (CIE76 $\Delta E^*_{ab}$)](#the-delta-algorithm-cie76-delta-e_ab)
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
├── color/
│   └── delta_e.go         # Color conversions, Delta E calculation, and coherence scoring
├── data/
│   └── outfits.json       # Outfit catalog (static dataset)
├── handlers/
│   ├── recommend.go       # Fiber HTTP route handlers (GET/POST endpoints)
│   └── recommend_test.go  # Unit tests for route handlers
├── loader/
│   └── loader.go          # JSON data utility to load outfits from disk
├── models/
│   └── outfit.go          # Core domain models (Item, Outfit, Request/Response payloads)
├── public/                # Static assets and frontend UI code
├── scoring/
│   ├── engine.go          # Recommendation scoring, penalty, and ranking logic
│   └── engine_test.go     # Unit tests for the recommendation engine
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

## The Delta Algorithm (CIE76 $\Delta E^*_{ab}$)

Once colors are represented in $L^*a^*b^*$ coordinates, the perceptual color difference between two colors is calculated using the **CIE76 Delta E** ($\Delta E^*_{ab}$) formula. This is the Euclidean distance between the two points:

$$\Delta E^*_{ab} = \sqrt{(L_1^* - L_2^*)^2 + (a_1^* - a_2^*)^2 + (b_1^* - b_2^*)^2}$$

Interpretation of $\Delta E^*_{ab}$ values:
- $\Delta E < 1.0$: Not perceptible by the human eye.
- $1.0 \le \Delta E < 2.0$: Scarcely perceptible, observable by close inspection.
- $2.0 \le \Delta E < 10.0$: Perceptible at a glance.
- $10.0 \le \Delta E < 49.0$: Colors are more similar than opposite.
- $\Delta E \ge 49.0$: Colors are exact opposites.

### Delta E to Score Mapping
The API maps the computed $\Delta E$ value to a matching score between $0.0$ and $1.0$. The mapping is a piecewise function designed to award high scores for close matches and taper off as the difference increases:

| $\Delta E$ Range | Score Formula | Visual Matching Quality |
| :--- | :--- | :--- |
| $\Delta E < 5$ | $1.0$ | Identical / indistinguishable |
| $5 \le \Delta E < 10$ | $0.85 - (\Delta E - 5) \times 0.030$ | Very close match (tapers $0.85 \to 0.70$) |
| $10 \le \Delta E < 20$ | $0.70 - (\Delta E - 10) \times 0.025$ | Perceptible close match (tapers $0.70 \to 0.45$) |
| $20 \le \Delta E < 35$ | $0.45 - (\Delta E - 20) \times 0.020$ | Tolerable match (tapers $0.45 \to 0.15$) |
| $35 \le \Delta E < 50$ | $0.15 - (\Delta E - 35) \times 0.005$ | Poor match (tapers $0.15 \to 0.075$) |
| $\Delta E \ge 50$ | $0.0$ | Clashing / No match |

*Note: The score is automatically clamped to the $[0.0, 1.0]$ range.*

### Avoid Penalty Mapping
If an item's color is close to a color the user wants to avoid, a penalty score between $0.0$ and $1.0$ is calculated:

| $\Delta E$ Range | Penalty Formula | Severity |
| :--- | :--- | :--- |
| $\Delta E < 5$ | $1.0$ | Severe overlap with avoided color |
| $5 \le \Delta E < 15$ | $0.90 - (\Delta E - 5) \times 0.050$ | Moderate overlap (tapers $0.90 \to 0.40$) |
| $15 \le \Delta E < 30$ | $0.40 - (\Delta E - 15) \times 0.020$ | Mild overlap (tapers $0.40 \to 0.00$) |
| $\Delta E \ge 30$ | $0.0$ | Safe / no penalty |

---

## Outfit Coherence Calculation

An outfit's quality depends not only on matching individual items to user preferences, but also on how well the pieces in the outfit go together. The API computes an **Outfit Coherence** score using the HSL (Hue, Saturation, Lightness) color space:

1. **Filter Saturated Colors**: Neutral colors (like white, gray, black, beige, etc.) do not clash with other hues. Thus, only items with a saturation $S > 10\%$ are selected.
2. **Handle Low Saturation Outfits**: If there are fewer than 2 saturated colors in the outfit, it is highly neutral or monochrome. These are visually safe, so the API returns a default coherence score of `0.8`.
3. **Calculate Hue Distances**: For outfits with $\ge 2$ saturated items, the API computes the average pairwise shortest distance on the $360^\circ$ hue wheel:
   $$\text{distance}(H_1, H_2) = \min(|H_1 - H_2|, 360 - |H_1 - H_2|)$$
4. **Map to Coherence Score**:
   - $\text{Average Difference} < 30^\circ$: Coherence = **$1.0$** (analogous, highly cohesive)
   - $\text{Average Difference} < 60^\circ$: Coherence = **$0.85$** (harmonious)
   - $\text{Average Difference} < 120^\circ$: Coherence = **$0.65$** (partially cohesive)
   - $\text{Average Difference} \ge 120^\circ$: Coherence = **$0.40$** (less cohesive / high contrast clashing potential)

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
   For each item, find its minimum Delta E to any of the user's preferred colors (`best_colors`), compute the match score, and weight it:
   $$T_{\text{best}} = \sum_{i \in \text{Items}} (\text{BestMatch}_i \times \text{Weight}_i)$$

2. **Avoided Color Penalty ($T_{\text{avoid}}$)**:
   For each item, find its minimum Delta E to any of the user's avoided colors (`avoid_colors`), compute the penalty score, and apply a penalty multiplier ($1.6$):
   $$T_{\text{avoid}} = \sum_{i \in \text{Items}} (\text{AvoidPenalty}_i \times \text{Weight}_i \times 1.6)$$

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

1. Make sure you have Go installed ($1.22+$ recommended).
2. Clone the repository and navigate to the project directory.
3. Install dependencies:
   ```bash
   go mod download
   ```
4. Run the API server:
   ```bash
   go run main.go
   ```
   *By default, the server runs on port `3000` and loads outfits from `data/outfits.json`.*

### Environment Variables
You can customize the API behavior using the following environment variables:
- `PORT`: The port number on which the server should listen (default: `3000`).
- `OUTFITS_JSON`: Path to the outfits catalog file (default: `data/outfits.json`).

Example:
```bash
PORT=8080 OUTFITS_JSON=my_outfits.json go run main.go
```

---

## Running Tests

Unit tests are provided for both the color delta calculations, HSL conversions, coherence scoring, and HTTP route handlers.

To run all tests, execute:
```bash
go test -v ./...
```
