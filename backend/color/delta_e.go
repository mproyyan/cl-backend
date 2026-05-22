package color

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

// HexToRGB converts a hex string to RGB (0-255).
// Signature unchanged — called externally.
func HexToRGB(hex string) (r, g, b float64, err error) {
	hex = strings.TrimPrefix(hex, "#")
	if len(hex) != 6 {
		return 0, 0, 0, fmt.Errorf("invalid hex length")
	}
	rInt, err := strconv.ParseInt(hex[0:2], 16, 64)
	if err != nil {
		return 0, 0, 0, err
	}
	gInt, err := strconv.ParseInt(hex[2:4], 16, 64)
	if err != nil {
		return 0, 0, 0, err
	}
	bInt, err := strconv.ParseInt(hex[4:6], 16, 64)
	if err != nil {
		return 0, 0, 0, err
	}
	return float64(rInt), float64(gInt), float64(bInt), nil
}

// rgbToXYZ converts linear RGB to CIE XYZ (D65).
func rgbToXYZ(r, g, b float64) (x, y, z float64) {
	r /= 255.0
	g /= 255.0
	b /= 255.0

	linearize := func(c float64) float64 {
		if c > 0.04045 {
			return math.Pow((c+0.055)/1.055, 2.4)
		}
		return c / 12.92
	}

	r = linearize(r)
	g = linearize(g)
	b = linearize(b)

	x = r*0.4124564 + g*0.3575761 + b*0.1804375
	y = r*0.2126729 + g*0.7151522 + b*0.0721750
	z = r*0.0193339 + g*0.1191920 + b*0.9503041
	return x, y, z
}

// xyzToLab converts CIE XYZ to CIE L*a*b*.
func xyzToLab(x, y, z float64) (L, a, b float64) {
	const Xn, Yn, Zn = 0.95047, 1.00000, 1.08883

	f := func(t float64) float64 {
		if t > 0.008856 {
			return math.Pow(t, 1.0/3.0)
		}
		return 7.787*t + 16.0/116.0
	}

	L = 116.0*f(y/Yn) - 16.0
	a = 500.0 * (f(x/Xn) - f(y/Yn))
	b = 200.0 * (f(y/Yn) - f(z/Zn))
	return L, a, b
}

// HexToLab converts a hex string to CIE L*a*b*.
// Signature unchanged — called externally.
func HexToLab(hex string) (L, a, b float64, err error) {
	r, g, bVal, err := HexToRGB(hex)
	if err != nil {
		return 0, 0, 0, err
	}
	x, y, z := rgbToXYZ(r, g, bVal)
	L, a, b = xyzToLab(x, y, z)
	return L, a, b, nil
}

// DeltaE computes CIEDE2000 perceptual color difference.
// Upgraded from CIE76 — signature unchanged, callers unaffected.
// CIEDE2000 is significantly more accurate for blues and dark colors,
// which are critical for cool-palette seasonal types (Deep Winter, True Summer, etc.).
func DeltaE(hex1, hex2 string) (float64, error) {
	L1, a1, b1, err := HexToLab(hex1)
	if err != nil {
		return 0, err
	}
	L2, a2, b2, err := HexToLab(hex2)
	if err != nil {
		return 0, err
	}
	return ciede2000(L1, a1, b1, L2, a2, b2), nil
}

