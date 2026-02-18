let currentSession = null;

const el = (id) => document.getElementById(id);

function showToast(message) {
    const x = el("toast");
    x.textContent = message;
    x.className = "show";
    setTimeout(function () { x.className = x.className.replace("show", ""); }, 3000);
}

async function initSession() {
    // Check localStorage
    const savedSession = localStorage.getItem('agentroom_session');
    if (savedSession) {
        currentSession = savedSession;
        el('sessionTag').textContent = `ID: ${currentSession} (Restored)`;

        try {
            const res = await fetch(`/api/history/${currentSession}`);
            if (res.ok) {
                const data = await res.json();
                renderMessages(data.messages);
                return;
            }
        } catch (e) {
            console.error("Failed to restore session", e);
        }
    }

    // If no session or restore failed, start new
    await startNewSession();
}

async function startNewSession() {
    try {
        const res = await fetch('/api/new_session', { method: 'POST' });
        const data = await res.json();
        currentSession = data.session_id;
        localStorage.setItem('agentroom_session', currentSession);

        el('sessionTag').textContent = `ID: ${currentSession}`;
        el('chatlog').innerHTML = '';
        renderMessages([]);
        showToast("New Session Started");
    } catch (e) {
        showToast("Error creating session");
    }
}

function renderMessages(messages) {
    const chatlog = el('chatlog');
    chatlog.innerHTML = '';
    messages.forEach(m => {
        const div = document.createElement('div');
        const roleClass = m.name === 'User' ? 'user' : 'assistant';
        div.className = `msg ${roleClass}`;

        // Use marked for rich text
        let contentHtml = m.content;
        try {
            contentHtml = marked.parse(m.content);
        } catch (e) {
            console.error("Markdown parse error", e);
        }

        div.innerHTML = `
            <div class="name">${m.name || m.role}</div>
            <div class="content">${contentHtml}</div>
        `;
        chatlog.appendChild(div);
    });
    chatlog.scrollTop = chatlog.scrollHeight;
}

async function runRound() {
    const prompt = el('prompt').value.trim();
    if (!prompt) {
        showToast("Please enter a prompt");
        return;
    }
    if (!currentSession) {
        await startNewSession();
    }

    // UI Feedback
    el('runBtn').disabled = true;
    el('status').textContent = "Agents are deliberating (check GPU terminal)...";

    const enabledAgents = Array.from(document.querySelectorAll('.agent-cb:checked')).map(cb => cb.value);

    try {
        const res = await fetch('/api/run_round', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSession,
                user_prompt: prompt,
                mode: el('mode').value,
                enabled_agents: enabledAgents
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Server Error");
        }

        const data = await res.json();
        renderMessages(data.messages);
        el('prompt').value = '';
    } catch (err) {
        console.error(err);
        showToast(`Error: ${err.message}`);
    } finally {
        el('runBtn').disabled = false;
        el('status').textContent = "";
    }
}

el('newSessBtn').onclick = startNewSession;
el('runBtn').onclick = runRound;

// Init
window.onload = initSession;