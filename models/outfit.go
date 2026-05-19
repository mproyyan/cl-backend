package models

type Item struct {
	Name  string `json:"name"`
	Color string `json:"color"`
	Hex   string `json:"hex"`
}

type Items struct {
	Top    Item `json:"top"`
	Bottom Item `json:"bottom"`
	Outer  Item `json:"outer"`
	Shoes  Item `json:"shoes"`
}

type Outfit struct {
	ID             string   `json:"id"`
	Name           string   `json:"name"`
	Gender         string   `json:"gender"`
	StyleTag       string   `json:"style_tag"`
	HarmonyTag     string   `json:"harmony_tag"`
	Undertone      string   `json:"undertone"`
	ContrastLevel  string   `json:"contrast_level"`
	Environments   []string `json:"environments"`
	WeatherSupport []string `json:"weather_support"`
	Items          Items    `json:"items"`
}

type OutfitData struct {
	Outfits []Outfit `json:"outfits"`
}

type RecommendRequest struct {
	BestColors  []string `json:"best_colors"`
	AvoidColors []string `json:"avoid_colors"`
	Gender      string   `json:"gender"`
}

type ItemScore struct {
	Key          string  `json:"key"`
	Name         string  `json:"name"`
	Color        string  `json:"color"`
	Hex          string  `json:"hex"`
	Weight       float64 `json:"weight"`
	BestDeltaE   float64 `json:"best_delta_e"`
	AvoidDeltaE  float64 `json:"avoid_delta_e"`
	BestMatch    float64 `json:"best_match"`
	AvoidMatch   float64 `json:"avoid_match"`
	Contribution float64 `json:"contribution"`
	Penalty      float64 `json:"penalty"`
}

type OutfitScore struct {
	Outfit     Outfit      `json:"outfit"`
	Score      float64     `json:"score"`
	BestTotal  float64     `json:"best_total"`
	AvoidTotal float64     `json:"avoid_total"`
	Coherence  float64     `json:"coherence"`
	ItemScores []ItemScore `json:"item_scores"`
	Reasons    []string    `json:"reasons"`
	Rank       int         `json:"rank"`
}

type RecommendResponse struct {
	Results []OutfitScore `json:"results"`
	Total   int           `json:"total"`
	Filters struct {
		Gender      string   `json:"gender"`
		BestColors  []string `json:"best_colors"`
		AvoidColors []string `json:"avoid_colors"`
	} `json:"filters"`
}
