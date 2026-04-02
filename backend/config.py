import os
import secrets

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    CONFIG_FOLDER = os.path.join(UPLOAD_FOLDER, 'config')
    MODEL_CONFIG_FILE = os.path.join(CONFIG_FOLDER, 'model_settings.json')
    SYSTEM_SETTINGS_FILE = os.path.join(CONFIG_FOLDER, 'system_settings.json')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'rtf', 'md', 'csv'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    DEFAULT_CHAT_PROVIDER = os.environ.get('DEFAULT_CHAT_PROVIDER', 'deepseek')
    DEFAULT_CHAT_MODEL = os.environ.get('DEFAULT_CHAT_MODEL', 'deepseek-chat')
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-f99dbcc54bef432ea5a9ecff869ddde4')

    @classmethod
    def user_model_config_file(cls, user_id):
        return os.path.join(cls.CONFIG_FOLDER, f'model_settings_user_{user_id}.json')

    @classmethod
    def user_system_settings_file(cls, user_id):
        return os.path.join(cls.CONFIG_FOLDER, f'system_settings_user_{user_id}.json')
