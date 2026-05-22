package models

import "strings"

type Color struct {
	Name string `json:"name"`
	Hex  string `json:"hex"`
}

type Undertone struct {
	Explanation string           `json:"explanation"`
	Values      []UndertoneValue `json:"values"`
}

type UndertoneValue struct {
	Name        string `json:"name"`
	Explanation string `json:"explanation"`
}

type UndertoneRespone struct {
	Explanation string         `json:"explanation"`
	Value       UndertoneValue `json:"value"`
}

type Skintone struct {
	Explanation string          `json:"explanation"`
	Values      []SkintoneValue `json:"values"`
}

type SkintoneValue struct {
	Name        string `json:"name"`
	Explanation string `json:"explanation"`
}

type SkintoneResponse struct {
	Explanation string        `json:"explanation"`
	Value       SkintoneValue `json:"value"`
}

type Contrast struct {
	Explanation string          `json:"explanation"`
	Values      []ContrastValue `json:"values"`
}

type ContrastValue struct {
	Name        string `json:"name"`
	Explanation string `json:"explanation"`
}

type ContrastResponse struct {
	Explanation string        `json:"explanation"`
	Value       ContrastValue `json:"value"`
}

var UndertoneTemplates Undertone = Undertone{
	Explanation: "Undertone is the natural color that exists beneath the surface of your skin. Unlike skintone, undertone usually does not change even if your skin becomes darker from sun exposure or lighter from skincare treatments. It affects how different colors interact with your complexion and determines whether certain shades make your appearance look brighter, healthier, softer, or more tired. Undertone is one of the most important factors in personal color analysis because it creates the foundation of overall color harmony.",
	Values: []UndertoneValue{
		{
			Name:        "Cool",
			Explanation: "Your skin naturally carries pink, rosy, bluish, or slightly red undertones beneath the surface. Cool-toned colors tend to make your complexion appear clearer, fresher, and more balanced because they harmonize with the natural coolness in your skin. Shades such as icy blue, jewel tones, charcoal, cool pink, pure white, and blue-based red usually enhance your features and create a refined, elegant impression. Warm earthy colors, on the other hand, may sometimes make your skin appear dull, uneven, or slightly yellowish because they conflict with the cool base of your complexion.",
		},
		{
			Name:        "Warm",
			Explanation: "Your skin contains golden, peachy, yellow, or olive warmth beneath the surface. Warm colors naturally enhance the healthy glow in your complexion and often make your face appear brighter and more radiant. Earthy tones, camel, warm browns, coral, mustard, olive green, and creamy whites usually blend harmoniously with your natural coloring and create an energetic, approachable appearance. Extremely cool or icy shades may sometimes make your skin look pale or washed out because they reduce the warmth that naturally exists in your features.",
		},
	},
}

var SkintoneTemplate Skintone = Skintone{
	Explanation: "Skintone refers to the visible depth or brightness of your skin color. Unlike undertone, skintone can change slightly because of tanning, sunlight, skincare, or environmental factors. Skintone mainly influences how light, dark, soft, or intense colors appear against your skin and helps determine the ideal depth and brightness level of a color palette.",
	Values: []SkintoneValue{
		{
			Name:        "Light Skintone",
			Explanation: "Your skin appears fair to light in depth and usually reflects light more easily than deeper skintones. Because of this, colors often stand out more noticeably against your complexion, especially darker or highly saturated shades. Softer, cleaner, or lighter colors frequently create a fresh and balanced appearance, while extremely heavy or muddy colors may sometimes overpower your natural softness depending on your overall contrast level.",
		},
		{
			Name:        "Medium Skintone",
			Explanation: "Your skin has a balanced depth that sits between very light and very deep complexions. This creates natural versatility, allowing many colors to appear harmonious when matched correctly with your undertone. Rich earthy tones, medium-depth colors, and balanced contrasts often work especially well because they complement the natural richness of your complexion without overpowering it.",
		},
		{
			Name:        "Dark Skintone",
			Explanation: "Your skin has strong depth and richness, giving your appearance natural intensity and visual presence. Deep, saturated, and bold colors often look striking and luxurious because they match the richness already present in your complexion. Strong jewel tones, deep neutrals, and vivid shades usually enhance your features beautifully, while very pale or dusty colors may sometimes appear less harmonious unless styled intentionally.",
		},
	},
}

