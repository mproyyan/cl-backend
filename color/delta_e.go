package color

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

// HexToRGB converts a hex string to RGB (0-255).
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

// rgbToXYZ converts RGB to XYZ color space.
func rgbToXYZ(r, g, b float64) (x, y, z float64) {
	r = r / 255.0
	g = g / 255.0
	b = b / 255.0

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

// xyzToLab converts XYZ to LAB color space.
func xyzToLab(x, y, z float64) (L, a, b float64) {
	Xn, Yn, Zn := 0.95047, 1.00000, 1.08883
	fx := x / Xn
	fy := y / Yn
	fz := z / Zn

	f := func(t float64) float64 {
		if t > 0.008856 {
			return math.Pow(t, 1.0/3.0)
		}
		return 7.787*t + 16.0/116.0
	}

	L = 116.0*f(fy) - 16.0
	a = 500.0 * (f(fx) - f(fy))
	b = 200.0 * (f(fy) - f(fz))
	return L, a, b
}

// HexToLab converts a hex string to LAB color space.
func HexToLab(hex string) (L, a, b float64, err error) {
	r, g, bVal, err := HexToRGB(hex)
	if err != nil {
		return 0, 0, 0, err
	}
	x, y, z := rgbToXYZ(r, g, bVal)
	L, a, b = xyzToLab(x, y, z)
	return L, a, b, nil
}

// DeltaE computes the CIE76 perceptual color difference.
func DeltaE(hex1, hex2 string) (float64, error) {
	L1, a1, b1, err := HexToLab(hex1)
	if err != nil {
		return 0, err
	}
	L2, a2, b2, err := HexToLab(hex2)
	if err != nil {
		return 0, err
	}
	return math.Sqrt(math.Pow(L1-L2, 2) + math.Pow(a1-a2, 2) + math.Pow(b1-b2, 2)), nil
}

// DeltaEToScore converts a DeltaE value to a match score.
func DeltaEToScore(dE float64) float64 {
	var score float64
	if dE < 5 {
		score = 1.0
	} else if dE >= 5 && dE < 10 {
		score = 0.85 - (dE-5)*0.030
	} else if dE >= 10 && dE < 20 {
		score = 0.70 - (dE-10)*0.025
	} else if dE >= 20 && dE < 35 {
		score = 0.45 - (dE-20)*0.020
	} else if dE >= 35 && dE < 50 {
		score = 0.15 - (dE-35)*0.005
	} else {
		score = 0.0
	}

	if score < 0.0 {
		score = 0.0
	} else if score > 1.0 {
		score = 1.0
	}
	return score
}

// AvoidPenalty converts a DeltaE value to a penalty score.
func AvoidPenalty(dE float64) float64 {
	var penalty float64
	if dE < 5 {
		penalty = 1.0
	} else if dE >= 5 && dE < 15 {
		penalty = 0.90 - (dE-5)*0.050
	} else if dE >= 15 && dE < 30 {
		penalty = 0.40 - (dE-15)*0.020
	} else {
		penalty = 0.0
	}

	if penalty < 0.0 {
		penalty = 0.0
	} else if penalty > 1.0 {
		penalty = 1.0
	}
	return penalty
}

// HexToHSL converts a hex string to HSL color space.
func HexToHSL(hex string) (h, s, l float64, err error) {
	r, g, b, err := HexToRGB(hex)
	if err != nil {
		return 0, 0, 0, err
	}

	r = r / 255.0
	g = g / 255.0
	b = b / 255.0

	max := math.Max(r, math.Max(g, b))
	min := math.Min(r, math.Min(g, b))
	l = (max + min) / 2.0

	if max == min {
		h = 0
		s = 0
	} else {
		d := max - min
		if l > 0.5 {
			s = d / (2.0 - max - min)
		} else {
			s = d / (max + min)
		}

		switch max {
		case r:
			if g < b {
				h = (g-b)/d + 6.0
			} else {
				h = (g-b)/d
			}
		case g:
			h = (b-r)/d + 2.0
		case b:
			h = (r-g)/d + 4.0
		}
		h = h * 60.0
	}

	return h, s, l, nil
}

// OutfitCoherence calculates a coherence score for a set of hex colors.
func OutfitCoherence(hexes []string) float64 {
	var saturatedHues []float64
	for _, hex := range hexes {
		if hex == "" {
			continue
		}
		h, s, _, err := HexToHSL(hex)
		if err == nil && s > 0.10 {
			saturatedHues = append(saturatedHues, h)
		}
	}

	if len(saturatedHues) < 2 {
		return 0.8
	}

	var totalDiff float64
	var count int
	for i := 0; i < len(saturatedHues); i++ {
		for j := i + 1; j < len(saturatedHues); j++ {
			diff := math.Abs(saturatedHues[i] - saturatedHues[j])
			minDiff := math.Min(diff, 360.0-diff)
			totalDiff += minDiff
			count++
		}
	}

	avgDiff := totalDiff / float64(count)

	if avgDiff < 30 {
		return 1.00
	} else if avgDiff < 60 {
		return 0.85
	} else if avgDiff < 120 {
		return 0.65
	}
	return 0.40
}
