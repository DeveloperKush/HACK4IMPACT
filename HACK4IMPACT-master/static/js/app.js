
const state = {
    activeTab: 'factchecker',
    activeSubTab: { mentalhealth: 'therapist' },
    diaryUUID: localStorage.getItem('diary_uuid') || generateUUID(),
    socket: null,
    peerConnected: false,
    inQueue: false,
};

// Persist UUID
localStorage.setItem('diary_uuid', state.diaryUUID);

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}



function switchTab(tabId) {
    state.activeTab = tabId;

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });

    // Update panels
    document.querySelectorAll('.mode-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `panel-${tabId}`);
    });
}

function switchSubTab(parent, subTabId) {
    state.activeSubTab[parent] = subTabId;

    const container = document.getElementById(`panel-${parent}`);
    container.querySelectorAll('.sub-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.subtab === subTabId);
    });
    container.querySelectorAll('.sub-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `sub-${subTabId}`);
    });
}



async function verifyFact() {
    const textInput = document.getElementById('fact-input');
    const fileInput = document.getElementById('fact-image');
    const resultsDiv = document.getElementById('fact-results');
    const text = textInput.value.trim();
    const file = fileInput.files[0];

    if (!text && !file) {
        showToast('Please enter text or upload an image to verify.');
        return;
    }

    resultsDiv.innerHTML = '<div class="loading-text"><span class="spinner"></span> Checking facts...</div>';

    try {
        let response;

        if (file) {
            const formData = new FormData();
            formData.append('image', file);
            if (text) formData.append('text', text);
            response = await fetch('/verify', { method: 'POST', body: formData });
        } else {
            response = await fetch('/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
            });
        }

        const data = await response.json();

        if (data.error) {
            resultsDiv.innerHTML = `<div class="disclaimer">${data.error}</div>`;
            return;
        }

        if (!data.results || data.results.length === 0) {
            resultsDiv.innerHTML = '<div class="empty-state"><div class="empty-state__icon">🔍</div><div class="empty-state__text">No matching facts found. Try rephrasing your query.</div></div>';
            return;
        }

        resultsDiv.innerHTML = data.results.map(r => {
            const badgeClass = r.confidence > 60 ? 'badge--high' : r.confidence > 35 ? 'badge--medium' : 'badge--low';
            const confidenceLabel = r.confidence > 60 ? 'High Match' : r.confidence > 35 ? 'Moderate' : 'Low Match';
            return `
                <div class="result-card">
                    <div class="result-card__header">
                        <span class="result-card__scheme">${r.scheme || r.category}</span>
                        <span class="result-card__badge ${badgeClass}">${confidenceLabel} · ${r.confidence}%</span>
                    </div>
                    <p class="result-card__text">${r.fact}</p>
                </div>
            `;
        }).join('');

    } catch (err) {
        resultsDiv.innerHTML = `<div class="disclaimer">Error: ${err.message}</div>`;
    }
}



async function sendTherapistMsg() {
    const input = document.getElementById('therapist-input');
    const chatArea = document.getElementById('therapist-chat');
    const message = input.value.trim();
    if (!message) return;

    // Add user message
    appendChat(chatArea, message, 'user');
    input.value = '';

    try {
        const res = await fetch('/mental-health/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });
        const data = await res.json();

        if (data.is_crisis) {
            appendChat(chatArea, data.response, 'crisis');
        } else {
            appendChat(chatArea, data.response, 'bot');
        }
    } catch (err) {
        appendChat(chatArea, 'Sorry, something went wrong. Please try again.', 'bot');
    }
}



let selectedMood = 'neutral';

function selectMood(mood, btn) {
    selectedMood = mood;
    document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
}

async function saveDiary() {
    const textarea = document.getElementById('diary-text');
    const entry = textarea.value.trim();
    if (!entry) {
        showToast('Please write something before saving.');
        return;
    }

    try {
        const res = await fetch('/diary/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uuid: state.diaryUUID, entry, mood: selectedMood }),
        });
        const data = await res.json();
        textarea.value = '';
        showToast(`✅ ${data.message} (Entry #${data.total_entries})`);
        loadDiary();
    } catch (err) {
        showToast('Failed to save diary entry.');
    }
}

async function loadDiary() {
    const container = document.getElementById('diary-entries');
    try {
        const res = await fetch(`/diary/${state.diaryUUID}`);
        const data = await res.json();

        if (!data.entries || data.entries.length === 0) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state__icon">📔</div><div class="empty-state__text">Your anonymous diary is empty. Start writing your first entry above.</div></div>';
            return;
        }

        container.innerHTML = data.entries.reverse().map(e => {
            const date = new Date(e.timestamp).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
            const moodEmoji = { happy: '😊', sad: '😢', anxious: '😰', angry: '😡', neutral: '😐', grateful: '🙏' }[e.mood] || '📝';
            return `
                <div class="diary-entry">
                    <div class="diary-entry__meta">
                        <span>${moodEmoji} ${e.mood}</span>
                        <span>${date}</span>
                    </div>
                    <p class="diary-entry__text">${e.text}</p>
                </div>
            `;
        }).join('');
    } catch (err) {
        container.innerHTML = '<div class="disclaimer">Failed to load diary entries.</div>';
    }
}



