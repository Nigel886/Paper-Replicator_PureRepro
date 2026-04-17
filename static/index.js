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

const progressContainer = document.getElementById('progress-container');
const progressStatus = document.getElementById('progress-status');
const progressPercent = document.getElementById('progress-percent');
const progressBar = document.getElementById('progress-bar');
const progressLog = document.getElementById('progress-log');

let selectedFiles = [];

// --- Progress Tracking Helper ---
function startProgressTracking(taskId, onComplete) {
    progressContainer.classList.remove('hidden');
    progressLog.innerHTML = '';
    
    const eventSource = new EventSource(`/progress/${taskId}`);
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.message === "COMPLETED") {
            eventSource.close();
            progressContainer.classList.add('hidden');
            if (onComplete) onComplete();
            return;
        }

        if (data.message.startsWith("FAILED")) {
            eventSource.close();
            progressContainer.classList.add('hidden');
            alert(data.message);
            if (onComplete) onComplete(new Error(data.message));
            return;
        }

        // Update UI
        progressStatus.innerText = data.message;
        const percent = Math.round((data.step / data.total_steps) * 100);
        progressPercent.innerText = `${percent}%`;
        progressBar.style.width = `${percent}%`;
        
        // Add log entry
        const logEntry = document.createElement('div');
        logEntry.className = "mb-1 border-l-2 border-blue-200 pl-2";
        logEntry.innerText = `[${new Date().toLocaleTimeString()}] ${data.message}`;
        progressLog.appendChild(logEntry);
        progressLog.scrollTop = progressLog.scrollHeight;
    };

    eventSource.onerror = () => {
        eventSource.close();
        // Don't hide container immediately on error, as it might be a temporary reconnect
    };

    return eventSource;
}

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
    btnText.innerHTML = '<span class="loader"></span>Running Engine...';
    resultArea.classList.add('hidden');
    
    // Generate a unique task ID for this session
    const taskId = 'task_' + Math.random().toString(36).substr(2, 9);

    // 定义任务完成后的回调逻辑
    const onTaskFinished = async (error) => {
        if (error) {
            replicateBtn.disabled = false;
            btnText.innerText = 'Start Replication';
            return;
        }

        try {
            // 任务在后台完成后，主动去请求最终结果
            const response = await fetch(`/result/${taskId}`);
            const data = await response.json();

            if (data.status === "success") {
                const result = parsePureReproResponse(data.analysis);
                renderContentWithMath(overviewOutput, result.overview);
                
                const insightLines = result.insights.split('\n').filter(l => l.trim());
                insightsOutput.innerHTML = '';
                insightLines.forEach(line => {
                    const container = document.createElement('div');
                    container.className = "flex items-start mb-2";
                    container.innerHTML = `<span class="mr-2 text-amber-500">•</span><span class="insight-text"></span>`;
                    const textSpan = container.querySelector('.insight-text');
                    renderContentWithMath(textSpan, line.replace(/^[*-]\s*/, ''), true);
                    insightsOutput.appendChild(container);
                });

                codeOutput.innerText = cleanCodeBlocks(result.code);
                resultArea.classList.remove('hidden');

                setTimeout(() => {
                    if (typeof renderMathInElement === 'function') {
                        renderMathInElement(resultArea, {
                            delimiters: [
                                {left: '$$', right: '$$', display: true},
                                {left: '$', right: '$', display: false},
                                {left: '\\(', right: '\\)', display: false},
                                {left: '\\[', right: '\\]', display: true}
                            ],
                            throwOnError: false, trust: true, strict: false
                        });
                    }
                }, 100);

                resultArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                alert("Analysis failed to retrieve result.");
            }
        } catch (err) {
            console.error("Result Fetch Error:", err);
            alert("Could not retrieve final results.");
        } finally {
            replicateBtn.disabled = false;
            btnText.innerText = 'Start Replication';
        }
    };

    startProgressTracking(taskId, onTaskFinished);

    try {
        if (currentMode === 'upload') {
            const formData = new FormData();
            selectedFiles.forEach(file => formData.append('files', file));
            formData.append('output_name', 'model.py');
            formData.append('framework', frameworkSelect.value);
            formData.append('task_id', taskId);

            // 文件上传模式也改为后台处理（此处后端逻辑暂未完全统一，但前端先适配 taskId）
            await fetch('/replicate', { method: 'POST', body: formData });
        } else {
            // ArXiv 模式：触发即走，不等待响应中的 analysis 字段
            await fetch('/replicate_arxiv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    arxiv_id: arxivInput.value.trim(),
                    framework: frameworkSelect.value,
                    task_id: taskId
                })
            });
        }
    } catch (error) {
        console.error("Submission Error:", error);
        alert("Could not connect to PureRepro Backend!");
        replicateBtn.disabled = false;
        btnText.innerText = 'Start Replication';
    }
};