import os
import subprocess
import platform
from datetime import datetime

SAFE_CMDS = {
    'ls', 'pwd', 'date', 'uptime', 'df', 'free', 'uname', 'whoami',
    'cat', 'head', 'tail', 'grep', 'find', 'echo', 'mkdir', 'touch',
    'wc', 'sort', 'uniq', 'du', 'env', 'printenv', 'which',
}


def read_file(path: str) -> str:
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return f'File not found: {path}'
    if os.path.getsize(path) > 512 * 1024:
        return 'File too large (>512 KB). Use head/tail via run_command instead.'
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return f'Error reading file: {e}'


def write_file(path: str, content: str) -> str:
    path = os.path.expanduser(path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f'Written: {path}'


def list_directory(path: str = '.') -> list[dict]:
    path = os.path.expanduser(path or '.')
    if not os.path.exists(path):
        return [{'error': f'Not found: {path}'}]
    items = []
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        items.append({
            'name': name,
            'type': 'dir' if os.path.isdir(full) else 'file',
            'size': os.path.getsize(full) if os.path.isfile(full) else None,
        })
    return items


def run_command(command: str) -> str:
    parts = command.strip().split()
    if not parts:
        return 'Empty command.'
    if parts[0] not in SAFE_CMDS:
        return f'"{parts[0]}" is not in the safe command list: {sorted(SAFE_CMDS)}'
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        return (result.stdout + result.stderr).strip() or '(no output)'
    except subprocess.TimeoutExpired:
        return 'Command timed out (15 s).'
    except Exception as e:
        return f'Error: {e}'


def system_info() -> dict:
    info: dict = {
        'platform': platform.platform(),
        'python': platform.python_version(),
        'time': datetime.now().isoformat(),
    }
    for cmd, key in [('free -h', 'memory'), ('df -h /', 'disk'), ('uptime', 'uptime')]:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            info[key] = r.stdout.strip()
        except Exception:
            pass
    return info


def open_url(url: str) -> str:
    try:
        subprocess.Popen(['xdg-open', url])
        return f'Opening in browser: {url}'
    except Exception as e:
        return f'Could not open browser ({e}). URL: {url}'


def search_web(query: str) -> list[dict]:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=6))
    except ImportError:
        return [{'error': 'duckduckgo-search not installed. Run: pip install duckduckgo-search'}]
    except Exception as e:
        return [{'error': str(e)}]
