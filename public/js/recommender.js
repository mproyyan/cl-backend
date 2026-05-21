const HEX_REGEX = /^#[0-9a-fA-F]{6}$/;

// Recommender Input Elements
const bestInput = document.getElementById("bestInput");
const avoidInput = document.getElementById("avoidInput");
const bestColorsContainer = document.getElementById("bestColors");
const avoidColorsContainer = document.getElementById("avoidColors");
const bestPreview = document.getElementById("bestPreview");
const avoidPreview = document.getElementById("avoidPreview");
const recommendBtn = document.getElementById("recommendBtn");
const resultsContainer = document.getElementById("results");
const presetSelect = document.getElementById("presetSelect");
const genderSelect = document.getElementById("gender");

// State variables
let bestColors = [];
let avoidColors = [];

// Color Presets mapping
const presets = {
    "Bright Spring": {
        best: ["#FF6B6B", "#FF8E3C", "#FFD93D", "#00C2A8", "#00A6FB", "#4D96FF", "#FF4FA3", "#FFFFFF"],
        avoid: ["#6B705C", "#7F5539", "#5C677D", "#8D99AE", "#A5A58D", "#4A4E69", "#2D2A32", "#B08968"]
    },
    "True Spring": {
        best: ["#FFA552", "#FFC857", "#F4D35E", "#06D6A0", "#2EC4B6", "#70E000", "#FF7F51", "#FFF4E6"],
        avoid: ["#4A4E69", "#22223B", "#5C677D", "#8D99AE", "#3C096C", "#6C757D", "#2B2D42", "#495057"]
    },
    "Light Spring": {
        best: ["#FFD6A5", "#FFE5B4", "#FFF3B0", "#CAFFBF", "#9BF6FF", "#A0C4FF", "#FFC6FF", "#FFFFFF"],
        avoid: ["#3D405B", "#2B2D42", "#5C677D", "#6D6875", "#4A4E69", "#7F5539", "#432818", "#1B263B"]
    },
    "Light Summer": {
        best: ["#D8E2DC", "#CDE7F0", "#A9DEF9", "#CBC0D3", "#F7D6E0", "#B8C0FF", "#E2ECE9", "#FFFFFF"],
        avoid: ["#FF6B35", "#E63946", "#D00000", "#FF8800", "#6A040F", "#9D0208", "#7B2CBF", "#3A0CA3"]
    },
    "True Summer": {
        best: ["#B8C0D6", "#A2D2FF", "#CDB4DB", "#E0B1CB", "#84A59D", "#A5A58D", "#DDE5B6", "#F8F9FA"],
        avoid: ["#FF5A5F", "#FF8500", "#FFB703", "#FB5607", "#8338EC", "#3A86FF", "#D90429", "#111111"]
    },
    "Soft Summer": {
        best: ["#B7B7A4", "#A5A58D", "#6B9080", "#84A59D", "#9A8C98", "#C9ADA7", "#D8E2DC", "#EDF2F4"],
        avoid: ["#FF0000", "#FFD60A", "#00F5D4", "#3A86FF", "#8338EC", "#F72585", "#000000", "#FF7F11"]
    },
    "Soft Autumn": {
        best: ["#CB997E", "#DDBEA9", "#B7B7A4", "#A5A58D", "#6B705C", "#B08968", "#CCD5AE", "#E9EDC9"],
        avoid: ["#00A6FB", "#4361EE", "#7209B7", "#F72585", "#FFFFFF", "#C1121F", "#3A0CA3", "#1D3557"]
    },
    "True Autumn": {
        best: ["#BC6C25", "#D4A373", "#CCD5AE", "#606C38", "#283618", "#A98467", "#E09F3E", "#FEFAE0"],
        avoid: ["#00BBF9", "#4CC9F0", "#B5179E", "#7209B7", "#E0FBFC", "#FFFFFF", "#3A86FF", "#C77DFF"]
    },
    "Deep Autumn": {
        best: ["#582F0E", "#7F5539", "#936639", "#A68A64", "#656D4A", "#414833", "#BC6C25", "#FEFAE0"],
        avoid: ["#9BF6FF", "#A0C4FF", "#BDB2FF", "#FFC6FF", "#FFFFFF", "#00F5D4", "#48CAE4", "#3A86FF"]
    },
    "Bright Winter": {
        best: ["#FF006E", "#8338EC", "#3A86FF", "#00BBF9", "#00F5D4", "#F72585", "#FFFFFF", "#111111"],
        avoid: ["#DDBEA9", "#CB997E", "#A5A58D", "#B08968", "#CCD5AE", "#6B705C", "#BC6C25", "#E9EDC9"]
    },
    "True Winter": {
        best: ["#000000", "#FFFFFF", "#1D3557", "#3A86FF", "#8338EC", "#FF006E", "#00BBF9", "#C1121F"],
        avoid: ["#D4A373", "#CCD5AE", "#E9EDC9", "#BC6C25", "#A98467", "#B7B7A4", "#A5A58D", "#606C38"]
    },
    "Deep Winter": {
        best: ["#111111", "#1B263B", "#14213D", "#3A0CA3", "#7209B7", "#9D0208", "#C1121F", "#F8F9FA"],
        avoid: ["#FFD6A5", "#FFE5B4", "#FFF3B0", "#CAFFBF", "#FFC6FF", "#DDBEA9", "#CCD5AE", "#E9EDC9"]
    }
};