// ciede2000 implements the CIEDE2000 color difference formula.
// Reference: Sharma et al. (2005), "The CIEDE2000 Color-Difference Formula".
func ciede2000(L1, a1, b1, L2, a2, b2 float64) float64 {
	// Step 1: compute C*ab and h*ab
	C1 := math.Sqrt(a1*a1 + b1*b1)
	C2 := math.Sqrt(a2*a2 + b2*b2)
	Cbar := (C1 + C2) / 2.0
	Cbar7 := math.Pow(Cbar, 7)
	denom := Cbar7 + math.Pow(25, 7)
	G := 0.5 * (1 - math.Sqrt(Cbar7/denom))

	a1p := a1 * (1 + G)
	a2p := a2 * (1 + G)

	C1p := math.Sqrt(a1p*a1p + b1*b1)
	C2p := math.Sqrt(a2p*a2p + b2*b2)

	h1p := math.Atan2(b1, a1p)
	if h1p < 0 {
		h1p += 2 * math.Pi
	}
	h2p := math.Atan2(b2, a2p)
	if h2p < 0 {
		h2p += 2 * math.Pi
	}

	// Step 2: deltas
	dLp := L2 - L1
	dCp := C2p - C1p

	var dhp float64
	if C1p*C2p == 0 {
		dhp = 0
	} else if math.Abs(h2p-h1p) <= math.Pi {
		dhp = h2p - h1p
	} else if h2p-h1p > math.Pi {
		dhp = h2p - h1p - 2*math.Pi
	} else {
		dhp = h2p - h1p + 2*math.Pi
	}
	dHp := 2 * math.Sqrt(C1p*C2p) * math.Sin(dhp/2)

	// Step 3: CIEDE2000 weighting
	Lbarp := (L1 + L2) / 2.0
	Cbarp := (C1p + C2p) / 2.0

	var Hbarp float64
	if C1p*C2p == 0 {
		Hbarp = h1p + h2p
	} else if math.Abs(h1p-h2p) <= math.Pi {
		Hbarp = (h1p + h2p) / 2.0
	} else if h1p+h2p < 2*math.Pi {
		Hbarp = (h1p + h2p + 2*math.Pi) / 2.0
	} else {
		Hbarp = (h1p + h2p - 2*math.Pi) / 2.0
	}

	T := 1 -
		0.17*math.Cos(Hbarp-degToRad(30)) +
		0.24*math.Cos(2*Hbarp) +
		0.32*math.Cos(3*Hbarp+degToRad(6)) -
		0.20*math.Cos(4*Hbarp-degToRad(63))

	SL := 1 + 0.015*math.Pow(Lbarp-50, 2)/math.Sqrt(20+math.Pow(Lbarp-50, 2))
	SC := 1 + 0.045*Cbarp
	SH := 1 + 0.015*Cbarp*T

	Cbarp7 := math.Pow(Cbarp, 7)
	RC := 2 * math.Sqrt(Cbarp7/(Cbarp7+math.Pow(25, 7)))
	dTheta := degToRad(30) * math.Exp(-math.Pow((Hbarp-degToRad(275))/degToRad(25), 2))
	RT := -math.Sin(2*dTheta) * RC

	dE := math.Sqrt(
		math.Pow(dLp/SL, 2) +
			math.Pow(dCp/SC, 2) +
			math.Pow(dHp/SH, 2) +
			RT*(dCp/SC)*(dHp/SH),
	)
	return dE
}

func degToRad(deg float64) float64 {
	return deg * math.Pi / 180.0
}

// DeltaEToScore converts a CIEDE2000 value to a [0,1] match score.
// Thresholds recalibrated for CIEDE2000 scale (CIEDE2000 values are
// perceptually tighter than CIE76 — a dE of 2 is already noticeable).
// Signature unchanged — called externally.
func DeltaEToScore(dE float64) float64 {
	var score float64
	switch {
	case dE < 3:
		// Near-identical match
		score = 1.0
	case dE < 8:
		// Close match — slight perceptual difference
		score = 0.90 - (dE-3)*0.030
	case dE < 18:
		// Similar family but distinct shade
		score = 0.75 - (dE-8)*0.025
	case dE < 30:
		// Related but noticeably different
		score = 0.50 - (dE-18)*0.020
	case dE < 45:
		// Distant — different color family
		score = 0.26 - (dE-30)*0.010
	default:
		score = 0.0
	}
	return math.Max(0.0, math.Min(1.0, score))
}

// AvoidPenalty converts a CIEDE2000 value to a [0,1] penalty score.
// Decay is steeper than DeltaEToScore so avoid-colors have a sharp, localised effect.
// Signature unchanged — called externally.
func AvoidPenalty(dE float64) float64 {
	var penalty float64
	switch {
	case dE < 3:
		// Essentially the same color — full penalty
		penalty = 1.0
	case dE < 12:
		// Close to avoid color — strong penalty that decays
		penalty = 0.90 - (dE-3)*0.055
	case dE < 25:
		// Noticeable distance — moderate residual penalty
		penalty = 0.40 - (dE-12)*0.025
	default:
		// Far enough — no penalty
		penalty = 0.0
	}
	return math.Max(0.0, math.Min(1.0, penalty))
}

// HexToHSL converts a hex string to HSL (h in degrees 0-360, s and l in 0-1).
// Signature unchanged — called externally.
func HexToHSL(hex string) (h, s, l float64, err error) {
	r, g, b, err := HexToRGB(hex)
	if err != nil {
		return 0, 0, 0, err
	}

	r /= 255.0
	g /= 255.0
	b /= 255.0

	maxC := math.Max(r, math.Max(g, b))
	minC := math.Min(r, math.Min(g, b))
	l = (maxC + minC) / 2.0

	if maxC == minC {
		return 0, 0, l, nil
	}

	d := maxC - minC
	if l > 0.5 {
		s = d / (2.0 - maxC - minC)
	} else {
		s = d / (maxC + minC)
	}

	switch maxC {
	case r:
		h = (g - b) / d
		if g < b {
			h += 6.0
		}
	case g:
		h = (b-r)/d + 2.0
	case b:
		h = (r-g)/d + 4.0
	}
	h *= 60.0

	return h, s, l, nil
}

