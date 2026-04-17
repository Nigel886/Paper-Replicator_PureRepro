const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const replicateBtn = document.getElementById('replicate-btn');
const btnText = document.getElementById('btn-text');
const previewContainer = document.getElementById('preview-container');
const resultArea = document.getElementById('result-area');

const modeUpload = document.getElementById('mode-upload');
const modeArxiv = document.getElementById('mode-arxiv');
const uploadContainer = document.getElementById('upload-container');
const arxivContainer = document.getElementById('arxiv-container');
const arxivInput = document.getElementById('arxiv-input');
const frameworkSelect = document.getElementById('framework-select');

let currentMode = 'upload'; // 'upload' or 'arxiv'

// --- Mode Switching ---
modeUpload.onclick = () => {
    currentMode = 'upload';
    modeUpload.className = "px-6 py-2 rounded-full font-bold transition-all bg-slate-900 text-white shadow-lg";
    modeArxiv.className = "px-6 py-2 rounded-full font-bold transition-all bg-white text-slate-600 border border-slate-200 hover:bg-slate-50";
    uploadContainer.classList.remove('hidden');
    arxivContainer.classList.add('hidden');
};

modeArxiv.onclick = () => {
    currentMode = 'arxiv';
    modeArxiv.className = "px-6 py-2 rounded-full font-bold transition-all bg-slate-900 text-white shadow-lg";
    modeUpload.className = "px-6 py-2 rounded-full font-bold transition-all bg-white text-slate-600 border border-slate-200 hover:bg-slate-50";
    arxivContainer.classList.remove('hidden');
    uploadContainer.classList.add('hidden');
};

const overviewOutput = document.getElementById('overview-output');
const codeOutput = document.getElementById('code-output');
const insightsOutput = document.getElementById('insights-output');

let selectedFiles = [];

// --- UI Interaction Logic ---
dropZone.onclick = () => fileInput.click();

dropZone.ondragover = (e) => { 
    e.preventDefault(); 
    dropZone.classList.add('drag-over'); 
};

dropZone.ondragleave = () => dropZone.classList.remove('drag-over');

dropZone.ondrop = (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    handleFiles(e.dataTransfer.files);
};

fileInput.onchange = (e) => handleFiles(e.target.files);

/**
 * Renders thumbnail previews of uploaded images
 */
function handleFiles(files) {
    selectedFiles = Array.from(files);
    previewContainer.innerHTML = '';
    selectedFiles.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = "h-24 w-24 object-cover rounded-xl border-2 border-white shadow-md transform hover:rotate-3 transition";
            previewContainer.appendChild(img);
        };
        reader.readAsDataURL(file);
    });
}

// --- Core Parsing Logic ---

/**
 * Splits the raw AI Markdown response into structured segments
 */
