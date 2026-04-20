import os
import secrets

#核心配置文件

class Config:
    # 安全密钥，用于会话加密
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # 文件上传根目录
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

    # 配置文件目录
    CONFIG_FOLDER = os.path.join(UPLOAD_FOLDER, 'config')
    MODEL_CONFIG_FILE = os.path.join(CONFIG_FOLDER, 'model_settings.json')
    SYSTEM_SETTINGS_FILE = os.path.join(CONFIG_FOLDER, 'system_settings.json')

    # 允许上传的文件类型
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'rtf', 'md', 'csv'}
    # 最大上传文件大小（16MB）
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # 默认AI聊天配置
    DEFAULT_CHAT_PROVIDER = os.environ.get('DEFAULT_CHAT_PROVIDER', 'deepseek')
    DEFAULT_CHAT_MODEL = os.environ.get('DEFAULT_CHAT_MODEL', 'deepseek-chat')
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-f99dbcc54bef432ea5a9ecff869ddde4')

#通过类方法为每个用户生成独立的配置文件
    @classmethod
    def user_model_config_file(cls, user_id):
        return os.path.join(cls.CONFIG_FOLDER, f'model_settings_user_{user_id}.json')

    @classmethod
    def user_system_settings_file(cls, user_id):
        return os.path.join(cls.CONFIG_FOLDER, f'system_settings_user_{user_id}.json')
