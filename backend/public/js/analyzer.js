document.addEventListener('DOMContentLoaded', () => {
    const imageInput = document.getElementById('imageInput');
    const dropZone = document.getElementById('dropZone');
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const uploadSection = document.getElementById('uploadSection');
    const changeBtn = document.getElementById('changeBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsSection = document.getElementById('resultsSection');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Result DOM elements
    const resColorType = document.getElementById('resColorType');
    const resUndertoneName = document.getElementById('resUndertoneName');
    const resUndertoneDesc = document.getElementById('resUndertoneDesc');
    const resSkintoneName = document.getElementById('resSkintoneName');
    const resSkintoneDesc = document.getElementById('resSkintoneDesc');
    const resContrastName = document.getElementById('resContrastName');
    const resContrastDesc = document.getElementById('resContrastDesc');
    const bestColorsList = document.getElementById('bestColorsList');
    const avoidColorsList = document.getElementById('avoidColorsList');

    let selectedFile = null;

    // --- Drag and Drop Handlers ---
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    imageInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (!file.type.startsWith('image/')) {
                alert('Please upload a valid image file (JPG, PNG, WEBP).');
                return;
            }
            
            if (file.size > 5 * 1024 * 1024) {
                alert('File is too large. Maximum size is 5MB.');
                return;
            }

            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                uploadSection.style.display = 'none';
                previewContainer.style.display = 'block';
                analyzeBtn.style.display = 'flex';
                resultsSection.style.display = 'none'; // hide previous results
            };
            reader.readAsDataURL(file);
        }
    }

    // --- Change Photo ---
    changeBtn.addEventListener('click', () => {
        selectedFile = null;
        imageInput.value = '';
        uploadSection.style.display = 'block';
        previewContainer.style.display = 'none';
        analyzeBtn.style.display = 'none';
        resultsSection.style.display = 'none';
    });

    // --- Analyze Form Submission ---
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('image', selectedFile);

        loadingOverlay.style.display = 'flex';
        resultsSection.style.display = 'none';

        try {
            const response = await fetch('/api/v1/analyze-color', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to analyze image');
            }

            renderResults(data);
        } catch (error) {
            console.error('Analysis error:', error);
            alert(`Error: ${error.message}`);
        } finally {
            loadingOverlay.style.display = 'none';
        }
    });

    // --- Render Results ---
    function renderResults(data) {
        // Set main traits
        resColorType.textContent = data.color_type;

        resUndertoneName.textContent = data.undertone.value.name;
        resUndertoneDesc.textContent = data.undertone.value.explanation;

        resSkintoneName.textContent = data.skintone.value.name;
        resSkintoneDesc.textContent = data.skintone.value.explanation;

        resContrastName.textContent = data.contrast.value.name;
        resContrastDesc.textContent = data.contrast.value.explanation;

        // Render color boxes
        renderColorList(bestColorsList, data.best_colors || []);
        renderColorList(avoidColorsList, data.avoid_color || []);

        resultsSection.style.display = 'block';
        
        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }

    function renderColorList(container, colors) {
        container.innerHTML = '';
        if (!colors || colors.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted); font-size: 14px;">No colors found.</p>';
            return;
        }

        colors.forEach(colorObj => {
            const box = document.createElement('div');
            box.className = 'color-box';
            box.style.backgroundColor = colorObj.hex;
            
            const span = document.createElement('span');
            span.textContent = colorObj.hex;
            
            // Set text color for contrast if needed
            // Currently using white background for span to ensure readability
            
            box.appendChild(span);
            box.title = colorObj.name || colorObj.hex;
            container.appendChild(box);
        });
    }
});