var ContrastTemplate = Contrast{
	Explanation: "Contrast describes the level of visual difference between your facial features, especially the relationship between your skin, hair, eyes, and eyebrows. It influences how strong or soft your overall appearance looks and determines whether bold or muted color combinations feel more natural on you.",
	Values: []ContrastValue{
		{
			Name:        "Low Contrast",
			Explanation: "Your features blend together more softly with less noticeable difference between your skin, hair, and eyes. Instead of sharp separation, your overall appearance feels smooth, gentle, and naturally balanced. Because of this, softer color transitions, muted palettes, and low-contrast combinations usually appear more harmonious and effortless on you. Dusty tones, tonal outfits, blended neutrals, and softer shades often enhance your features without overpowering them. Extremely bold contrasts or very harsh color combinations may sometimes draw attention away from your natural softness and make your appearance feel less balanced.",
		},
		{
			Name:        "High Contrast",
			Explanation: "Your features create a strong visual separation, such as light skin paired with dark hair or bright eyes combined with deeper facial features. Because your appearance already contains natural sharpness and definition, bold color combinations and strong light-dark balance tend to look especially harmonious on you. High saturation, crisp contrast, and clearly separated tones often enhance your features and make your appearance look more striking and confident. Softer or overly muted palettes may sometimes reduce the natural clarity and impact of your overall look.",
		},
	},
}

type SeasonalPallete struct {
	Name       string  `json:"name"`
	BestColor  []Color `json:"best_color"`
	AvoidColor []Color `json:"avoid_color"`
}

