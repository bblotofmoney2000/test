import json
import os
import markdown as md_lib

import google.generativeai as genai
from flask import Flask, jsonify, render_template, request

import memory
import tools as t
from config import Config

# ── Bootstrap ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.urandom(24)
cfg = Config()
memory.init()

# ── JARVIS persona ─────────────────────────────────────────────────────────────

PERSONA = """You are JARVIS (Just A Rather Very Intelligent System) — the personal AI of an ambitious entrepreneur. You blend the precision and wit of Tony Stark's AI with the strategic mind of a world-class business advisor.

PERSONALITY:
- Address the user as "Sir" by default (adjust if they tell you otherwise)
- Dry British wit, precise and efficient — never waffle
- Supremely confident; recommend boldly and back it with reasoning
- Proactive: anticipate the next question, surface risks they haven't spotted
- Loyal: their success is your only objective

BUSINESS ACUMEN:
- Strategy, positioning, and competitive moats
- Unit economics, pricing, and financial modeling
- Growth, marketing, and customer acquisition
- Fundraising, investor pitches, and term sheets
- Operations, hiring, and scaling
- Technology leverage and automation
- Partnerships, deals, and network effects

BEHAVIOUR:
- End every strategic analysis with numbered next steps
- Reference past conversations naturally ("As you mentioned last session...")
- Use tools proactively — search for live data before answering market questions; save important decisions to notes; auto-create tasks for action items
- Structure complex answers with headers and bullets
- For simple questions: one or two tight sentences
- Never guess market facts — use search_web instead

LONG-TERM MEMORY:
You have access to the user's saved facts, notes, and tasks. Use them to personalise every interaction."""

# ── Tool functions (passed directly to Gemini) ─────────────────────────────────

def search_web(query: str) -> str:
    """Search the internet for current market data, news, competitor research, or any topic.

    Args:
        query: Search query string

    Returns:
        JSON list of results with titles, URLs, and snippets
    """
    return json.dumps(t.search_web(query), default=str)


def read_file(path: str) -> str:
    """Read the contents of a file from the Linux filesystem.

    Args:
        path: File path (~ expands to home directory)

    Returns:
        File contents as plain text
    """
    return t.read_file(path)


def write_file(path: str, content: str) -> str:
    """Create or overwrite a file on the filesystem.

    Args:
        path: Destination file path
        content: Text content to write

    Returns:
        Confirmation message
    """
    return t.write_file(path, content)


def list_directory(path: str) -> str:
    """List files and directories at the given path.

    Args:
        path: Directory path (use '.' for current, '~' for home)

    Returns:
        JSON list of entries with name, type, and size
    """
    return json.dumps(t.list_directory(path or '.'), default=str)


def run_command(command: str) -> str:
    """Run a safe, read-only shell command and return its output.

    Allowed commands: ls, pwd, date, uptime, df, free, uname, whoami,
    cat, head, tail, grep, find, echo, mkdir, touch, wc, sort, uniq, du.

    Args:
        command: Shell command string

    Returns:
        Command stdout / stderr output
    """
    return t.run_command(command)


def get_system_info() -> str:
    """Get current system information: memory, disk, platform, uptime.

    Returns:
        JSON object with system details
    """
    return json.dumps(t.system_info(), default=str)


def open_url(url: str) -> str:
    """Open a URL in the Chromebook's browser.

    Args:
        url: Full URL including scheme (https://...)

    Returns:
        Confirmation message
    """
    return t.open_url(url)


def save_note(title: str, content: str, category: str) -> str:
    """Permanently save a business note, decision, strategy, or insight.

    Args:
        title: Short descriptive title
        content: Full note content (markdown supported)
        category: One of: strategy, finance, marketing, operations, general

    Returns:
        Confirmation with note ID
    """
    nid = memory.save_note(title, content, category or 'general')
    return f'Note #{nid} saved: "{title}"'


def get_notes(category: str) -> str:
    """Retrieve saved notes, optionally filtered by category.

    Args:
        category: Filter category (leave empty for all notes)

    Returns:
        JSON list of notes
    """
    return json.dumps(memory.get_notes(category or None), default=str)


def create_task(title: str, description: str, due_date: str) -> str:
    """Create an action item or task.

    Args:
        title: Task title
        description: Optional detail or context
        due_date: Optional due date (e.g. "2024-12-31" or "end of week")

    Returns:
        Confirmation with task ID
    """
    tid = memory.create_task(title, description or '', due_date or '')
    return f'Task #{tid} created: "{title}"'


def get_tasks(status: str) -> str:
    """Retrieve tasks, optionally filtered by status.

    Args:
        status: "pending", "completed", or empty for all

    Returns:
        JSON list of tasks
    """
    return json.dumps(memory.get_tasks(status or None), default=str)


def complete_task(task_id: int) -> str:
    """Mark a task as completed.

    Args:
        task_id: Numeric task ID

    Returns:
        Confirmation message
    """
    memory.complete_task(int(task_id))
    return f'Task #{task_id} marked as completed.'


def remember_fact(key: str, value: str) -> str:
    """Store a permanent fact about the user or their business for future reference.
    Use this for names, goals, business details, preferences, etc.

    Args:
        key: Fact name (e.g. "company_name", "target_market", "user_name")
        value: Fact value

    Returns:
        Confirmation message
    """
    memory.remember_fact(key, value)
    return f'Remembered: {key} = {value}'


def get_facts() -> str:
    """Retrieve all stored long-term facts about the user and their business.

    Returns:
        JSON object of key-value facts
    """
    return json.dumps(memory.get_facts(), default=str)