// Initialize Presets Dropdown
Object.keys(presets).forEach(name => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    presetSelect.appendChild(option);
});

// RENDER COLOR BOXES
function renderColors(container, colors) {
    container.innerHTML = "";
    colors.forEach(hex => {
        const box = document.createElement("div");
        box.className = "color-box";
        box.style.background = hex;
        box.title = "Click to remove";

        const span = document.createElement("span");
        span.textContent = hex.toUpperCase();

        box.appendChild(span);

        box.addEventListener("click", () => {
            const index = colors.indexOf(hex);
            if (index > -1) {
                colors.splice(index, 1);
                renderColors(container, colors);
            }
        });

        container.appendChild(box);
    });
}

// SETUP COLOR INPUT EVENTS
function setupColorInput(input, preview, colorsArr, container) {
    input.addEventListener("input", () => {
        const val = input.value.trim();
        if (HEX_REGEX.test(val)) {
            preview.style.background = val;
        } else {
            preview.style.background = "transparent";
        }
    });

    input.addEventListener("keydown", (e) => {
        if (e.key !== "Enter") return;
        e.preventDefault();

        const value = input.value.trim().toUpperCase();

        if (!HEX_REGEX.test(value)) {
            alert("Invalid HEX color format. Please use #RRGGBB.");
            return;
        }

        if (!colorsArr.includes(value)) {
            colorsArr.push(value);
            renderColors(container, colorsArr);
        }

        input.value = "";
        preview.style.background = "transparent";
    });
}

setupColorInput(bestInput, bestPreview, bestColors, bestColorsContainer);
setupColorInput(avoidInput, avoidPreview, avoidColors, avoidColorsContainer);

// PRESETS SELECTION
presetSelect.addEventListener("change", () => {
    const selected = presets[presetSelect.value];
    if (!selected) {
        bestColors = [];
        avoidColors = [];
    } else {
        bestColors = [...selected.best];
        avoidColors = [...selected.avoid];
    }
    renderColors(bestColorsContainer, bestColors);
    renderColors(avoidColorsContainer, avoidColors);
});