var SeasonalPalletePresets []SeasonalPallete = []SeasonalPallete{
	{
		Name: "Clear Spring",
		BestColor: []Color{
			{Hex: "#E8472A", Name: "vivid warm red-orange"},
			{Hex: "#F4763A", Name: "clear tangerine"},
			{Hex: "#E8B020", Name: "warm golden yellow"},
			{Hex: "#E8C84A", Name: "warm clear yellow"},
			{Hex: "#5BAD6A", Name: "warm yellow-green"},
			{Hex: "#F28B6E", Name: "bright warm peach-coral"},
			{Hex: "#D94F7A", Name: "warm vivid rose"},
			{Hex: "#FFF0D6", Name: "warm ivory white"},
		},
		AvoidColor: []Color{
			{Hex: "#8C8C78", Name: "dusty warm gray"},
			{Hex: "#6B7A8D", Name: "cool blue-gray"},
			{Hex: "#7A6E88", Name: "dusty cool purple"},
			{Hex: "#5C6650", Name: "muted dark olive"},
			{Hex: "#A0896C", Name: "muddy tan"},
			{Hex: "#3A3A3A", Name: "heavy charcoal"},
			{Hex: "#7C8FA0", Name: "cool slate"},
			{Hex: "#9E8E7E", Name: "dusty beige-gray"},
		},
	},
	{
		Name: "Warm Spring",
		BestColor: []Color{
			{Hex: "#F5963C", Name: "warm amber orange"},
			{Hex: "#F2BE3A", Name: "golden warm yellow"},
			{Hex: "#D4A800", Name: "deep warm gold"},
			{Hex: "#78B040", Name: "warm yellow-green"},
			{Hex: "#E07050", Name: "warm terracotta coral"},
			{Hex: "#F0C080", Name: "warm peach apricot"},
			{Hex: "#C86030", Name: "warm rust-orange"},
			{Hex: "#FDF0D0", Name: "warm cream"},
		},
		AvoidColor: []Color{
			{Hex: "#4A506E", Name: "cool dark navy-gray"},
			{Hex: "#7090A8", Name: "cool steel blue"},
			{Hex: "#9080A8", Name: "cool dusty purple"},
			{Hex: "#606878", Name: "cool blue-gray"},
			{Hex: "#8898A8", Name: "cool medium gray-blue"},
			{Hex: "#B0A8C0", Name: "cool lavender-gray"},
			{Hex: "#3A3050", Name: "deep cool purple-navy"},
			{Hex: "#505868", Name: "cool dark slate"},
		},
	},
	{
		Name: "Light Spring",
		BestColor: []Color{
			{Hex: "#F8D5A8", Name: "warm peach"},
			{Hex: "#FAE0B0", Name: "warm apricot cream"},
			{Hex: "#F5E898", Name: "warm pale yellow"},
			{Hex: "#C8E0A0", Name: "warm soft yellow-green"},
			{Hex: "#F4B8A0", Name: "warm soft coral"},
			{Hex: "#E8C8B8", Name: "warm rose beige"},
			{Hex: "#F0D0B8", Name: "warm sandy pink"},
			{Hex: "#FBF5E8", Name: "warm soft white-cream"},
		},
		AvoidColor: []Color{
			{Hex: "#2A3050", Name: "dark cool navy"},
			{Hex: "#3A3850", Name: "dark cool charcoal-purple"},
			{Hex: "#504868", Name: "cool dark plum"},
			{Hex: "#284040", Name: "dark cool teal-black"},
			{Hex: "#3C3028", Name: "dark heavy warm brown"},
			{Hex: "#486050", Name: "dark muted teal-green"},
			{Hex: "#2C2840", Name: "very dark cool purple"},
			{Hex: "#5A4030", Name: "heavy dark warm brown"},
		},
	},
	{
		Name: "Light Summer",
		BestColor: []Color{
			{Hex: "#B8CCD8", Name: "soft cool blue-gray"},
			{Hex: "#C0D0E0", Name: "light icy blue"},
			{Hex: "#C8B8D0", Name: "soft cool lavender"},
			{Hex: "#E0C8D0", Name: "soft cool rose"},
			{Hex: "#B8C8D0", Name: "cool gray-blue"},
			{Hex: "#D0C8E0", Name: "pale cool lilac"},
			{Hex: "#D8E4EC", Name: "very light cool blue"},
			{Hex: "#F4F0F8", Name: "cool near-white"},
		},
		AvoidColor: []Color{
			{Hex: "#D4622A", Name: "warm burnt orange"},
			{Hex: "#C84820", Name: "warm dark rust"},
			{Hex: "#B87800", Name: "warm dark golden amber"},
			{Hex: "#8C4A18", Name: "warm brown"},
			{Hex: "#A03820", Name: "warm deep rust-red"},
			{Hex: "#784010", Name: "dark warm brown"},
			{Hex: "#C06030", Name: "warm terracotta"},
			{Hex: "#905020", Name: "warm caramel brown"},
		},
	},
	{
		Name: "Cool Summer",
		BestColor: []Color{
			{Hex: "#7A90A8", Name: "cool medium blue-gray"},
			{Hex: "#9098B8", Name: "cool dusty periwinkle"},
			{Hex: "#A888A0", Name: "cool muted mauve"},
			{Hex: "#B89898", Name: "cool dusty rose"},
			{Hex: "#7A9890", Name: "cool muted teal-gray"},
			{Hex: "#9090A8", Name: "cool gray-purple"},
			{Hex: "#C0A8B8", Name: "cool soft pink-gray"},
			{Hex: "#F0EEF4", Name: "cool soft white"},
		},
		AvoidColor: []Color{
			{Hex: "#C87830", Name: "warm amber orange"},
			{Hex: "#D4A030", Name: "warm golden yellow"},
			{Hex: "#C06828", Name: "warm rust"},
			{Hex: "#A07848", Name: "warm tan"},
			{Hex: "#B89060", Name: "warm camel"},
			{Hex: "#8A6040", Name: "warm medium brown"},
			{Hex: "#D49850", Name: "warm peach-gold"},
			{Hex: "#904820", Name: "warm dark rust"},
		},
	},
	{
		Name: "Soft Summer",
		BestColor: []Color{
			{Hex: "#A0A098", Name: "dusty neutral gray"},
			{Hex: "#9898A8", Name: "dusty cool gray-purple"},
			{Hex: "#8AA098", Name: "dusty cool sage"},
			{Hex: "#A89098", Name: "dusty cool rose-gray"},
			{Hex: "#B0A8B8", Name: "dusty cool lavender-gray"},
			{Hex: "#C0B0B0", Name: "soft dusty pink-gray"},
			{Hex: "#B8C0C8", Name: "soft dusty blue-gray"},
			{Hex: "#E8E4E0", Name: "soft neutral off-white"},
		},
		AvoidColor: []Color{
			{Hex: "#E83020", Name: "bright warm red"},
			{Hex: "#B87800", Name: "bright warm amber"},
			{Hex: "#30C890", Name: "bright cool green"},
			{Hex: "#E83080", Name: "bright warm magenta"},
			{Hex: "#1060D0", Name: "bright saturated blue"},
			{Hex: "#D03870", Name: "vivid warm rose"},
			{Hex: "#101010", Name: "pure black"},
			{Hex: "#E86020", Name: "bright warm orange"},
		},
	},
	{
		Name: "Soft Autumn",
		BestColor: []Color{
			{Hex: "#C4936A", Name: "muted warm terracotta"},
			{Hex: "#D8B898", Name: "soft warm beige-tan"},
			{Hex: "#B8B090", Name: "muted warm khaki"},
			{Hex: "#A8A880", Name: "dusty warm olive"},
			{Hex: "#708060", Name: "muted warm olive green"},
			{Hex: "#B89870", Name: "warm muted camel"},
			{Hex: "#D0C898", Name: "warm pale khaki"},
			{Hex: "#EEE8D8", Name: "warm soft cream"},
		},
		AvoidColor: []Color{
			{Hex: "#3070C0", Name: "cool bright blue"},
			{Hex: "#5050C8", Name: "cool medium blue"},
			{Hex: "#8030B8", Name: "cool purple"},
			{Hex: "#C030A0", Name: "cool magenta"},
			{Hex: "#F0F8FF", Name: "icy cool white"},
			{Hex: "#B020A0", Name: "cool vivid purple"},
			{Hex: "#2848A0", Name: "cool dark navy"},
			{Hex: "#20B0D8", Name: "cool bright teal"},
		},
	},
	{
		Name: "Warm Autumn",
		BestColor: []Color{
			{Hex: "#B85C20", Name: "rich warm rust"},
			{Hex: "#C89050", Name: "warm golden amber"},
			{Hex: "#A06830", Name: "warm medium brown"},
			{Hex: "#688030", Name: "warm olive green"},
			{Hex: "#304820", Name: "deep warm forest green"},
			{Hex: "#986040", Name: "warm caramel"},
			{Hex: "#D0A040", Name: "warm mustard gold"},
			{Hex: "#F8EED0", Name: "warm ivory cream"},
		},
		AvoidColor: []Color{
			{Hex: "#20A8D0", Name: "cool bright teal-blue"},
			{Hex: "#40B8E0", Name: "cool sky blue"},
			{Hex: "#A020C0", Name: "cool vivid purple"},
			{Hex: "#8040E0", Name: "cool bright violet"},
			{Hex: "#C8F0F8", Name: "cool icy light blue"},
			{Hex: "#E040B8", Name: "cool magenta"},
			{Hex: "#3060D0", Name: "cool medium blue"},
			{Hex: "#C0A8D8", Name: "cool lavender"},
		},
	},
	{
		Name: "Deep Autumn",
		BestColor: []Color{
			{Hex: "#5A2808", Name: "deep dark warm brown"},
			{Hex: "#7A4220", Name: "rich warm chestnut"},
			{Hex: "#8C5A28", Name: "warm medium brown"},
			{Hex: "#9A7840", Name: "warm dark camel"},
			{Hex: "#506028", Name: "deep warm army green"},
			{Hex: "#384018", Name: "very deep warm olive"},
			{Hex: "#B05C18", Name: "warm rust-amber"},
			{Hex: "#D8C090", Name: "warm light tan (contrast anchor)"},
		},
		AvoidColor: []Color{
			{Hex: "#90E8F8", Name: "icy cool cyan"},
			{Hex: "#A0B8F8", Name: "cool periwinkle"},
			{Hex: "#C0B0F8", Name: "cool lilac"},
			{Hex: "#F8F4FF", Name: "icy cool white"},
			{Hex: "#40D0F0", Name: "cool bright aqua"},
			{Hex: "#E0F8F8", Name: "cool ice blue"},
			{Hex: "#80B0F8", Name: "cool medium blue"},
			{Hex: "#3080E8", Name: "cool saturated blue"},
		},
	},
	{
		Name: "Clear Winter",
		BestColor: []Color{
			{Hex: "#902098", Name: "vivid cool magenta-purple"},
			{Hex: "#7820D8", Name: "vivid cool purple"},
			{Hex: "#1860E8", Name: "clear cool blue"},
			{Hex: "#00A8D8", Name: "clear cool cyan-blue"},
			{Hex: "#00C8B0", Name: "clear cool blue-green"},
			{Hex: "#B020A8", Name: "clear cool fuchsia"},
			{Hex: "#F0F0F8", Name: "cool crisp white"},
			{Hex: "#181828", Name: "cool near-black"},
		},
		AvoidColor: []Color{
			{Hex: "#D8A870", Name: "warm tan beige"},
			{Hex: "#C88050", Name: "warm caramel"},
			{Hex: "#A07850", Name: "warm medium brown"},
			{Hex: "#B89858", Name: "warm khaki"},
			{Hex: "#C8C090", Name: "warm pale khaki"},
			{Hex: "#706040", Name: "warm dark olive"},
			{Hex: "#B86820", Name: "warm rust"},
			{Hex: "#E8D8B8", Name: "warm cream"},
		},
	},
	{
		Name: "Cool Winter",
		BestColor: []Color{
			{Hex: "#101018", Name: "near-black cool"},
			{Hex: "#F4F4F8", Name: "crisp cool white"},
			{Hex: "#182858", Name: "deep cool navy"},
			{Hex: "#601878", Name: "cool deep plum"},
			{Hex: "#680870", Name: "cool deep wine-purple"},
			{Hex: "#183898", Name: "cool royal blue"},
			{Hex: "#284880", Name: "cool dark slate-blue"},
			{Hex: "#500050", Name: "deep cool violet-black"},
		},
		AvoidColor: []Color{
			{Hex: "#C8906A", Name: "warm tan"},
			{Hex: "#C8A850", Name: "warm golden"},
			{Hex: "#E8D8A0", Name: "warm pale yellow"},
			{Hex: "#B06828", Name: "warm rust"},
			{Hex: "#A07848", Name: "warm camel"},
			{Hex: "#B09878", Name: "warm dusty tan"},
			{Hex: "#A09060", Name: "warm khaki"},
			{Hex: "#586030", Name: "warm olive"},
		},
	},
	{
		Name: "Deep Winter",
		BestColor: []Color{
			{Hex: "#101018", Name: "deep cool black"},
			{Hex: "#181830", Name: "very dark cool navy-black"},
			{Hex: "#182050", Name: "deep cool navy"},
			{Hex: "#380898", Name: "deep cool indigo"},
			{Hex: "#680898", Name: "deep cool purple"},
			{Hex: "#500860", Name: "deep cool indigo-wine"},
			{Hex: "#480868", Name: "deep cool purple-wine"},
			{Hex: "#E8EAF0", Name: "cool icy light (contrast anchor)"},
		},
		AvoidColor: []Color{
			{Hex: "#F8D898", Name: "warm light peach"},
			{Hex: "#F8E8A8", Name: "warm pale yellow"},
			{Hex: "#F4F0C8", Name: "warm ivory"},
			{Hex: "#C8F0B8", Name: "warm mint-green"},
			{Hex: "#F8E8D0", Name: "warm cream beige"},
			{Hex: "#D8B898", Name: "warm soft tan"},
			{Hex: "#C8C898", Name: "warm pale khaki"},
			{Hex: "#E8D8B0", Name: "warm sandy beige"},
		},
	},
}