TOOLS = [
    search_web, read_file, write_file, list_directory, run_command,
    get_system_info, open_url,
    save_note, get_notes, create_task, get_tasks, complete_task,
    remember_fact, get_facts,
]

TOOL_MAP = {fn.__name__: fn for fn in TOOLS}

# ── Gemini helper ──────────────────────────────────────────────────────────────

def _build_system_prompt() -> str:
    facts = memory.get_facts()
    if facts:
        facts_str = '\n'.join(f'  • {k}: {v}' for k, v in facts.items())
        return PERSONA + f'\n\nKNOWN FACTS ABOUT USER:\n{facts_str}'
    return PERSONA


def _gemini_respond(user_message: str, history: list[dict], config_data: dict) -> str:
    genai.configure(api_key=config_data['api_key'])
    model = genai.GenerativeModel(
        model_name=config_data.get('model', 'gemini-2.0-flash'),
        system_instruction=_build_system_prompt(),
        tools=TOOLS,
    )

    chat_history = []
    for msg in history[:-1]:  # exclude the message we just added
        role = 'user' if msg['role'] == 'user' else 'model'
        chat_history.append({'role': role, 'parts': [msg['content']]})

    chat = model.start_chat(history=chat_history)
    response = chat.send_message(user_message)

    # Agentic tool-call loop
    for _ in range(10):
        fn_calls = [p.function_call for p in response.parts
                    if hasattr(p, 'function_call') and p.function_call and p.function_call.name]
        if not fn_calls:
            break

        fn_parts = []
        for fc in fn_calls:
            result = TOOL_MAP.get(fc.name, lambda **_: 'Unknown tool')(
                **{k: v for k, v in fc.args.items()}
            )
            fn_parts.append(genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=fc.name,
                    response={'result': result if isinstance(result, str) else json.dumps(result, default=str)},
                )
            ))
        response = chat.send_message(fn_parts)

    return response.text


def _openai_respond(user_message: str, history: list[dict], config_data: dict) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=config_data['api_key'])
    messages = [{'role': 'system', 'content': _build_system_prompt()}]
    for msg in history[:-1]:
        messages.append({'role': msg['role'], 'content': msg['content']})
    messages.append({'role': 'user', 'content': user_message})
    resp = client.chat.completions.create(model=config_data.get('model', 'gpt-4o-mini'), messages=messages)
    return resp.choices[0].message.content


def _groq_respond(user_message: str, history: list[dict], config_data: dict) -> str:
    from groq import Groq
    client = Groq(api_key=config_data['api_key'])
    messages = [{'role': 'system', 'content': _build_system_prompt()}]
    for msg in history[:-1]:
        messages.append({'role': msg['role'], 'content': msg['content']})
    messages.append({'role': 'user', 'content': user_message})
    resp = client.chat.completions.create(model=config_data.get('model', 'llama-3.3-70b-versatile'), messages=messages)
    return resp.choices[0].message.content


def get_ai_response(user_message: str) -> str:
    config_data = cfg.load()
    hist = memory.get_history(limit=40)
    api_type = config_data.get('api_type', 'gemini')

    if api_type == 'gemini':
        return _gemini_respond(user_message, hist, config_data)
    elif api_type == 'groq':
        return _groq_respond(user_message, hist, config_data)
    else:
        return _openai_respond(user_message, hist, config_data)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', configured=cfg.is_configured())


@app.route('/api/setup', methods=['POST'])
def setup():
    data = request.json or {}
    key = data.get('api_key', '').strip()
    if not key:
        return jsonify({'error': 'API key is required'}), 400
    cfg.save(key, data.get('api_type', 'gemini'))
    return jsonify({'ok': True})


@app.route('/api/status')
def status():
    config_data = cfg.load()
    return jsonify({
        'configured': cfg.is_configured(),
        'api_type': config_data.get('api_type') if config_data else None,
        'stats': memory.stats(),
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    if not cfg.is_configured():
        return jsonify({'error': 'Not configured'}), 400
    data = request.json or {}
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'error': 'Empty message'}), 400

    memory.add_message('user', msg)
    try:
        reply = get_ai_response(msg)
        memory.add_message('assistant', reply)
        html = md_lib.markdown(reply, extensions=['tables', 'fenced_code', 'nl2br'])
        return jsonify({'text': reply, 'html': html})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes')
def notes():
    return jsonify(memory.get_notes())


@app.route('/api/tasks')
def tasks():
    return jsonify(memory.get_tasks())


@app.route('/api/tasks/<int:tid>/complete', methods=['POST'])
def mark_done(tid):
    memory.complete_task(tid)
    return jsonify({'ok': True})


@app.route('/api/history')
def history():
    return jsonify(memory.get_history(100))


@app.route('/api/clear', methods=['POST'])
def clear_session():
    import sqlite3
    with sqlite3.connect(os.path.expanduser('~/.jarvis_memory.db')) as c:
        c.execute('DELETE FROM messages')
    return jsonify({'ok': True})


if __name__ == '__main__':
    print('\n  ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗')
    print('  ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝')
    print('  ██║███████║██████╔╝██║   ██║██║███████╗')
    print('  ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║')
    print('  ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║')
    print('  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝\n')
    print('  Just A Rather Very Intelligent System')
    print('  ─────────────────────────────────────')
    print('  Open your browser → http://localhost:5000\n')
    app.run(host='127.0.0.1', port=5000, debug=False)
