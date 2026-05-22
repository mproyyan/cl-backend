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

    // ─────────────────────────────────────────────
    // SPRING — warm undertone, clear energy
    // ─────────────────────────────────────────────

    "Clear Spring": {
        // Warm, vivid, high contrast. Clear saturated warm colors only.
        best: [
            "#E8472A", // vivid warm red-orange
            "#F4763A", // clear tangerine
            "#E8B020", // warm golden yellow
            "#E8C84A", // warm clear yellow
            "#5BAD6A", // warm yellow-green
            "#F28B6E", // bright warm peach-coral
            "#D94F7A", // warm vivid rose
            "#FFF0D6", // warm ivory white
        ],
        // Avoid: muted, dusty, cool, heavy tones
        avoid: [
            "#8C8C78", // dusty warm gray
            "#6B7A8D", // cool blue-gray
            "#7A6E88", // dusty cool purple
            "#5C6650", // muted dark olive
            "#A0896C", // muddy tan
            "#3A3A3A", // heavy charcoal
            "#7C8FA0", // cool slate
            "#9E8E7E", // dusty beige-gray
        ],
    },

    "Warm Spring": {
        // Warm, energetic, medium-high saturation. No dusty or grayish colors.
        best: [
            "#F5963C", // warm amber orange
            "#F2BE3A", // golden warm yellow
            "#D4A800", // deep warm gold
            "#78B040", // warm yellow-green
            "#E07050", // warm terracotta coral
            "#F0C080", // warm peach apricot
            "#C86030", // warm rust-orange
            "#FDF0D0", // warm cream
        ],
        // Avoid: cool, desaturated, dark gray-blue tones
        avoid: [
            "#4A506E", // cool dark navy-gray
            "#7090A8", // cool steel blue
            "#9080A8", // cool dusty purple
            "#606878", // cool blue-gray
            "#8898A8", // cool medium gray-blue
            "#B0A8C0", // cool lavender-gray
            "#3A3050", // deep cool purple-navy
            "#505868", // cool dark slate
        ],
    },

    "Light Spring": {
        // Warm, airy, low-medium contrast only. Soft peachy warm pastels.
        best: [
            "#F8D5A8", // warm peach
            "#FAE0B0", // warm apricot cream
            "#F5E898", // warm pale yellow
            "#C8E0A0", // warm soft yellow-green
            "#F4B8A0", // warm soft coral
            "#E8C8B8", // warm rose beige
            "#F0D0B8", // warm sandy pink
            "#FBF5E8", // warm soft white-cream
        ],
        // Avoid: dark, heavy, cool tones
        avoid: [
            "#2A3050", // dark cool navy
            "#3A3850", // dark cool charcoal-purple
            "#504868", // cool dark plum
            "#284040", // dark cool teal-black
            "#3C3028", // dark heavy warm brown
            "#486050", // dark muted teal-green
            "#2C2840", // very dark cool purple
            "#5A4030", // heavy dark warm brown
        ],
    },

    // ─────────────────────────────────────────────
    // SUMMER — cool undertone, soft/muted energy
    // ─────────────────────────────────────────────

    "Light Summer": {
        // Cool, pastel, delicate. Low contrast. Soft blues, lavenders, cool pinks.
        best: [
            "#B8CCD8", // soft cool blue-gray
            "#C0D0E0", // light icy blue
            "#C8B8D0", // soft cool lavender
            "#E0C8D0", // soft cool rose
            "#B8C8D0", // cool gray-blue
            "#D0C8E0", // pale cool lilac
            "#D8E4EC", // very light cool blue
            "#F4F0F8", // cool near-white
        ],
        // Avoid: warm oranges, rusts, browns
        avoid: [
            "#D4622A", // warm burnt orange
            "#C84820", // warm dark rust
            "#B87800", // warm dark golden amber
            "#8C4A18", // warm brown
            "#A03820", // warm deep rust-red
            "#784010", // dark warm brown
            "#C06030", // warm terracotta
            "#905020", // warm caramel brown
        ],
    },

    "Cool Summer": {
        // Cool, muted, elegant. Medium contrast. No warm earth tones.
        best: [
            "#7A90A8", // cool medium blue-gray
            "#9098B8", // cool dusty periwinkle
            "#A888A0", // cool muted mauve
            "#B89898", // cool dusty rose
            "#7A9890", // cool muted teal-gray
            "#9090A8", // cool gray-purple
            "#C0A8B8", // cool soft pink-gray
            "#F0EEF4", // cool soft white
        ],
        // Avoid: warm amber, rust, brown, golden tones
        avoid: [
            "#C87830", // warm amber orange
            "#D4A030", // warm golden yellow
            "#C06828", // warm rust
            "#A07848", // warm tan
            "#B89060", // warm camel
            "#8A6040", // warm medium brown
            "#D49850", // warm peach-gold
            "#904820", // warm dark rust
        ],
    },

    "Soft Summer": {
        // Cool-neutral, dusty, desaturated. Very low contrast only.
        best: [
            "#A0A098", // dusty neutral gray
            "#9898A8", // dusty cool gray-purple
            "#8AA098", // dusty cool sage
            "#A89098", // dusty cool rose-gray
            "#B0A8B8", // dusty cool lavender-gray
            "#C0B0B0", // soft dusty pink-gray
            "#B8C0C8", // soft dusty blue-gray
            "#E8E4E0", // soft neutral off-white
        ],
        // Avoid: bright, saturated, vivid tones of any family
        avoid: [
            "#E83020", // bright warm red
            "#B87800", // bright warm amber
            "#30C890", // bright cool green
            "#E83080", // bright warm magenta
            "#1060D0", // bright saturated blue
            "#D03870", // vivid warm rose
            "#101010", // pure black
            "#E86020", // bright warm orange
        ],
    },

    // ─────────────────────────────────────────────
    // AUTUMN — warm undertone, earthy/muted energy
    // ─────────────────────────────────────────────

    "Soft Autumn": {
        // Warm, muted, earthy. Low-medium contrast. Soft transitions.
        best: [
            "#C4936A", // muted warm terracotta
            "#D8B898", // soft warm beige-tan
            "#B8B090", // muted warm khaki
            "#A8A880", // dusty warm olive
            "#708060", // muted warm olive green
            "#B89870", // warm muted camel
            "#D0C898", // warm pale khaki
            "#EEE8D8", // warm soft cream
        ],
        // Avoid: cool blues, purples, bright cool tones
        avoid: [
            "#3070C0", // cool bright blue
            "#5050C8", // cool medium blue
            "#8030B8", // cool purple
            "#C030A0", // cool magenta
            "#F0F8FF", // icy cool white
            "#B020A0", // cool vivid purple
            "#2848A0", // cool dark navy
            "#20B0D8", // cool bright teal
        ],
    },

    "Warm Autumn": {
        // Warm, rich, earthy. Medium contrast. Grounded deep tones.
        best: [
            "#B85C20", // rich warm rust
            "#C89050", // warm golden amber
            "#A06830", // warm medium brown
            "#688030", // warm olive green
            "#304820", // deep warm forest green
            "#986040", // warm caramel
            "#D0A040", // warm mustard gold
            "#F8EED0", // warm ivory cream
        ],
        // Avoid: cool blues, teals, cool purples, icy tones
        avoid: [
            "#20A8D0", // cool bright teal-blue
            "#40B8E0", // cool sky blue
            "#A020C0", // cool vivid purple
            "#8040E0", // cool bright violet
            "#C8F0F8", // cool icy light blue
            "#E040B8", // cool magenta
            "#3060D0", // cool medium blue
            "#C0A8D8", // cool lavender
        ],
    },

    "Deep Autumn": {
        // Warm, deep, dark-rich. Medium-high contrast. Heavy earthy depth.
        best: [
            "#5A2808", // deep dark warm brown
            "#7A4220", // rich warm chestnut
            "#8C5A28", // warm medium brown
            "#9A7840", // warm dark camel
            "#506028", // deep warm army green
            "#384018", // very deep warm olive
            "#B05C18", // warm rust-amber
            "#D8C090", // warm light tan (contrast anchor)
        ],
        // Avoid: icy cool blues, pastels, cool light tones
        avoid: [
            "#90E8F8", // icy cool cyan
            "#A0B8F8", // cool periwinkle
            "#C0B0F8", // cool lilac
            "#F8F4FF", // icy cool white
            "#40D0F0", // cool bright aqua
            "#E0F8F8", // cool ice blue
            "#80B0F8", // cool medium blue
            "#3080E8", // cool saturated blue
        ],
    },

    // ─────────────────────────────────────────────
    // WINTER — cool undertone, pure/sharp energy
    // ─────────────────────────────────────────────

    "Clear Winter": {
        // Cool, vivid, high contrast. Clear saturated cool colors.
        // Reds replaced with cool fuchsia/magenta — Winter reds are
        // always magenta-leaning, never orange-leaning.
        best: [
            "#902098", // vivid cool magenta-purple
            "#7820D8", // vivid cool purple
            "#1860E8", // clear cool blue
            "#00A8D8", // clear cool cyan-blue
            "#00C8B0", // clear cool blue-green
            "#B020A8", // clear cool fuchsia
            "#F0F0F8", // cool crisp white
            "#181828", // cool near-black
        ],
        // Avoid: warm tans, camels, khakis, warm creams
        avoid: [
            "#D8A870", // warm tan beige
            "#C88050", // warm caramel
            "#A07850", // warm medium brown
            "#B89858", // warm khaki
            "#C8C090", // warm pale khaki
            "#706040", // warm dark olive
            "#B86820", // warm rust
            "#E8D8B8", // warm cream
        ],
    },

    "Cool Winter": {
        // Cool, pure, maximum contrast. Navy, white, black, cool jewel tones.
        // Deep wine/plum used instead of warm red — True Winter reds are
        // cool plum-reds and wine tones, not orange-reds.
        best: [
            "#101018", // near-black cool
            "#F4F4F8", // crisp cool white
            "#182858", // deep cool navy
            "#601878", // cool deep plum
            "#680870", // cool deep wine-purple
            "#183898", // cool royal blue
            "#284880", // cool dark slate-blue
            "#500050", // deep cool violet-black
        ],
        // Avoid: warm goldens, tans, khakis, warm olives
        avoid: [
            "#C8906A", // warm tan
            "#C8A850", // warm golden
            "#E8D8A0", // warm pale yellow
            "#B06828", // warm rust
            "#A07848", // warm camel
            "#B09878", // warm dusty tan
            "#A09060", // warm khaki
            "#586030", // warm olive
        ],
    },

    "Deep Winter": {
        // Cool, deep, dramatic. Dark cool tones with strong depth.
        // Deep indigo and plum-wine replace warm reds.
        best: [
            "#101018", // deep cool black
            "#181830", // very dark cool navy-black
            "#182050", // deep cool navy
            "#380898", // deep cool indigo
            "#680898", // deep cool purple
            "#500860", // deep cool indigo-wine
            "#480868", // deep cool purple-wine
            "#E8EAF0", // cool icy light (contrast anchor)
        ],
        // Avoid: warm peaches, warm yellows, warm creams, warm pastels
        avoid: [
            "#F8D898", // warm light peach
            "#F8E8A8", // warm pale yellow
            "#F4F0C8", // warm ivory
            "#C8F0B8", // warm mint-green
            "#F8E8D0", // warm cream beige
            "#D8B898", // warm soft tan
            "#C8C898", // warm pale khaki
            "#E8D8B0", // warm sandy beige
        ],
    },
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