type ColorAnalysisResponse struct {
	ColorType  string           `json:"color_type"`
	Undertone  UndertoneRespone `json:"undertone"`
	Skintone   SkintoneResponse `json:"skintone"`
	Contrast   ContrastResponse `json:"contrast"`
	BestColors []Color          `json:"best_colors"`
	AvoidColor []Color          `json:"avoid_color"`
}

func FindUndertoneValue(name string) UndertoneValue {
	for _, v := range UndertoneTemplates.Values {
		if strings.EqualFold(name, v.Name) {
			return v
		}
	}
	return UndertoneValue{}
}

func FindSkintoneValue(name string) SkintoneValue {
	for _, v := range SkintoneTemplate.Values {
		// e.g., if API returns "medium", we want to match "Medium Skintone"
		if strings.Contains(strings.ToLower(v.Name), strings.ToLower(name)) {
			return v
		}
	}
	return SkintoneValue{}
}

func FindContrastValue(name string) ContrastValue {
	for _, v := range ContrastTemplate.Values {
		if strings.Contains(strings.ToLower(v.Name), strings.ToLower(name)) {
			return v
		}
	}
	return ContrastValue{}
}

func FindSeasonalPalette(name string) SeasonalPallete {
	for _, v := range SeasonalPalletePresets {
		if strings.EqualFold(name, v.Name) {
			return v
		}
	}
	return SeasonalPallete{}
}