// RECOMMENDATION ENGINE CALL
recommendBtn.addEventListener("click", async () => {
    resultsContainer.innerHTML = `
        <div style="text-align:center; padding:40px;">
            <p style="font-size:18px; color:var(--text-muted);">Finding your matching outfits...</p>
        </div>
    `;

    try {
        const response = await fetch("/api/v1/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                best_colors: bestColors,
                avoid_colors: avoidColors,
                gender: genderSelect.value
            })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || "Failed to fetch recommendations");
        }

        const data = await response.json();
        renderResults(data.results || []);
    } catch (err) {
        resultsContainer.innerHTML = `
            <div style="text-align:center; padding:40px; border: 1px solid var(--danger); border-radius:var(--radius-lg); background:var(--danger-light); color:var(--danger)">
                <p>Error: ${err.message}</p>
            </div>
        `;
    }
});

// RENDER RECOMMENDATION RESULTS
function renderResults(results) {
    resultsContainer.innerHTML = "";

    if (results.length === 0) {
        resultsContainer.innerHTML = `
            <div style="text-align:center; padding:60px 20px;">
                <p style="font-size:18px; color:var(--text-muted); font-weight:600;">No matching outfits found</p>
                <p style="font-size:14px; color:var(--text-muted); margin-top:4px;">Try adding more outfits to your library or adjusting color filters.</p>
            </div>
        `;
        return;
    }

    results.forEach(result => {
        const card = document.createElement("div");
        card.className = "outfit-card";

        const items = result.outfit.items;
        const itemKeys = ["outer", "top", "bottom", "shoes"];
        
        let itemCardsHTML = "";
        itemKeys.forEach(key => {
            const item = items[key];
            if (item && item.name) {
                itemCardsHTML += `
                    <div class="item-card">
                        <div class="item-color-preview" style="background:${item.hex}">
                            <span class="item-badge">${key}</span>
                        </div>
                        <div class="item-info">
                            <div class="item-name">${item.name}</div>
                            <div class="item-color-name">${item.color}</div>
                            <div class="item-hex">${item.hex.toUpperCase()}</div>
                        </div>
                    </div>
                `;
            }
        });

        const reasonsHTML = result.reasons && result.reasons.length > 0 
            ? `<ul class="reasons-list">${result.reasons.map(r => `<li>${r}</li>`).join("")}</ul>`
            : "";

        const envTags = result.outfit.environments ? result.outfit.environments.map(e => `<span class="meta-tag">${e}</span>`).join("") : "";
        const weatherTags = result.outfit.weather_support ? result.outfit.weather_support.map(w => `<span class="meta-tag">${w}</span>`).join("") : "";

        let fallbackImage = "https://placehold.co/600x400/f1f5f9/64748b?text=No+Image";
        let imageUrl = result.outfit.image_url || fallbackImage;
        let imageHTML = `<img src="${imageUrl}" alt="Outfit Image" class="outfit-card-image" />`;
        card.classList.add("has-image");

        card.innerHTML = `
            ${imageHTML}
            <div class="outfit-card-header">
                <div class="header-main">
                    <h2>${result.outfit.name}</h2>
                    <span class="gender-badge ${result.outfit.gender}">${result.outfit.gender}</span>
                </div>
                <div style="display:flex; gap:8px;">
                    <div class="rank-badge">Rank #${result.rank}</div>
                    <div class="score-badge">Match: ${result.score}%</div>
                </div>
            </div>

            <div class="meta-tags">
                <span class="meta-tag accent">${result.outfit.style_tag || "Casual"}</span>
                ${result.outfit.harmony_tag ? `<span class="meta-tag accent">${result.outfit.harmony_tag}</span>` : ""}
                ${result.outfit.undertone ? `<span class="meta-tag">Undertone: ${result.outfit.undertone}</span>` : ""}
                ${result.outfit.contrast_level ? `<span class="meta-tag">Contrast: ${result.outfit.contrast_level}</span>` : ""}
                ${envTags}
                ${weatherTags}
            </div>

            ${reasonsHTML}

            <div class="outfit-items">
                ${itemCardsHTML}
            </div>
        `;

        resultsContainer.appendChild(card);
    });
}