function parsePureReproResponse(text) {
    const overviewMatch = text.match(/##\s*1\.\s*Overview([\s\S]*?)(?=##\s*2\.)/i);
    const codeMatch = text.match(/##\s*2\.\s*Implementation Code([\s\S]*?)(?=##\s*3\.)/i);
    const insightsMatch = text.match(/##\s*3\.\s*Key Engineering Insights([\s\S]*)/i);

    return {
        overview: overviewMatch ? overviewMatch[1].trim() : "Analysis complete. Review the sections below.",
        code: codeMatch ? codeMatch[1].trim() : text, 
        insights: insightsMatch ? insightsMatch[1].trim() : "No specific insights extracted."
    };
}

/**
 * Sanitizes code blocks by stripping Markdown triple-backticks
 */
function cleanCodeBlocks(codeText) {
    return codeText.replace(/```[a-z]*\n?/gi, '').replace(/```/g, '').trim();
}

/**
 * A helper to render content by protecting LaTeX from Markdown interference
 * FIXED: Ensures placeholder replacement handles special regex characters correctly
 */
function renderContentWithMath(element, rawText, isInline = false) {
    const latexBlocks = [];
    // 1. Extract and hide LaTeX blocks to protect them from marked.js
    // Use a unique string that won't be mangled by marked.js
    const placeholderText = rawText.replace(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g, (match) => {
        latexBlocks.push(match);
        return `@@LATEX${latexBlocks.length - 1}@@`;
    });

    // 2. Render the surrounding Markdown
    let renderedHtml = isInline ? marked.parseInline(placeholderText) : marked.parse(placeholderText);

    // 3. Put the raw LaTeX back into the rendered HTML
    // Fixed with a safer split/join or loop to avoid regex substitution issues
    latexBlocks.forEach((block, i) => {
        const target = `@@LATEX${i}@@`;
        renderedHtml = renderedHtml.split(target).join(block);
    });

    element.innerHTML = renderedHtml;
}

// --- Global Action Handlers ---
window.copyCode = () => {
    const code = codeOutput.innerText;
    navigator.clipboard.writeText(code).then(() => {
        const copyBtn = document.querySelector('button[onclick="copyCode()"]');
        const originalText = copyBtn.innerText;
        copyBtn.innerText = "Copied!";
        setTimeout(() => copyBtn.innerText = originalText, 2000);
    });
};

// --- Execution Flow & API Integration ---
replicateBtn.onclick = async () => {
    if (currentMode === 'upload' && selectedFiles.length === 0) {
        alert("Please upload paper excerpts first.");
        return;
    }
    if (currentMode === 'arxiv' && !arxivInput.value.trim()) {
        alert("Please enter an ArXiv ID.");
        return;
    }

    // UI State: Loading Initialization
    replicateBtn.disabled = true;
    btnText.innerHTML = '<span class="loader"></span>Analyzing Paper Content...';
    resultArea.classList.add('hidden');

    try {
        let data;
        if (currentMode === 'upload') {
            const formData = new FormData();
            selectedFiles.forEach(file => formData.append('files', file));
            formData.append('output_name', 'model.py');
            formData.append('framework', frameworkSelect.value);

            const response = await fetch('/replicate', {
                method: 'POST',
                body: formData
            });
            data = await response.json();
        } else {
            const response = await fetch('/replicate_arxiv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    arxiv_id: arxivInput.value.trim(),
                    framework: frameworkSelect.value
                })
            });
            data = await response.json();
        }

        if (data.status === "success") {
            // ArXiv mode might return multiple algorithms, but we'll use the same parser
            const result = parsePureReproResponse(data.analysis);

            // 1. Render Overview and Insights using the Protection Helper
            renderContentWithMath(overviewOutput, result.overview);
            
            const insightLines = result.insights.split('\n').filter(l => l.trim());
            insightsOutput.innerHTML = ''; // Clear old content
            insightLines.forEach(line => {
                const container = document.createElement('div');
                container.className = "flex items-start mb-2";
                container.innerHTML = `<span class="mr-2 text-amber-500">•</span><span class="insight-text"></span>`;
                const textSpan = container.querySelector('.insight-text');
                // Protect LaTeX within each bullet point
                renderContentWithMath(textSpan, line.replace(/^[*-]\s*/, ''), true);
                insightsOutput.appendChild(container);
            });

            // 2. Render Code normally
            codeOutput.innerText = cleanCodeBlocks(result.code);

            // UI State: Show Result Area
            resultArea.classList.remove('hidden');

            // 3. Final KaTeX Polish: Trigger the actual rendering of math symbols
            setTimeout(() => {
                if (typeof renderMathInElement === 'function') {
                    renderMathInElement(resultArea, {
                        delimiters: [
                            {left: '$$', right: '$$', display: true},
                            {left: '$', right: '$', display: false},
                            {left: '\\(', right: '\\)', display: false},
                            {left: '\\[', right: '\\]', display: true}
                        ],
                        throwOnError: false,
                        trust: true,
                        strict: false
                    });
                }
            }, 100);

            resultArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            alert("Analysis failed: " + (data.error || "Unknown error"));
        }
    } catch (error) {
        console.error("Replication Error:", error);
        alert("Could not connect to PureRepro Backend!");
    } finally {
        replicateBtn.disabled = false;
        btnText.innerText = 'Start Replication';
    }
};