// undertoneScore classifies how warm (+1.0) or cool (-1.0) a hue is.
// Warm: reds, oranges, yellows, yellow-greens (hue 0-80, 330-360).
// Cool: blues, blue-greens, purples (hue 180-300).
// Neutral zone in between scores near 0.
func undertoneScore(h, s, l float64) float64 {
	// Achromatic colors (gray, white, black) are undertone-neutral
	if s < 0.08 || l < 0.08 || l > 0.95 {
		return 0.0
	}

	// Map hue to a warm/cool axis in [-1, 1]
	// Warm peak around hue 30 (orange), cool peak around hue 240 (blue)
	radH := h * math.Pi / 180.0
	// cos(hue - 30°) gives +1 at warm peak, -1 at cool peak
	warmCoolAxis := math.Cos(radH - degToRad(30))

	// Scale by saturation so pale/muted colors contribute less
	return warmCoolAxis * s
}

// OutfitCoherence calculates a coherence score [0,1] for a set of hex colors.
//
// Improvements over original:
//  1. Undertone conflict penalty — warm+cool mixing is the primary violation
//     in seasonal color analysis and now receives a hard deduction.
//  2. Hue spread still contributes but is weighted less than undertone consistency.
//
// Signature unchanged — called externally.
func OutfitCoherence(hexes []string) float64 {
	type colorInfo struct {
		h, s, l   float64
		undertone float64 // warm > 0, cool < 0, neutral ≈ 0
	}

	var colors []colorInfo
	for _, hex := range hexes {
		if hex == "" {
			continue
		}
		h, s, l, err := HexToHSL(hex)
		if err != nil {
			continue
		}
		colors = append(colors, colorInfo{
			h:         h,
			s:         s,
			l:         l,
			undertone: undertoneScore(h, s, l),
		})
	}

	if len(colors) < 2 {
		return 0.80
	}

	// --- Component 1: undertone consistency ---
	// Collect non-neutral items (|undertone| > 0.15 means the color has
	// a meaningful warm or cool lean after saturation weighting).
	var warmCount, coolCount int
	for _, c := range colors {
		if c.undertone > 0.15 {
			warmCount++
		} else if c.undertone < -0.15 {
			coolCount++
		}
	}

	// Undertone conflict = both warm and cool items present
	undertoneScore := 1.0
	if warmCount > 0 && coolCount > 0 {
		// Severity scales with how many items are on the minority side
		minority := math.Min(float64(warmCount), float64(coolCount))
		majority := math.Max(float64(warmCount), float64(coolCount))
		conflictRatio := minority / majority
		// conflictRatio 1.0 (equal split) → deduction 0.50; 0.33 → deduction ~0.25
		undertoneScore = 1.0 - 0.50*conflictRatio
	}

	// --- Component 2: hue spread (analogous vs complementary) ---
	var saturatedHues []float64
	for _, c := range colors {
		if c.s > 0.10 {
			saturatedHues = append(saturatedHues, c.h)
		}
	}

	hueScore := 0.85 // default when not enough saturated colors to compare
	if len(saturatedHues) >= 2 {
		var totalDiff float64
		var count int
		for i := 0; i < len(saturatedHues); i++ {
			for j := i + 1; j < len(saturatedHues); j++ {
				diff := math.Abs(saturatedHues[i] - saturatedHues[j])
				totalDiff += math.Min(diff, 360.0-diff)
				count++
			}
		}
		avgDiff := totalDiff / float64(count)

		switch {
		case avgDiff < 30:
			hueScore = 1.00 // monochromatic / analogous
		case avgDiff < 60:
			hueScore = 0.85 // close analogous
		case avgDiff < 120:
			hueScore = 0.65 // split-complementary territory
		default:
			hueScore = 0.40 // wide complementary or discordant
		}
	}

	// --- Final coherence: undertone weighted more heavily ---
	// Undertone consistency is the primary rule in seasonal color analysis.
	// Hue spread matters but is secondary.
	coherence := 0.65*undertoneScore + 0.35*hueScore
	return math.Max(0.0, math.Min(1.0, coherence))
}
