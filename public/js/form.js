const HEX_REGEX = /^#[0-9a-fA-F]{6}$/;

// Form Elements
const outfitForm = document.getElementById("outfitForm");
const formOutfitId = document.getElementById("formOutfitId");
const formName = document.getElementById("formName");
const formGender = document.getElementById("formGender");
const formStyleTag = document.getElementById("formStyleTag");
const formHarmonyTag = document.getElementById("formHarmonyTag");
const formUndertone = document.getElementById("formUndertone");
const formContrastLevel = document.getElementById("formContrastLevel");
const formEnvironments = document.getElementById("formEnvironments");
const formWeatherSupport = document.getElementById("formWeatherSupport");

// Clothes Items Form Inputs
const formTopName = document.getElementById("formTopName");
const formTopColor = document.getElementById("formTopColor");
const formTopHex = document.getElementById("formTopHex");
const formTopColorPicker = document.getElementById("formTopColorPicker");

const formBottomName = document.getElementById("formBottomName");
const formBottomColor = document.getElementById("formBottomColor");
const formBottomHex = document.getElementById("formBottomHex");
const formBottomColorPicker = document.getElementById("formBottomColorPicker");

const formOuterName = document.getElementById("formOuterName");
const formOuterColor = document.getElementById("formOuterColor");
const formOuterHex = document.getElementById("formOuterHex");
const formOuterColorPicker = document.getElementById("formOuterColorPicker");

const formShoesName = document.getElementById("formShoesName");
const formShoesColor = document.getElementById("formShoesColor");
const formShoesHex = document.getElementById("formShoesHex");
const formShoesColorPicker = document.getElementById("formShoesColorPicker");

// COLOR PICKER SYNCHRONIZATION
function syncColorPicker(picker, textInput) {
    picker.addEventListener("input", () => {
        textInput.value = picker.value.toUpperCase();
    });

    textInput.addEventListener("input", () => {
        const val = textInput.value.trim();
        if (HEX_REGEX.test(val)) {
            picker.value = val;
        }
    });
}

syncColorPicker(formTopColorPicker, formTopHex);
syncColorPicker(formBottomColorPicker, formBottomHex);
syncColorPicker(formOuterColorPicker, formOuterHex);
syncColorPicker(formShoesColorPicker, formShoesHex);

// DETECT MODE & LOAD DATA
async function initForm() {
    const urlParams = new URLSearchParams(window.location.search);
    const outfitId = urlParams.get("id");

    if (outfitId) {
        // Edit Mode
        formOutfitId.value = outfitId;
        try {
            const response = await fetch(`/api/v1/outfits/${outfitId}`);
            if (!response.ok) throw new Error("Failed to load outfit detail");

            const outfit = await response.json();
            populateForm(outfit);
        } catch (err) {
            alert("Error loading outfit detail: " + err.message);
            window.location.href = "/outfits";
        }
    } else {
        // Create Mode - Set default picker color values
        formTopColorPicker.value = "#FFFFFF";
        formBottomColorPicker.value = "#000080";
        formOuterColorPicker.value = "#8B4513";
        formShoesColorPicker.value = "#1A1A1A";
        
        formTopHex.value = "#FFFFFF";
        formBottomHex.value = "#000080";
        formOuterHex.value = "#8B4513";
        formShoesHex.value = "#1A1A1A";
    }
}

