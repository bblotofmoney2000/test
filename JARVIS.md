# J.A.R.V.I.S — Setup & User Guide

> *Just A Rather Very Intelligent System*
> Your personal business AI — runs entirely on your Chromebook, free, forever.

---

## What JARVIS Does

| Capability | Details |
|---|---|
| **AI Brain** | Gemini 2.0 Flash (free) or Groq / OpenAI |
| **Persistent Memory** | Remembers every conversation via SQLite |
| **Business Notes** | Save strategies, decisions, and insights permanently |
| **Task Manager** | Create and track action items automatically |
| **Long-term Facts** | Stores key info about you and your business |
| **Web Search** | Real-time DuckDuckGo search (no key needed) |
| **File System** | Read/write files in your Linux home directory |
| **Voice Input** | Speak to JARVIS via Chrome's built-in speech API |
| **Voice Output** | JARVIS speaks back (British male voice) |
| **File Analysis** | Upload `.txt`, `.md`, `.py`, `.json`, `.csv` and more |
| **Safe Commands** | Run read-only shell commands via AI |
| **Export** | Download full conversation as Markdown |

---

## Requirements

- Chromebook with **Linux (Beta) enabled**
- **Python 3.10+** (comes with Linux on Chromebook)
- Internet for AI API calls
- **Free Gemini API key** (takes ~30 seconds to get)

---

## One-time Setup

### Step 1 — Enable Linux on your Chromebook

1. Open **Settings**
2. Go to **Advanced → Developers**
3. Click **Linux development environment → Turn on**
4. Follow the prompts (takes ~5 minutes)

### Step 2 — Copy JARVIS to Linux

Open the Linux terminal and run:

```bash
# Move JARVIS to your home directory (if not already there)
cp -r /path/to/jarvis ~/jarvis
```

Or if you cloned this repo:

```bash
cd ~
git clone <your-repo> jarvis
```

### Step 3 — Get your free Gemini API key

1. Go to **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)**
2. Click **Create API Key**
3. Copy the key (starts with `AIza...`)

> Gemini free tier: **1,500 requests/day** — more than enough for heavy personal use.

### Step 4 — Launch JARVIS

```bash
cd ~/jarvis
bash start.sh
```

JARVIS will:
- Create a virtual environment automatically
- Install all dependencies
- Open `http://localhost:5000` in your browser
- Show the setup screen where you paste your key

**That's it.** JARVIS is running.

---

## Running JARVIS Again (After First Setup)

```bash
cd ~/jarvis && bash start.sh
```

Or create a desktop shortcut / alias:

```bash
# Add to ~/.bashrc
alias jarvis="cd ~/jarvis && bash start.sh"
```

Then just type `jarvis` in any terminal.

---

## API Options

### Gemini — Recommended (Free)
- **Free tier**: 1,500 requests/day, full tool use
- **Key**: [aistudio.google.com](https://aistudio.google.com/app/apikey)
- **Model**: `gemini-2.0-flash`

### Groq — Alternative Free Option
- **Free tier**: very generous, fastest inference
- **Key**: [console.groq.com/keys](https://console.groq.com/keys)
- **Model**: `llama-3.3-70b-versatile`
- Note: no tool calling (web search, file ops disabled with Groq)

### OpenAI — Paid
- Requires a funded account
- Full tool use supported

---

## What JARVIS Can Access on Your Chromebook

Everything below runs **inside your Linux container** — safe and isolated from ChromeOS.

| Tool | What it does |
|---|---|
| `search_web` | DuckDuckGo search for live info |
| `read_file` | Read any file in Linux home (`~/`) |
| `write_file` | Create or overwrite files |
| `list_directory` | Browse your file system |
| `run_command` | Safe read-only commands (`ls`, `cat`, `grep`, `df`, `free`, etc.) |
| `get_system_info` | Memory, disk, uptime |
| `open_url` | Open a URL in Chrome |
| `save_note` | Save business notes to permanent storage |
| `get_notes` | Retrieve saved notes |
| `create_task` | Add an action item |
| `get_tasks` | List pending tasks |
| `complete_task` | Mark a task done |
| `remember_fact` | Store a permanent fact (your name, company, goals…) |
| `get_facts` | Recall all stored facts |

JARVIS chooses which tools to use **automatically** based on what you ask.

---

## Example Conversations

```
You:    I'm building a SaaS for freelance designers. What's the market like?

JARVIS: [searches web for market data automatically]
        Sir, the freelance design software market is currently valued at...
        Here are the key opportunities and your top 3 competitors...
        
        Next steps:
        1. Validate with 10 interviews in the next 7 days
        2. Map out your pricing vs. Canva, Figma, Adobe
        3. Define your moat — what can you do they cannot?

---

You:    Save that analysis as a note

JARVIS: [saves to notes automatically]
        Done. Saved as "SaaS Market Analysis — Freelance Design" 
        under the 'strategy' category.

---

You:    Create a task to do the 10 interviews by Friday

JARVIS: [creates task automatically]
        Task created: "Complete 10 freelance designer interviews"
        Due: Friday. I'll keep that on your radar, Sir.

---

You:    Read my business plan at ~/docs/plan.md and give me feedback

JARVIS: [reads the file]
        I've reviewed your plan. Here's my assessment...
```

---

## Data & Privacy

- All data stored **locally** in `~/.jarvis_memory.db` (SQLite)
- API key stored in `~/.jarvis_config.json`
- Nothing is sent anywhere except to your chosen AI API
- Conversations are only sent to Google/Groq/OpenAI as needed for responses

---

## File Structure

```
jarvis/
├── app.py          — Flask server, AI logic, tool calling
├── config.py       — API key management
├── memory.py       — SQLite: messages, notes, tasks, facts
├── tools.py        — File system, commands, web, system info
├── requirements.txt
├── start.sh        — One-command launcher
├── templates/
│   └── index.html  — JARVIS web interface
└── static/
    ├── style.css   — JARVIS dark theme
    └── jarvis.js   — Frontend: chat, voice, sidebar
```

Data files (auto-created in `~`):

```
~/.jarvis_config.json   — your API key
~/.jarvis_memory.db     — all your data
```

---

## Troubleshooting

**"Module not found" errors**
```bash
source ~/jarvis/venv/bin/activate
pip install -r ~/jarvis/requirements.txt
```

**Browser doesn't open automatically**
→ Manually open Chrome and go to `http://localhost:5000`

**Voice input not working**
→ Chrome must have microphone permission. Click the 🔒 in the address bar → Allow microphone.

**Gemini quota hit (1500/day)**
→ Wait until midnight UTC, or get a Groq key as backup.

**Port 5000 already in use**
```bash
pkill -f "python3 app.py"
bash start.sh
```

---

## Tips for Your Business

- Tell JARVIS your name, company name, and goals on first run — it will remember them forever
- Ask it to **save a note** after every important decision
- Ask it to **create tasks** after every planning session
- Use **file upload** (📎) to analyse contracts, spreadsheets, pitch decks
- Say **"search for X"** and JARVIS will pull live data from the web
- Export your conversation log (↓ button) after strategy sessions

---

*JARVIS runs 100% locally on your Chromebook. Your data stays yours.*
