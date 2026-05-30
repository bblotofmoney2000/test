/* ── State ────────────────────────────────────────────────────────────────── */
let apiType       = 'gemini';
let voiceEnabled  = false;
let voiceInput    = false;
let recognition   = null;
let sidebarOpen   = true;
let currentSidebarTab = 'notes';

/* ── Init ─────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initVoice();
  fetchStatus();
  setInterval(fetchStatus, 30_000);
});

function fetchStatus() {
  fetch('/api/status').then(r => r.json()).then(d => {
    if (d.stats) {
      document.getElementById('memory-count').textContent =
        `${d.stats.messages} MEMORIES`;
      document.getElementById('task-count').textContent =
        `${d.stats.pending_tasks} TASKS`;
    }
  }).catch(() => {});
}

/* ── Setup ────────────────────────────────────────────────────────────────── */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    apiType = btn.dataset.type;
    document.querySelectorAll('.setup-hint').forEach(h => h.classList.add('hidden'));
    document.getElementById(`setup-hint-${apiType}`)?.classList.remove('hidden');
  });
});

async function submitSetup() {
  const key = document.getElementById('api-key-input').value.trim();
  const errEl = document.getElementById('setup-error');
  errEl.classList.add('hidden');

  if (!key) { showSetupError('Please paste your API key.'); return; }

  const btn = document.querySelector('.setup-btn');
  btn.textContent = 'INITIALIZING...';
  btn.disabled = true;

  try {
    const resp = await fetch('/api/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key, api_type: apiType }),
    });
    const data = await resp.json();
    if (data.ok) {
      document.getElementById('setup-modal').classList.add('hidden');
      document.getElementById('main-interface').classList.remove('hidden');
      fetchStatus();
      loadNotes();
      loadTasks();
    } else {
      showSetupError(data.error || 'Setup failed.');
    }
  } catch (e) {
    showSetupError('Connection error. Make sure JARVIS is running.');
  } finally {
    btn.textContent = 'INITIALIZE JARVIS';
    btn.disabled = false;
  }
}

function showSetupError(msg) {
  const el = document.getElementById('setup-error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

/* ── Chat ─────────────────────────────────────────────────────────────────── */
async function sendMessage(text) {
  const input = document.getElementById('user-input');
  const msg   = (text || input.value).trim();
  if (!msg) return;

  input.value = '';
  autoResize(input);
  appendMessage('user', msg);
  setProcessing(true);

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg }),
    });
    const data = await resp.json();
    if (data.error) {
      appendMessage('jarvis', `⚠ ${data.error}`, true);
    } else {
      appendMessage('jarvis', data.html, false, true);
      if (voiceEnabled && data.text) speakText(data.text);
    }
    fetchStatus();
  } catch (e) {
    appendMessage('jarvis', '⚠ Connection error. Is JARVIS running?', true);
  } finally {
    setProcessing(false);
  }
}

function appendMessage(role, content, isError = false, isHtml = false) {
  const container = document.getElementById('chat-messages');
  const isUser    = role === 'user';

  const div = document.createElement('div');
  div.className = `message ${isUser ? 'user-msg' : 'jarvis-msg'}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = isUser ? 'YOU' : 'J';

  const content_div = document.createElement('div');
  content_div.className = 'msg-content';

  const text_div = document.createElement('div');
  text_div.className = 'msg-text' + (isError ? ' error-text' : '');
  if (isHtml) {
    text_div.innerHTML = content;
  } else {
    text_div.textContent = content;
  }

  const time_div = document.createElement('div');
  time_div.className = 'msg-time';
  time_div.textContent = isUser ? now() : `JARVIS — ${now()}`;

  content_div.appendChild(text_div);
  content_div.appendChild(time_div);
  div.appendChild(avatar);
  div.appendChild(content_div);

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function setProcessing(on) {
  document.getElementById('typing-indicator').classList.toggle('hidden', !on);
  document.getElementById('send-btn').disabled = on;
  if (on) {
    document.getElementById('chat-messages').scrollTop = 99999;
  }
}

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/* ── Input ────────────────────────────────────────────────────────────────── */
function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

/* ── Voice Input ──────────────────────────────────────────────────────────── */
function initVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;

  recognition = new SR();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (e) => {
    const transcript = Array.from(e.results)
      .map(r => r[0].transcript).join('');
    document.getElementById('user-input').value = transcript;
    autoResize(document.getElementById('user-input'));
  };

  recognition.onend = () => {
    if (voiceInput) {
      const val = document.getElementById('user-input').value.trim();
      if (val) sendMessage();
    }
    stopVoice();
  };

  recognition.onerror = () => stopVoice();
}

function toggleVoice() {
  if (!recognition) {
    alert('Speech recognition not available in this browser.');
    return;
  }
  voiceInput ? stopVoice() : startVoice();
}

function startVoice() {
  voiceInput = true;
  recognition.start();
  document.getElementById('voice-btn').classList.add('active');
  document.getElementById('voice-status').textContent = '● LISTENING';
}

function stopVoice() {
  voiceInput = false;
  try { recognition.stop(); } catch(e) {}
  document.getElementById('voice-btn').classList.remove('active');
  document.getElementById('voice-status').textContent = '';
}

/* ── Voice Output ─────────────────────────────────────────────────────────── */
function toggleSpeech() {
  voiceEnabled = !voiceEnabled;
  const btn = document.getElementById('speech-btn');
  btn.title = voiceEnabled ? 'Voice Output: ON' : 'Voice Output: OFF';
  btn.style.color = voiceEnabled ? 'var(--cyan)' : '';
}

function speakText(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();

  const clean = text
    .replace(/[#*`_~\[\]]/g, '')
    .replace(/\n{2,}/g, '. ')
    .replace(/\n/g, ' ')
    .slice(0, 600);  // keep it concise

  const utt = new SpeechSynthesisUtterance(clean);
  utt.rate  = 1.05;
  utt.pitch = 0.88;
  utt.volume = 0.9;

  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.name.includes('Google UK English Male'))
    || voices.find(v => v.lang === 'en-GB')
    || voices.find(v => v.lang.startsWith('en'));
  if (preferred) utt.voice = preferred;

  window.speechSynthesis.speak(utt);
}