function populateForm(outfit) {
    formName.value = outfit.name || "";
    formGender.value = outfit.gender || "unisex";
    formStyleTag.value = outfit.style_tag || "";
    formHarmonyTag.value = outfit.harmony_tag || "";
    formUndertone.value = outfit.undertone || "";
    formContrastLevel.value = outfit.contrast_level || "";
    formEnvironments.value = outfit.environments ? outfit.environments.join(", ") : "";
    formWeatherSupport.value = outfit.weather_support ? outfit.weather_support.join(", ") : "";

    // Top Wear
    formTopName.value = outfit.items.top.name || "";
    formTopColor.value = outfit.items.top.color || "";
    formTopHex.value = outfit.items.top.hex || "";
    if (HEX_REGEX.test(outfit.items.top.hex)) formTopColorPicker.value = outfit.items.top.hex;

    // Bottom Wear
    formBottomName.value = outfit.items.bottom.name || "";
    formBottomColor.value = outfit.items.bottom.color || "";
    formBottomHex.value = outfit.items.bottom.hex || "";
    if (HEX_REGEX.test(outfit.items.bottom.hex)) formBottomColorPicker.value = outfit.items.bottom.hex;

    // Outer Wear (optional)
    if (outfit.items.outer) {
        formOuterName.value = outfit.items.outer.name || "";
        formOuterColor.value = outfit.items.outer.color || "";
        formOuterHex.value = outfit.items.outer.hex || "";
        if (HEX_REGEX.test(outfit.items.outer.hex)) formOuterColorPicker.value = outfit.items.outer.hex;
    }

    // Shoes
    formShoesName.value = outfit.items.shoes.name || "";
    formShoesColor.value = outfit.items.shoes.color || "";
    formShoesHex.value = outfit.items.shoes.hex || "";
    if (HEX_REGEX.test(outfit.items.shoes.hex)) formShoesColorPicker.value = outfit.items.shoes.hex;
}

// FORM SUBMISSION (CREATE/UPDATE)
outfitForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const splitTags = (str) => str ? str.split(",").map(t => t.trim()).filter(t => t.length > 0) : [];

    const id = formOutfitId.value;
    const name = formName.value.trim();
    const gender = formGender.value;
    const style_tag = formStyleTag.value.trim();
    const harmony_tag = formHarmonyTag.value.trim();
    const undertone = formUndertone.value.trim();
    const contrast_level = formContrastLevel.value.trim();
    const environments = splitTags(formEnvironments.value);
    const weather_support = splitTags(formWeatherSupport.value);

    // Validate Hex Colors
    const topHex = formTopHex.value.trim().toUpperCase();
    const bottomHex = formBottomHex.value.trim().toUpperCase();
    const outerHex = formOuterHex.value.trim().toUpperCase();
    const shoesHex = formShoesHex.value.trim().toUpperCase();

    if (!HEX_REGEX.test(topHex) || !HEX_REGEX.test(bottomHex) || !HEX_REGEX.test(shoesHex)) {
        alert("Top Wear, Bottom Wear, and Shoes colors must have a valid HEX code (e.g. #FFFFFF)");
        return;
    }

    if (formOuterName.value.trim() && !HEX_REGEX.test(outerHex)) {
        alert("Outer Wear color must have a valid HEX code if outer is provided.");
        return;
    }

    const payload = {
        name,
        gender,
        style_tag,
        harmony_tag,
        undertone,
        contrast_level,
        environments,
        weather_support,
        items: {
            top: {
                name: formTopName.value.trim(),
                color: formTopColor.value.trim(),
                hex: topHex
            },
            bottom: {
                name: formBottomName.value.trim(),
                color: formBottomColor.value.trim(),
                hex: bottomHex
            },
            outer: {
                name: formOuterName.value.trim(),
                color: formOuterColor.value.trim(),
                hex: formOuterName.value.trim() ? outerHex : ""
            },
            shoes: {
                name: formShoesName.value.trim(),
                color: formShoesColor.value.trim(),
                hex: shoesHex
            }
        }
    };

    if (id) {
        payload.id = id;
    }

    const url = id ? `/api/v1/outfits/${id}` : "/api/v1/outfits";
    const method = id ? "PUT" : "POST";

    try {
        const response = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || "Failed to save outfit");
        }

        window.location.href = "/outfits";
    } catch (err) {
        alert("Error: " + err.message);
    }
});

// Run initialization
document.addEventListener("DOMContentLoaded", initForm);
