import json
import os

CONFIG_FILE = os.path.expanduser('~/.jarvis_config.json')

class Config:
    def save(self, api_key: str, api_type: str = 'gemini'):
        models = {
            'gemini': 'gemini-2.0-flash',
            'groq':   'llama-3.3-70b-versatile',
            'openai': 'gpt-4o-mini',
        }
        data = {'api_key': api_key, 'api_type': api_type, 'model': models.get(api_type, 'gemini-2.0-flash')}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)

    def load(self) -> dict | None:
        if not os.path.exists(CONFIG_FILE):
            return None
        with open(CONFIG_FILE) as f:
            return json.load(f)

    def is_configured(self) -> bool:
        return os.path.exists(CONFIG_FILE)