/* ── File Upload ──────────────────────────────────────────────────────────── */
function handleFileUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    const content = ev.target.result;
    const msg = `Please analyse this file — "${file.name}":\n\n\`\`\`\n${content.slice(0, 8000)}\n\`\`\``;
    sendMessage(msg);
  };
  reader.readAsText(file);
  e.target.value = '';
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
function toggleSidebar() {
  sidebarOpen = !sidebarOpen;
  document.getElementById('sidebar').classList.toggle('collapsed', !sidebarOpen);
  if (sidebarOpen) {
    loadNotes();
    loadTasks();
  }
}

function showSidebarTab(tab) {
  currentSidebarTab = tab;
  document.querySelectorAll('.sidebar-tab').forEach((el, i) => {
    el.classList.toggle('active', ['notes','tasks','history'][i] === tab);
  });
  document.getElementById('sidebar-notes').classList.toggle('hidden', tab !== 'notes');
  document.getElementById('sidebar-tasks').classList.toggle('hidden', tab !== 'tasks');
  document.getElementById('sidebar-history').classList.toggle('hidden', tab !== 'history');

  if (tab === 'notes')   loadNotes();
  if (tab === 'tasks')   loadTasks();
  if (tab === 'history') loadHistory();
}

/* ── Notes ────────────────────────────────────────────────────────────────── */
async function loadNotes() {
  const list = document.getElementById('notes-list');
  try {
    const notes = await fetch('/api/notes').then(r => r.json());
    if (!notes.length) {
      list.innerHTML = '<div style="padding:.8rem;color:var(--txt-dim);font-size:.8rem;text-align:center">No notes yet.</div>';
      return;
    }
    list.innerHTML = notes.map(n => `
      <div class="note-item" onclick="showNote(${n.id},'${escHtml(n.title)}','${escHtml(n.content)}')">
        <div class="item-title">${escHtml(n.title)}</div>
        <div class="item-meta">
          <span class="item-category">${n.category}</span>
          <span>${n.ts ? n.ts.slice(0,10) : ''}</span>
        </div>
      </div>`).join('');
  } catch(e) {}
}

function showNote(id, title, content) {
  document.getElementById('note-modal-title').textContent = title;
  document.getElementById('note-modal-content').innerHTML =
    content.replace(/\n/g, '<br>');
  document.getElementById('note-modal').classList.remove('hidden');
}

function closeNoteModal() {
  document.getElementById('note-modal').classList.add('hidden');
}

/* ── Tasks ────────────────────────────────────────────────────────────────── */
async function loadTasks() {
  const list = document.getElementById('tasks-list');
  try {
    const tasks = await fetch('/api/tasks').then(r => r.json());
    const pending = tasks.filter(t => t.status === 'pending');
    if (!pending.length) {
      list.innerHTML = '<div style="padding:.8rem;color:var(--txt-dim);font-size:.8rem;text-align:center">All clear, Sir.</div>';
      return;
    }
    list.innerHTML = pending.map(t => `
      <div class="task-item">
        <div class="item-title">${escHtml(t.title)}</div>
        <div class="item-meta">
          <span>${t.due ? '📅 ' + t.due : ''}</span>
          <button class="task-done-btn" onclick="completeTask(${t.id})">✓ Done</button>
        </div>
      </div>`).join('');
  } catch(e) {}
}

async function completeTask(id) {
  await fetch(`/api/tasks/${id}/complete`, { method: 'POST' });
  loadTasks();
  fetchStatus();
}

/* ── History ──────────────────────────────────────────────────────────────── */
async function loadHistory() {
  const list = document.getElementById('history-list');
  try {
    const msgs = await fetch('/api/history').then(r => r.json());
    list.innerHTML = msgs.slice(-30).reverse().map(m => `
      <div class="history-item">
        <div class="h-role ${m.role === 'user' ? 'user' : 'assistant'}">
          ${m.role === 'user' ? 'YOU' : 'JARVIS'}
        </div>
        <div class="h-text">${escHtml((m.content || '').slice(0, 80))}…</div>
      </div>`).join('');
  } catch(e) {}
}

/* ── Session controls ─────────────────────────────────────────────────────── */
function clearChat() {
  if (!confirm('Start a new session? Current conversation will be cleared from the chat view (notes and tasks are kept).')) return;
  fetch('/api/clear', { method: 'POST' }).then(() => {
    document.getElementById('chat-messages').innerHTML = `
      <div class="message jarvis-msg">
        <div class="msg-avatar">J</div>
        <div class="msg-content">
          <div class="msg-text">New session initialised. How may I assist you, Sir?</div>
          <div class="msg-time">JARVIS — ${now()}</div>
        </div>
      </div>`;
    fetchStatus();
  });
}

function exportChat() {
  fetch('/api/history').then(r => r.json()).then(msgs => {
    const lines = msgs.map(m =>
      `**${m.role === 'user' ? 'You' : 'JARVIS'}** (${m.ts || ''})\n\n${m.content}`
    ).join('\n\n---\n\n');
    const blob = new Blob([`# JARVIS Session Export\n\n${lines}`], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `jarvis-${new Date().toISOString().slice(0,10)}.md`;
    a.click();
  });
}

/* ── Helpers ──────────────────────────────────────────────────────────────── */
function escHtml(s) {
  return String(s || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