function initSocket() {
    if (state.socket) return;
    state.socket = io();

    state.socket.on('system_message', data => {
        const chatArea = document.getElementById('peer-chat');
        appendChat(chatArea, data.message, 'system');
    });

    state.socket.on('peer_matched', data => {
        const chatArea = document.getElementById('peer-chat');
        state.peerConnected = true;
        state.inQueue = false;
        updatePeerUI();
        appendChat(chatArea, data.message, 'system');
    });

    state.socket.on('peer_message', data => {
        const chatArea = document.getElementById('peer-chat');
        appendChat(chatArea, data.message, data.sender === 'you' ? 'user' : 'bot');
    });

    state.socket.on('peer_disconnected', data => {
        const chatArea = document.getElementById('peer-chat');
        state.peerConnected = false;
        updatePeerUI();
        appendChat(chatArea, data.message, 'system');
    });
}

function joinPeerQueue() {
    initSocket();
    state.inQueue = true;
    updatePeerUI();
    state.socket.emit('join_queue');
}

function sendPeerMsg() {
    const input = document.getElementById('peer-input');
    const message = input.value.trim();
    if (!message || !state.peerConnected) return;
    state.socket.emit('send_peer_message', { message });
    input.value = '';
}

function leavePeerChat() {
    if (state.socket) {
        state.socket.emit('leave_chat');
    }
    state.peerConnected = false;
    state.inQueue = false;
    updatePeerUI();
}

function updatePeerUI() {
    const joinBtn = document.getElementById('peer-join-btn');
    const leaveBtn = document.getElementById('peer-leave-btn');
    const inputRow = document.getElementById('peer-input-row');
    const statusText = document.getElementById('peer-status');

    if (state.peerConnected) {
        joinBtn.classList.add('hidden');
        leaveBtn.classList.remove('hidden');
        inputRow.classList.remove('hidden');
        statusText.textContent = '🟢 Connected to anonymous peer';
        statusText.style.color = 'var(--accent-green)';
    } else if (state.inQueue) {
        joinBtn.classList.add('hidden');
        leaveBtn.classList.remove('hidden');
        inputRow.classList.add('hidden');
        statusText.textContent = '⏳ Waiting for a peer...';
        statusText.style.color = 'var(--accent-amber)';
    } else {
        joinBtn.classList.remove('hidden');
        leaveBtn.classList.add('hidden');
        inputRow.classList.add('hidden');
        statusText.textContent = 'Connect anonymously with someone who understands.';
        statusText.style.color = 'var(--text-muted)';
    }
}



async function checkSymptoms() {
    const input = document.getElementById('symptom-input');
    const resultsDiv = document.getElementById('triage-results');
    const symptoms = input.value.trim();
    if (!symptoms) {
        showToast('Please describe your symptoms.');
        return;
    }

    resultsDiv.innerHTML = '<div class="loading-text"><span class="spinner"></span> Analysing symptoms...</div>';

    try {
        const res = await fetch('/telemedicine/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symptoms }),
        });
        const data = await res.json();

        let html = `<div class="disclaimer">${data.disclaimer}</div>`;

        if (!data.matched) {
            html += `<div class="empty-state"><div class="empty-state__icon">🩺</div><div class="empty-state__text">${data.message}</div></div>`;
        } else {
            data.results.forEach(r => {
                const sevClass = r.severity.toLowerCase();
                const actionClass = (sevClass === 'emergency' || sevClass === 'high') ? 'action-box--emergency' : 'action-box--moderate';

                html += `
                    <div class="result-card">
                        <div class="result-card__header">
                            <strong>${r.condition}</strong>
                            <span class="severity severity--${sevClass}">${r.severity}</span>
                        </div>
                        <ul class="first-aid-list">
                            ${r.first_aid.map((step, i) => `<li data-step="${i + 1}">${step}</li>`).join('')}
                        </ul>
                        <div class="action-box ${actionClass}">${r.action}</div>
                    </div>
                `;
            });
        }

        resultsDiv.innerHTML = html;
    } catch (err) {
        resultsDiv.innerHTML = `<div class="disclaimer">Error: ${err.message}</div>`;
    }
}



function appendChat(chatArea, message, type) {
    const div = document.createElement('div');
    div.className = `chat-msg chat-msg--${type}`;
    div.textContent = message;
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function showToast(message) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.style.cssText = `
            position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
            background: #1e293b; color: #f1f5f9; padding: 12px 24px; border-radius: 12px;
            font-size: 0.85rem; z-index: 9999; box-shadow: 0 8px 30px rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.1); transition: opacity 0.3s ease;
            font-family: 'Inter', sans-serif;
        `;
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = '1';
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => { toast.style.opacity = '0'; }, 3000);
}

// Handle Enter key for chat inputs
document.addEventListener('DOMContentLoaded', () => {
    const therapistInput = document.getElementById('therapist-input');
    if (therapistInput) {
        therapistInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') { e.preventDefault(); sendTherapistMsg(); }
        });
    }

    const peerInput = document.getElementById('peer-input');
    if (peerInput) {
        peerInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') { e.preventDefault(); sendPeerMsg(); }
        });
    }

    // Load diary on start
    loadDiary();

    // Add welcome message to therapist chat
    const therapistChat = document.getElementById('therapist-chat');
    if (therapistChat) {
        appendChat(therapistChat, "Welcome. I'm here to listen. This is a safe, judgement-free space. How are you feeling today?", 'bot');
    }
});
