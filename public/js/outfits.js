// Wardrobe Elements
const searchOutfitInput = document.getElementById("searchOutfitInput");
const outfitsGrid = document.getElementById("outfitsGrid");

let allOutfits = [];

// FETCH ALL OUTFITS
async function fetchOutfits() {
    outfitsGrid.innerHTML = `
        <div style="text-align:center; padding:40px; grid-column: 1 / -1;">
            <p style="font-size:16px; color:var(--text-muted);">Loading outfits...</p>
        </div>
    `;

    try {
        const response = await fetch("/api/v1/outfits");
        if (!response.ok) throw new Error("Failed to fetch outfits list");
        
        allOutfits = await response.json();
        renderOutfitsGrid(allOutfits);
    } catch (err) {
        outfitsGrid.innerHTML = `
            <div style="text-align:center; padding:40px; grid-column: 1 / -1; color:var(--danger);">
                <p>Error loading outfits: ${err.message}</p>
            </div>
        `;
    }
}

// RENDER OUTFITS GRID
function renderOutfitsGrid(outfits) {
    outfitsGrid.innerHTML = "";

    if (outfits.length === 0) {
        outfitsGrid.innerHTML = `
            <div style="text-align:center; padding:60px 20px; grid-column: 1 / -1;">
                <p style="font-size:18px; color:var(--text-muted); font-weight:600;">No outfits in your wardrobe</p>
                <p style="font-size:14px; color:var(--text-muted); margin-top:4px;">Click "Add New Outfit" to create one.</p>
            </div>
        `;
        return;
    }

    outfits.forEach(outfit => {
        const card = document.createElement("div");
        card.className = "outfit-card cursor-pointer";

        // Add redirect listener to the card
        card.addEventListener("click", (e) => {
            // Prevent redirect if clicking the delete button
            if (e.target.closest(".icon-btn.delete")) {
                return;
            }
            window.location.href = `/outfits/edit?id=${outfit.id}`;
        });

        const items = outfit.items;
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

        const envTags = outfit.environments ? outfit.environments.map(e => `<span class="meta-tag">${e}</span>`).join("") : "";
        const weatherTags = outfit.weather_support ? outfit.weather_support.map(w => `<span class="meta-tag">${w}</span>`).join("") : "";

        card.innerHTML = `
            <div class="outfit-card-header">
                <div class="header-main">
                    <h2>${outfit.name}</h2>
                    <span class="gender-badge ${outfit.gender}">${outfit.gender}</span>
                </div>
                <div class="card-actions">
                    <button class="icon-btn delete" title="Delete Outfit">🗑️</button>
                </div>
            </div>

            <div class="meta-tags">
                <span class="meta-tag accent">${outfit.style_tag || "Casual"}</span>
                ${outfit.harmony_tag ? `<span class="meta-tag accent">${outfit.harmony_tag}</span>` : ""}
                ${outfit.undertone ? `<span class="meta-tag">Undertone: ${outfit.undertone}</span>` : ""}
                ${outfit.contrast_level ? `<span class="meta-tag">Contrast: ${outfit.contrast_level}</span>` : ""}
                ${envTags}
                ${weatherTags}
            </div>

            <div class="outfit-items">
                ${itemCardsHTML}
            </div>
        `;

        // Wire up delete button event listener
        const deleteBtn = card.querySelector(".icon-btn.delete");
        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation(); // prevent card click
            deleteOutfit(outfit.id);
        });

        outfitsGrid.appendChild(card);
    });
}

// DELETE OUTFIT ACTION
async function deleteOutfit(id) {
    if (!confirm("Are you sure you want to delete this outfit?")) return;

    try {
        const response = await fetch(`/api/v1/outfits/${id}`, {
            method: "DELETE"
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || "Failed to delete outfit");
        }

        fetchOutfits();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

// SEARCH FILTER
searchOutfitInput.addEventListener("input", () => {
    const query = searchOutfitInput.value.toLowerCase().trim();
    if (!query) {
        renderOutfitsGrid(allOutfits);
        return;
    }

    const filtered = allOutfits.filter(o => {
        const nameMatch = o.name.toLowerCase().includes(query);
        const styleMatch = o.style_tag && o.style_tag.toLowerCase().includes(query);
        const itemsMatch = Object.values(o.items).some(item => 
            item.name && (item.name.toLowerCase().includes(query) || item.color.toLowerCase().includes(query))
        );
        return nameMatch || styleMatch || itemsMatch;
    });

    renderOutfitsGrid(filtered);
});

// Load outfits on start
document.addEventListener("DOMContentLoaded", fetchOutfits);
