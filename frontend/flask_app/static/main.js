document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const uploadBtn = document.getElementById('uploadBtn');
    const sendBtn = document.getElementById('sendBtn');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');
    const clearChat = document.getElementById('clearChat');
    const modelSelect = document.getElementById('modelSelect');
    const apiStatus = document.getElementById('apiStatus');
    const apiStatusText = document.getElementById('apiStatusText');
    const statDocs = document.getElementById('statDocs');
    const statChunks = document.getElementById('statChunks');
    const indexedFileList = document.getElementById('indexedFileList');

    let selectedFiles = [];

    // --- API Health Check ---
    async function checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            if (response.ok) {
                apiStatus.className = 'status-dot online';
                apiStatusText.innerText = 'API Online';
                if (data.collection_stats) {
                    statDocs.innerText = data.collection_stats.total_documents || 0;
                    statChunks.innerText = data.collection_stats.total_chunks || 0;
                }
                refreshIndexedDocuments();
            } else {
                throw new Error();
            }
        } catch (err) {
            apiStatus.className = 'status-dot offline';
            apiStatusText.innerText = 'API Offline';
        }
    }

    // --- Indexed Documents Handling ---
    async function refreshIndexedDocuments() {
        try {
            const response = await fetch('/documents');
            const data = await response.json();
            if (response.ok && data.documents) {
                renderIndexedDocuments(data.documents);
            }
        } catch (err) {
            console.error('Error fetching documents:', err);
        }
    }

    function renderIndexedDocuments(docs) {
        if (docs.length === 0) {
            indexedFileList.innerHTML = '<p class="empty-hint">Nenhum documento indexado.</p>';
            return;
        }

        indexedFileList.innerHTML = '';
        docs.forEach(doc => {
            const item = document.createElement('div');
            item.className = 'indexed-item';
            item.innerHTML = `
                <span class="file-name" title="${doc}">${doc}</span>
                <button class="delete-btn" data-filename="${doc}" title="Excluir documento">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6"/></svg>
                </button>
            `;
            indexedFileList.appendChild(item);
        });

        // Add delete event listeners
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.onclick = async (e) => {
                const filename = btn.getAttribute('data-filename');
                if (confirm(`Deseja excluir o documento "${filename}"?`)) {
                    await deleteDocument(filename);
                }
            };
        });
    }

    async function deleteDocument(filename) {
        try {
            const response = await fetch(`/documents/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                showNotification(`Documento "${filename}" excluído.`, 'success');
                checkHealth();
            } else {
                const data = await response.json();
                showNotification(data.detail || 'Erro ao excluir documento.', 'error');
            }
        } catch (err) {
            showNotification('Erro de conexão ao excluir.', 'error');
        }
    }

    setInterval(checkHealth, 10000);
    checkHealth();

    // --- Upload Modal Controls ---
    const uploadModal = document.getElementById('uploadModal');
    const closeModal = document.getElementById('closeModal');
    const modalProcessBtn = document.getElementById('modalProcessBtn');
    const modalDoneBtn = document.getElementById('modalDoneBtn');
    const modalInitial = document.getElementById('modalInitial');
    const modalProcessing = document.getElementById('modalProcessing');
    const modalSuccess = document.getElementById('modalSuccess');
    const modalFileCount = document.getElementById('modalFileCount');
    const modalFileListText = document.getElementById('modalFileListText');

    function openUploadModal(files) {
        selectedFiles = Array.from(files).filter(f => f.type === 'application/pdf');
        if (selectedFiles.length === 0) {
            showNotification('Selecione apenas arquivos PDF.', 'error');
            return;
        }

        modalFileCount.innerText = `${selectedFiles.length} ${selectedFiles.length === 1 ? 'arquivo selecionado' : 'arquivos selecionados'}`;
        modalFileListText.innerText = selectedFiles.map(f => f.name).join(', ');

        showModalState('initial');
        uploadModal.hidden = false;
    }

    function showModalState(state) {
        modalInitial.hidden = (state !== 'initial');
        modalProcessing.hidden = (state !== 'processing');
        modalSuccess.hidden = (state !== 'success');

        // Hide close button during processing to prevent interruption
        closeModal.hidden = (state === 'processing');
    }

    closeModal.onclick = () => {
        uploadModal.hidden = true;
        resetUpload();
    };

    modalDoneBtn.onclick = () => {
        uploadModal.hidden = true;
        resetUpload();
    };

    function resetUpload() {
        selectedFiles = [];
        fileList.innerHTML = '';
        fileInput.value = '';
    }

    // --- File Handling ---
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        openUploadModal(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            openUploadModal(fileInput.files);
        }
    });

    // --- Slider Value Synchronization ---
    const chunkSizeSlider = document.getElementById('chunkSize');
    const chunkSizeDisplay = document.getElementById('chunkSizeValue');
    const chunkOverlapSlider = document.getElementById('chunkOverlap');
    const chunkOverlapDisplay = document.getElementById('chunkOverlapValue');

    chunkSizeSlider.addEventListener('input', () => {
        chunkSizeDisplay.innerText = chunkSizeSlider.value;
    });

    chunkOverlapSlider.addEventListener('input', () => {
        chunkOverlapDisplay.innerText = chunkOverlapSlider.value;
    });

    // --- Upload Action from Modal ---
    modalProcessBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;

        const formData = new FormData();
        selectedFiles.forEach(f => formData.append('files', f));

        const chunkSize = document.getElementById('chunkSize').value;
        const chunkOverlap = document.getElementById('chunkOverlap').value;
        formData.append('chunk_size', chunkSize);
        formData.append('chunk_overlap', chunkOverlap);

        showModalState('processing');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                showModalState('success');
                checkHealth();
            } else {
                showNotification(data.detail || 'Erro ao subir arquivos.', 'error');
                showModalState('initial');
            }
        } catch (err) {
            showNotification('Erro de conexão com o servidor.', 'error');
            showModalState('initial');
        }
    });

    // --- Chat Action ---
    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Add user message to UI
        appendMessage('user', text);
        userInput.value = '';
        userInput.style.height = 'auto';

        const loadingMsg = appendMessage('assistant', 'Pensando...', true);

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: text,
                    provider: modelSelect.value
                })
            });
            const data = await response.json();

            loadingMsg.remove();

            if (response.ok) {
                appendMessage('assistant', data.answer, false, data.references);
            } else {
                appendMessage('assistant', `⚠️ Erro: ${data.detail || 'Não foi possível obter resposta.'}`);
            }
        } catch (err) {
            loadingMsg.remove();
            appendMessage('assistant', '⚠️ Erro de conexão com o servidor.');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    // --- UI Helpers ---
    function appendMessage(role, text, isLoading = false, references = []) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;

        let contentHtml = `<div class="message-content">${text}</div>`;

        if (references && references.length > 0) {
            const refHtml = references.map((r, i) => `
                <div class="ref-item">
                    <div class="ref-header" onclick="this.nextElementSibling.hidden = !this.nextElementSibling.hidden">
                        📖 Referência ${i + 1}
                    </div>
                    <div class="ref-content" hidden>${r}</div>
                </div>
            `).join('');
            contentHtml = `
                <div class="message-content">
                    ${text}
                    <div class="references">
                        ${refHtml}
                    </div>
                </div>
            `;
        }

        msgDiv.innerHTML = contentHtml;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv;
    }

    function showNotification(text, type) {
        const container = document.getElementById('notifications');
        const n = document.createElement('div');
        n.className = `notification ${type}`;
        n.innerText = text;
        container.appendChild(n);
        setTimeout(() => n.remove(), 5000);
    }

    clearChat.addEventListener('click', () => {
        chatMessages.innerHTML = `
            <div class="message assistant welcome">
                <div class="message-content">
                    Chat limpo. Como posso ajudar agora?
                </div>
            </div>
        `;
    });
});
