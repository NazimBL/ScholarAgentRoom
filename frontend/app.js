let currentSession = null;

const el = (id) => document.getElementById(id);

async function startNewSession() {
    const res = await fetch('/api/new_session', { method: 'POST' });
    const data = await res.json();
    currentSession = data.session_id;
    el('sessionTag').textContent = `ID: ${currentSession}`;
    el('chatlog').innerHTML = '';
    renderMessages([]);
}

function renderMessages(messages) {
    const chatlog = el('chatlog');
    chatlog.innerHTML = '';
    messages.forEach(m => {
        const div = document.createElement('div');
        const roleClass = m.name === 'User' ? 'user' : 'assistant';
        div.className = `msg ${roleClass}`;
        div.innerHTML = `
            <div class="name">${m.name || m.role}</div>
            <div class="content">${m.content.replace(/\n/g, '<br>')}</div>
        `;
        chatlog.appendChild(div);
    });
    chatlog.scrollTop = chatlog.scrollHeight;
}

async function runRound() {
    const prompt = el('prompt').value.trim();
    if (!prompt || !currentSession) return;

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
        const data = await res.json();
        renderMessages(data.messages);
        el('prompt').value = '';
    } catch (err) {
        alert("Error connecting to backend!");
    } finally {
        el('runBtn').disabled = false;
        el('status').textContent = "";
    }
}

el('newSessBtn').onclick = startNewSession;
el('runBtn').onclick = runRound;

// Init
window.onload = startNewSession;