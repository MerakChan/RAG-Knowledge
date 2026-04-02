from flask import Flask, send_from_directory, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
import uuid
import json
import requests
import time
import hmac
import base64
import hashlib
import ipaddress
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, cast, Date, text
from datetime import datetime, date, timedelta
from html.parser import HTMLParser
from urllib.parse import urlparse
from database import SessionLocal, AppUser, KnowledgeBase, KnowledgeData, KnowledgeChunk, KnowledgeItem, KnowledgeDocument, KnowledgeDatasource, KnowledgeTableSchema, LearningQuickNote, LearningWebBookmark, LearningDatabaseNote, ChatSession, ChatMessage, init_db

from services.document_service import DocumentService
from services.sql_service import SQLService
from services.chunk_service import ChunkService
from services.vector_service import VectorService
from services.rag_service import RAGService
from services.model_config_service import ModelConfigService
from config import Config

app = Flask(__name__)
CORS(app)

# 初始化数据库
# 注意：在生产环境中通常使用迁移工具，这里简单起见直接调用
# init_db() # 表已经存在，可以注释掉

# 数据库会话依赖
def get_db_session():
    return SessionLocal()

# 配置
DATA_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
COVER_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data', 'covers')
ALLOWED_EXTENSIONS = {extension.lstrip('.') for extension in DocumentService.SUPPORTED_EXTENSIONS}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COVER_FOLDER'] = COVER_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COVER_FOLDER, exist_ok=True)

# 初始化服务
sql_service = SQLService()
document_service = DocumentService()
chunk_service = ChunkService(chunk_size=500, overlap=50)
vector_service = VectorService()
model_config_service = ModelConfigService(Config.MODEL_CONFIG_FILE)
rag_service = RAGService(sql_service, model_config_service)
rag_service.vector_service = vector_service

# 历史记录存储
chat_history = []

JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_SECONDS = 7 * 24 * 60 * 60
PUBLIC_API_PATHS = {
    '/api/auth/login',
    '/api/auth/register',
}
PUBLIC_API_PREFIXES = (
    '/api/media/covers/',
)


def current_user_id():
    return int(request.current_user.id)


def get_user_model_config_service(user_id):
    return ModelConfigService(Config.user_model_config_file(user_id))


def get_owned_knowledge_ids(db, user_id=None):
    owner_id = int(user_id or current_user_id())
    return [
        kb_id
        for (kb_id,) in db.query(KnowledgeBase.id).filter(KnowledgeBase.user_id == owner_id).all()
    ]


def get_owned_knowledge_base(db, knowledge_id, user_id=None):
    owner_id = int(user_id or current_user_id())
    return (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == int(knowledge_id), KnowledgeBase.user_id == owner_id)
        .first()
    )


def get_owned_session(db, session_id, user_id=None):
    owner_id = int(user_id or current_user_id())
    return (
        db.query(ChatSession)
        .join(KnowledgeBase, KnowledgeBase.id == ChatSession.knowledge_id)
        .filter(ChatSession.id == int(session_id), KnowledgeBase.user_id == owner_id)
        .first()
    )


def get_owned_knowledge_item(db, item_id, user_id=None):
    owner_id = int(user_id or current_user_id())
    return (
        db.query(KnowledgeItem)
        .join(KnowledgeBase, KnowledgeBase.id == KnowledgeItem.knowledge_id)
        .filter(KnowledgeItem.id == int(item_id), KnowledgeBase.user_id == owner_id)
        .first()
    )


def assert_owned_knowledge_base(db, knowledge_id, user_id=None):
    knowledge_base = get_owned_knowledge_base(db, knowledge_id, user_id=user_id)
    if not knowledge_base:
        raise PermissionError('Knowledge base not found')
    return knowledge_base


def jwt_b64encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('utf-8')


def jwt_b64decode(value):
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def generate_jwt(payload, expire_seconds=JWT_EXPIRE_SECONDS):
    header = {'alg': JWT_ALGORITHM, 'typ': 'JWT'}
    body = dict(payload)
    body['exp'] = int(time.time()) + expire_seconds

    header_segment = jwt_b64encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_segment = jwt_b64encode(json.dumps(body, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))
    signing_input = f"{header_segment}.{payload_segment}".encode('utf-8')
    signature = hmac.new(Config.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_segment = jwt_b64encode(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def decode_jwt(token):
    try:
        header_segment, payload_segment, signature_segment = token.split('.')
    except ValueError as exc:
        raise ValueError('Token format invalid') from exc

    signing_input = f"{header_segment}.{payload_segment}".encode('utf-8')
    expected_signature = hmac.new(Config.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    actual_signature = jwt_b64decode(signature_segment)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise ValueError('Token signature invalid')

    payload = json.loads(jwt_b64decode(payload_segment).decode('utf-8'))
    if int(payload.get('exp', 0)) < int(time.time()):
        raise ValueError('Token expired')
    return payload


def issue_user_token(user):
    return generate_jwt({
        'user_id': int(user.id),
        'username': user.username,
    })


def get_request_user():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None

    token = auth_header.replace('Bearer ', '', 1).strip()
    if not token:
        return None

    payload = decode_jwt(token)
    db = get_db_session()
    try:
        user = db.query(AppUser).filter(AppUser.id == payload.get('user_id')).first()
        if not user or user.status != 'active':
            raise ValueError('User not found or inactive')
        return user
    finally:
        db.close()


@app.before_request
def require_api_auth():
    path = request.path or ''
    if not path.startswith('/api/'):
        return None
    if request.method == 'OPTIONS':
        return None
    if path in PUBLIC_API_PATHS or path.startswith(PUBLIC_API_PREFIXES):
        return None

    try:
        user = get_request_user()
    except Exception as exc:
        return jsonify({'error': str(exc)}), 401

    if not user:
        return jsonify({'error': 'Authentication required'}), 401

    db = get_db_session()
    try:
        ensure_user_scoped_schema(db)
        ensure_learning_database_note_schema(db)
        claim_orphan_records(db, user.id)
    finally:
        db.close()

    request.current_user = user
    return None

def allowed_file(filename, content_type=''):
    return bool(DocumentService.infer_extension(filename, content_type))


def build_upload_path(filename, content_type=''):
    original_name = os.path.basename(filename or '').strip() or '未命名文件'
    file_extension = DocumentService.infer_extension(original_name, content_type)

    stem = os.path.splitext(original_name)[0].strip() or 'file'
    safe_stem = secure_filename(stem) or 'file'
    safe_name = f"{safe_stem}{file_extension}" if file_extension else safe_stem
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    return original_name, safe_name, file_extension.lstrip('.'), os.path.join(app.config['UPLOAD_FOLDER'], unique_name)


def build_cover_upload_path(filename):
    original_name = os.path.basename(filename or '').strip() or 'cover.png'
    extension = os.path.splitext(original_name)[1].lower().lstrip('.')
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        extension = 'png'

    stem = os.path.splitext(original_name)[0].strip() or 'cover'
    safe_stem = secure_filename(stem) or 'cover'
    unique_name = f"{uuid.uuid4().hex}_{safe_stem}.{extension}"
    return original_name, unique_name, os.path.join(app.config['COVER_FOLDER'], unique_name)


def save_vectors_and_chunks(db, knowledge_id, item_id, chunks, source, title='', filename='', document_id=None, data_id=None):
    if not chunks:
        raise ValueError('文档解析成功，但未生成有效分块')

    vector_ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
    metadatas = []
    chunk_records = []

    for index, chunk in enumerate(chunks):
        metadatas.append({
            'knowledge_id': str(knowledge_id),
            'item_id': str(item_id),
            'source': source,
            'title': title or '',
            'filename': filename or '',
            'document_id': str(document_id) if document_id else '',
            'data_id': str(data_id) if data_id else '',
            'chunk': index
        })
        chunk_records.append(KnowledgeChunk(
            knowledge_id=knowledge_id,
            data_id=data_id,
            document_id=document_id,
            chunk_text=chunk,
            chunk_index=index,
            vector_status='finished'
        ))

    vector_service.add_documents(chunks, ids=vector_ids, metadatas=metadatas)
    db.add_all(chunk_records)
    return len(chunks)


def parse_kb_tags(raw_value):
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]

    text = str(raw_value or '').strip()
    if not text:
        return []

    if text.startswith('['):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass

    normalized = text.replace('，', ',').replace('\n', ',')
    return [item.strip() for item in normalized.split(',') if item.strip()]


def build_kb_payload(data):
    return {
        'name': str(data.get('name', '')).strip(),
        'description': str(data.get('description', '')).strip(),
        'embedding_model': str(data.get('embedding_model', 'bge-large')).strip() or 'bge-large',
        'vector_store': str(data.get('vector_store', 'faiss')).strip() or 'faiss',
        'tags': json.dumps(parse_kb_tags(data.get('tags')), ensure_ascii=False),
        'cover_url': str(data.get('cover_url', '')).strip(),
        'category': str(data.get('category', '')).strip() or '通用学习',
        'retrieval_mode': str(data.get('retrieval_mode', 'hybrid')).strip() or 'hybrid',
        'chunk_strategy': str(data.get('chunk_strategy', 'paragraph-balanced')).strip() or 'paragraph-balanced'
    }


def ensure_learning_database_note_schema(db):
    column_rows = db.execute(text("SHOW COLUMNS FROM learning_database_note")).fetchall()
    existing_columns = {row[0] for row in column_rows}
    alter_statements = []

    if 'user_id' not in existing_columns:
        alter_statements.append("ADD COLUMN user_id BIGINT NULL COMMENT '所属用户ID' AFTER id")
    if 'note_type' not in existing_columns:
        alter_statements.append("ADD COLUMN note_type VARCHAR(50) NOT NULL DEFAULT 'sql' COMMENT 'sql/code/bugfix/summary' AFTER title")
    if 'code_language' not in existing_columns:
        after_column = 'note_type' if 'note_type' in existing_columns or any('note_type' in item for item in alter_statements) else 'title'
        alter_statements.append(f"ADD COLUMN code_language VARCHAR(50) NOT NULL DEFAULT 'sql' COMMENT '代码语言' AFTER {after_column}")
    if 'issue_note' not in existing_columns:
        after_column = 'sql_text'
        alter_statements.append(f"ADD COLUMN issue_note LONGTEXT NULL COMMENT 'Bug说明或关键知识点' AFTER {after_column}")

    for statement in alter_statements:
        db.execute(text(f"ALTER TABLE learning_database_note {statement}"))

    if alter_statements:
        db.commit()


def ensure_user_scoped_schema(db):
    table_columns = {
        'knowledge_base': {'user_id': "ADD COLUMN user_id BIGINT NULL COMMENT '所属用户ID' AFTER id"},
        'learning_web_bookmark': {'user_id': "ADD COLUMN user_id BIGINT NULL COMMENT '所属用户ID' AFTER id"},
    }

    for table_name, columns in table_columns.items():
        existing_columns = {
            row[0]
            for row in db.execute(text(f"SHOW COLUMNS FROM {table_name}")).fetchall()
        }
        for column_name, alter_sql in columns.items():
            if column_name not in existing_columns:
                db.execute(text(f"ALTER TABLE {table_name} {alter_sql}"))

    db.commit()


def claim_orphan_records(db, user_id):
    if db.query(AppUser).count() != 1:
        return

    db.query(KnowledgeBase).filter(KnowledgeBase.user_id.is_(None)).update(
        {'user_id': int(user_id)},
        synchronize_session=False
    )
    db.query(LearningWebBookmark).filter(LearningWebBookmark.user_id.is_(None)).update(
        {'user_id': int(user_id)},
        synchronize_session=False
    )
    db.query(LearningDatabaseNote).filter(LearningDatabaseNote.user_id.is_(None)).update(
        {'user_id': int(user_id)},
        synchronize_session=False
    )
    db.commit()


def ensure_user_auth_schema(db):
    table_exists = db.execute(text("SHOW TABLES LIKE 'app_user'")).fetchone()
    if table_exists:
        return

    db.execute(text("""
        CREATE TABLE app_user (
            id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
            username VARCHAR(64) NOT NULL UNIQUE COMMENT '登录用户名',
            password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
            nickname VARCHAR(100) NULL COMMENT '昵称',
            status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/inactive',
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_app_user_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表'
    """))
    db.commit()


@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.get_json() or {}
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()
    nickname = str(data.get('nickname', '')).strip()

    if len(username) < 3:
        return jsonify({'error': '用户名至少需要 3 个字符'}), 400
    if len(password) < 6:
        return jsonify({'error': '密码至少需要 6 个字符'}), 400

    db = get_db_session()
    try:
        ensure_user_auth_schema(db)
        exists = db.query(AppUser).filter(AppUser.username == username).first()
        if exists:
            return jsonify({'error': '该用户名已存在'}), 400

        user = AppUser(
            username=username,
            password_hash=generate_password_hash(password),
            nickname=nickname or username,
            status='active'
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return jsonify({
            'message': '注册成功',
            'token': issue_user_token(user),
            'user': user.to_dict()
        }), 201
    finally:
        db.close()


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.get_json() or {}
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()

    if not username or not password:
        return jsonify({'error': '请输入用户名和密码'}), 400

    db = get_db_session()
    try:
        ensure_user_auth_schema(db)
        user = db.query(AppUser).filter(AppUser.username == username).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': '用户名或密码错误'}), 401
        if user.status != 'active':
            return jsonify({'error': '账号已被禁用'}), 403

        return jsonify({
            'message': '登录成功',
            'token': issue_user_token(user),
            'user': user.to_dict()
        })
    finally:
        db.close()


@app.route('/api/auth/me', methods=['GET'])
def get_current_user_profile():
    return jsonify(request.current_user.to_dict())


def create_manual_material(db, knowledge_id, title, content, tags=None, is_favorite=False, is_pinned=False):
    clean_content = document_service.clean_text(content)
    normalized_tags = parse_kb_tags(tags)

    new_data = KnowledgeData(
        knowledge_id=knowledge_id,
        title=title,
        content=clean_content,
        source_type='manual'
    )
    db.add(new_data)
    db.flush()

    new_item = KnowledgeItem(
        knowledge_id=knowledge_id,
        title=title,
        content=clean_content,
        source_type='manual',
        datasource_config={
            'data_id': new_data.id,
            'tags': normalized_tags,
            'is_favorite': bool(is_favorite),
            'is_pinned': bool(is_pinned)
        },
        status='processing'
    )
    db.add(new_item)
    db.flush()

    quick_note = LearningQuickNote(
        knowledge_id=knowledge_id,
        knowledge_item_id=new_item.id,
        title=title or '未命名笔记',
        content=clean_content,
        tags=json.dumps(normalized_tags, ensure_ascii=False),
        is_favorite=1 if is_favorite else 0,
        is_pinned=1 if is_pinned else 0
    )
    db.add(quick_note)
    db.flush()

    new_item.datasource_config = {
        'data_id': new_data.id,
        'quick_note_id': quick_note.id,
        'tags': normalized_tags,
        'is_favorite': bool(is_favorite),
        'is_pinned': bool(is_pinned)
    }

    db.commit()
    db.refresh(new_item)

    try:
        chunks = chunk_service.split_text(clean_content)
        chunk_count = save_vectors_and_chunks(
            db,
            int(knowledge_id),
            new_item.id,
            chunks,
            source='manual',
            title=title or '手动录入',
            data_id=new_data.id
        )

        new_item.chunk_count = chunk_count
        new_item.status = 'finished'
        db.commit()
        db.refresh(quick_note)
        return new_item, quick_note, chunk_count
    except Exception:
        db.rollback()
        failed_item = db.query(KnowledgeItem).filter(KnowledgeItem.id == new_item.id).first()
        if failed_item:
            failed_item.status = 'error'
            db.commit()
        raise


class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip_stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'noscript'}:
            self.skip_stack.append(tag)

    def handle_endtag(self, tag):
        if self.skip_stack and self.skip_stack[-1] == tag:
            self.skip_stack.pop()

    def handle_data(self, data):
        if self.skip_stack:
            return
        text = str(data or '').strip()
        if text:
            self.parts.append(text)


def fetch_webpage_content(url):
    if not is_safe_web_url(url):
        raise ValueError('仅支持抓取公开的 http/https 网页地址')

    response = requests.get(url, timeout=12, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response.raise_for_status()
    html = response.text

    title_match = re_search(r'<title>(.*?)</title>', html)
    title = title_match or url

    extractor = SimpleHTMLTextExtractor()
    extractor.feed(html)
    content = document_service.clean_text('\n'.join(extractor.parts))
    return title.strip(), content


def re_search(pattern, text):
    import re
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return ''
    return document_service.clean_text(match.group(1))


def is_safe_web_url(url):
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in {'http', 'https'}:
        return False

    hostname = (parsed.hostname or '').strip().lower()
    if not hostname or hostname == 'localhost':
        return False

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False
    except ValueError:
        pass

    return True


def load_system_settings(user_id=None):
    os.makedirs(Config.CONFIG_FOLDER, exist_ok=True)
    settings_file = Config.user_system_settings_file(user_id) if user_id else Config.SYSTEM_SETTINGS_FILE
    default_settings = {
        'default_model': 'builtin-deepseek-chat',
        'default_knowledge_id': '',
        'chat_style': 'balanced',
        'theme_mode': 'light',
        'export_format': 'markdown',
        'backup_mode': 'manual',
        'sync_mode': 'local-only'
    }

    if not os.path.exists(settings_file):
        with open(settings_file, 'w', encoding='utf-8') as file:
            json.dump(default_settings, file, ensure_ascii=False, indent=2)
        return default_settings

    with open(settings_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    for key, value in default_settings.items():
        data.setdefault(key, value)
    return data


def save_system_settings(settings, user_id=None):
    os.makedirs(Config.CONFIG_FOLDER, exist_ok=True)
    settings_file = Config.user_system_settings_file(user_id) if user_id else Config.SYSTEM_SETTINGS_FILE
    current_settings = load_system_settings(user_id=user_id)
    current_settings.update(settings)
    with open(settings_file, 'w', encoding='utf-8') as file:
        json.dump(current_settings, file, ensure_ascii=False, indent=2)
    return current_settings


def build_ai_context(db, knowledge_ids, limit=8, user_id=None):
    owner_id = int(user_id or current_user_id())
    normalized_ids = [int(item) for item in knowledge_ids if str(item).strip()]
    if not normalized_ids:
        return '当前没有选择知识库。'

    kbs = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id.in_(normalized_ids), KnowledgeBase.user_id == owner_id)
        .all()
    )
    valid_ids = [item.id for item in kbs]
    if not valid_ids:
        return '所选知识库不存在或无访问权限。'

    items = (
        db.query(KnowledgeItem)
        .filter(KnowledgeItem.knowledge_id.in_(valid_ids))
        .order_by(KnowledgeItem.create_time.desc())
        .limit(limit)
        .all()
    )

    kb_lines = [f"- {kb.name}: {kb.description or '暂无描述'}" for kb in kbs]
    item_lines = []
    for item in items:
        content = (item.content or '').strip()
        if not content:
            continue
        item_lines.append(f"【{item.title or '未命名资料'}】\n{content[:1200]}")

    context_parts = []
    if kb_lines:
        context_parts.append("知识库：\n" + "\n".join(kb_lines))
    if item_lines:
        context_parts.append("资料内容：\n" + "\n\n".join(item_lines))
    return "\n\n".join(context_parts) if context_parts else '所选知识库中暂无可用资料。'

def resolve_frontend_dir():
    vue_dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vue-frontend', 'dist'))
    legacy_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    if os.path.isdir(vue_dist_dir):
        return vue_dist_dir
    return legacy_dir

@app.route('/')
def index():
    frontend_dir = resolve_frontend_dir()
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    frontend_dir = resolve_frontend_dir()
    target = os.path.join(frontend_dir, path)
    if os.path.exists(target):
        return send_from_directory(frontend_dir, path)
    return send_from_directory(frontend_dir, 'index.html')


@app.route('/api/media/covers/<path:filename>')
def serve_cover_file(filename):
    return send_from_directory(app.config['COVER_FOLDER'], filename)


@app.route('/api/knowledge/cover/upload', methods=['POST'])
def upload_knowledge_cover():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        extension = os.path.splitext(file.filename)[1].lower().lstrip('.')
        if extension not in ALLOWED_IMAGE_EXTENSIONS and not str(file.content_type or '').startswith('image/'):
            return jsonify({'error': 'Only image files are supported'}), 400

        _, saved_name, file_path = build_cover_upload_path(file.filename)
        file.save(file_path)
        return jsonify({
            'message': '封面上传成功',
            'url': f'/api/media/covers/{saved_name}',
            'file_name': saved_name
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

# 文件上传接口
@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename, file.content_type):
            return jsonify({'error': 'Invalid or unsupported file type'}), 400
        
        # 保存文件
        original_filename, _, file_type, file_path = build_upload_path(file.filename, file.content_type)
        file.save(file_path)
        
        # 获取 knowledge_id
        knowledge_id = request.form.get('knowledgeId')
        if not knowledge_id:
            return jsonify({'error': 'knowledgeId is required'}), 400
            
        db = get_db_session()
        new_item = None
        new_document = None
        try:
            assert_owned_knowledge_base(db, knowledge_id)
            file_size = os.path.getsize(file_path)

            new_document = KnowledgeDocument(
                knowledge_id=knowledge_id,
                file_name=original_filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                parse_status='processing'
            )
            db.add(new_document)
            db.flush()

            new_item = KnowledgeItem(
                knowledge_id=knowledge_id,
                title=original_filename,
                source_type='file',
                file_name=original_filename,
                file_path=file_path,
                datasource_config={'document_id': new_document.id},
                status='processing'
            )
            db.add(new_item)
            db.commit()
            db.refresh(new_item)
            db.refresh(new_document)

            # 解析、清洗并向量化文档
            text = document_service.parse_document(file_path, original_filename=original_filename, content_type=file.content_type)
            new_item.content = text
            chunks = chunk_service.split_text(text)
            chunk_count = save_vectors_and_chunks(
                db,
                int(knowledge_id),
                new_item.id,
                chunks,
                source='file',
                title=original_filename,
                filename=original_filename,
                document_id=new_document.id
            )

            new_item.chunk_count = chunk_count
            new_item.status = 'finished'
            new_document.parse_status = 'finished'
            db.commit()

            return jsonify({
                'message': '文档上传成功',
                'filename': original_filename,
                'chunks': chunk_count,
                'characters': len(text)
            })
        except Exception as e:
            db.rollback()
            if new_item and new_item.id:
                failed_item = db.query(KnowledgeItem).filter(KnowledgeItem.id == new_item.id).first()
                if failed_item:
                    failed_item.status = 'error'
            if new_document and new_document.id:
                failed_document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == new_document.id).first()
                if failed_document:
                    failed_document.parse_status = 'error'
            db.commit()
            return jsonify({'error': f'文档上传或解析失败: {str(e)}'}), 500
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 手动输入知识接口
@app.route('/api/knowledge/data/manual', methods=['POST'])
def add_manual_knowledge():
    data = request.get_json()
    knowledge_id = data.get('knowledgeId')
    title = data.get('title')
    content = data.get('content')
    tags = data.get('tags')
    is_favorite = bool(data.get('isFavorite') or data.get('is_favorite'))
    is_pinned = bool(data.get('isPinned') or data.get('is_pinned'))
    
    if not knowledge_id or not content:
        return jsonify({'error': 'Knowledge ID and content are required'}), 400
        
    db = get_db_session()
    new_item = None
    try:
        assert_owned_knowledge_base(db, knowledge_id)
        new_item, quick_note, chunk_count = create_manual_material(
            db,
            int(knowledge_id),
            title,
            content,
            tags=tags,
            is_favorite=is_favorite,
            is_pinned=is_pinned
        )

        return jsonify({
            'message': '知识添加成功',
            'item_id': new_item.id,
            'quick_note_id': quick_note.id,
            'chunks_count': chunk_count
        })
        
    except Exception as e:
        db.rollback()
        if new_item and new_item.id:
            failed_item = db.query(KnowledgeItem).filter(KnowledgeItem.id == new_item.id).first()
            if failed_item:
                failed_item.status = 'error'
        db.commit()
        return jsonify({'error': f'知识写入失败: {str(e)}'}), 500
    finally:
        db.close()

from datetime import datetime

# ----------------- 聊天会话管理接口 -----------------

@app.route('/api/chat/sessions', methods=['GET'])
def get_chat_sessions():
    knowledge_id = request.args.get('knowledge_id')
    if not knowledge_id:
        return jsonify({'error': 'knowledge_id is required'}), 400
        
    db = get_db_session()
    try:
        knowledge_base = get_owned_knowledge_base(db, knowledge_id)
        if not knowledge_base:
            return jsonify({'error': 'Knowledge base not found'}), 404

        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.knowledge_id == knowledge_base.id)
            .order_by(ChatSession.update_time.desc())
            .all()
        )
        return jsonify([session.to_dict() for session in sessions])
    finally:
        db.close()

@app.route('/api/chat/session/create', methods=['POST'])
def create_chat_session():
    data = request.get_json()
    knowledge_id = data.get('knowledgeId') or data.get('knowledge_id')
    
    if not knowledge_id:
        return jsonify({'error': 'knowledgeId is required'}), 400
        
    db = get_db_session()
    try:
        if not get_owned_knowledge_base(db, knowledge_id):
            return jsonify({'error': 'Knowledge base not found'}), 404

        # 自动生成会话名称，例如 "会话 2023-10-27 10:00"
        session_name = f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        new_session = ChatSession(
            knowledge_id=knowledge_id,
            session_name=session_name
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return jsonify(new_session.to_dict())
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/chat/messages', methods=['GET'])
def get_chat_messages():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400
        
    db = get_db_session()
    try:
        session = get_owned_session(db, session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.id.asc()).all()
        return jsonify([msg.to_dict() for msg in messages])
    finally:
        db.close()

@app.route('/api/chat/session/<int:session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    db = get_db_session()
    try:
        session = get_owned_session(db, session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
            
        # 手动级联删除消息
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        
        # 删除会话
        db.delete(session)
        db.commit()
        return jsonify({'message': 'Session deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# RAG提问接口 (更新版)
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        knowledge_id = data.get('knowledgeId') or data.get('knowledge_id')
        knowledge_ids = data.get('knowledgeIds') or []
        session_id = data.get('sessionId') or data.get('session_id') # 支持两种命名风格
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        if not session_id:
            # 如果没有 session_id，应该先创建会话，这里为了简化，报错或者自动创建
            # 前端应该保证传递 session_id
            return jsonify({'error': 'Session ID is required'}), 400

        db = get_db_session()
        try:
            session = get_owned_session(db, session_id)
            if not session:
                return jsonify({'error': 'Session not found'}), 404
            if knowledge_id and session.knowledge_id != int(knowledge_id):
                return jsonify({'error': 'Session does not belong to the selected knowledge base'}), 400
            knowledge_id = session.knowledge_id
            knowledge_ids = [
                int(item)
                for item in knowledge_ids
                if str(item).strip() and get_owned_knowledge_base(db, item)
            ]
        finally:
            db.close()
        
        # 1. 保存用户消息
        db = get_db_session()
        try:
            user_msg = ChatMessage(
                session_id=session_id,
                role='user',
                content=message
            )
            db.add(user_msg)
            
            # 更新会话时间
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.update_time = datetime.now()
                # 如果是新会话的第一条消息，可以用消息内容更新会话名称
                # 简单判断：如果只有这一条消息
                msg_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
                if msg_count == 0: # 刚插入的这条还没提交，所以是0？不对，add了但没commit
                     # 在同一个 transaction 中，count 应该能看到？或者直接更新
                     session.session_name = message[:20] # 截取前20个字
            
            db.commit()
        except Exception as e:
            db.rollback()
            return jsonify({'error': f'保存消息失败: {str(e)}'}), 500
        finally:
            db.close()
        
        def persist_assistant_message(content):
            if not str(content or '').strip():
                return

            db_inner = get_db_session()
            try:
                ai_msg = ChatMessage(
                    session_id=session_id,
                    role='assistant',
                    content=content
                )
                db_inner.add(ai_msg)
                db_inner.commit()
            except Exception as save_error:
                print(f"Error saving AI response: {save_error}")
            finally:
                db_inner.close()

        def generate():
            full_answer = ""
            try:
                # 获取流式响应，传入 knowledge_id 和 session_id (用于上下文)
                response = rag_service.query(
                    message,
                    top_k=5,
                    stream=True,
                    knowledge_id=knowledge_id,
                    knowledge_ids=knowledge_ids,
                    session_id=session_id,
                    user_id=current_user_id()
                )
                
                # 判断 response 类型
                if hasattr(response, 'iter_lines'):
                    # 这是 requests.Response 对象 (DeepSeek API 流式)
                    iterator = response.iter_lines()
                    thought_started = False
                    answer_started = False
                    first_content_chunk = True
                    for line in iterator:
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                json_str = line[6:] # 去掉 'data: ' 前缀
                                if json_str == '[DONE]':
                                    break
                                try:
                                    chunk_data = json.loads(json_str)
                                    if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                        delta = chunk_data['choices'][0].get('delta', {})
                                        reasoning = delta.get('reasoning_content', '')
                                        content = delta.get('content', '')

                                        if reasoning:
                                            if not thought_started:
                                                prefix = '[思考]：\n'
                                                full_answer += prefix
                                                yield prefix
                                                thought_started = True
                                            full_answer += reasoning
                                            yield reasoning

                                        if content:
                                            stripped_content = content.lstrip()
                                            if first_content_chunk and (stripped_content.startswith('[思考]') or stripped_content.startswith('[回答]')):
                                                answer_started = True
                                                full_answer += content
                                                yield content
                                                first_content_chunk = False
                                                continue

                                            if thought_started and not answer_started:
                                                prefix = '\n\n[回答]：\n'
                                                full_answer += prefix
                                                yield prefix
                                                answer_started = True
                                            elif not thought_started and not answer_started and not full_answer.strip().startswith('[回答]'):
                                                answer_started = True
                                            full_answer += content
                                            yield content
                                            first_content_chunk = False
                                except json.JSONDecodeError:
                                    pass
                else:
                    # 这是 Python generator 对象 (本地生成的 SQL 结果流)
                    for content in response:
                        full_answer += content
                        yield content
                
            except Exception as e:
                error_message = f"[回答]：生成失败，错误信息：{str(e)}"
                if full_answer.strip():
                    if not full_answer.endswith('\n'):
                        full_answer += '\n\n'
                    full_answer += error_message
                    yield f"\n\n{error_message}"
                else:
                    full_answer = error_message
                    yield error_message
            finally:
                persist_assistant_message(full_answer)

        return Response(stream_with_context(generate()), mimetype='text/plain')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 清除知识库接口
@app.route('/api/knowledge/clear', methods=['POST'])
def clear_knowledge():
    knowledge_id = request.args.get('knowledge_id')
    
    if not knowledge_id:
        # 如果没有传 ID，暂时不支持全局清除，或者报错
        return jsonify({'error': 'knowledge_id is required'}), 400

    db = get_db_session()
    try:
        knowledge_base = get_owned_knowledge_base(db, knowledge_id)
        if not knowledge_base:
            return jsonify({'error': 'Knowledge base not found'}), 404

        # 1. 获取该知识库下的所有 item
        items = db.query(KnowledgeItem).filter(KnowledgeItem.knowledge_id == knowledge_base.id).all()
        
        # 2. 从向量数据库中删除
        # 由于 vector_service 可能不支持 where knowledge_id (取决于实现)，我们先遍历删除
        # 或者 vector_service.collection.delete(where={"knowledge_id": str(knowledge_id)})
        # 假设 metadata 中有 knowledge_id
        try:
             vector_service.collection.delete(where={"knowledge_id": str(knowledge_base.id)})
        except Exception as e:
             print(f"Vector delete error: {e}")
             
        datasource_items = items
        for item in datasource_items:
            item_config = item.datasource_config or {}
            document_id = item_config.get('document_id')
            data_id = item_config.get('data_id')
            if document_id:
                db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document_id).delete(synchronize_session=False)
                db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).delete(synchronize_session=False)
            if data_id:
                db.query(KnowledgeChunk).filter(KnowledgeChunk.data_id == data_id).delete(synchronize_session=False)
                db.query(KnowledgeData).filter(KnowledgeData.id == data_id).delete(synchronize_session=False)

        # 3. 删除数据库记录
        db.query(LearningQuickNote).filter(LearningQuickNote.knowledge_id == knowledge_base.id).delete(synchronize_session=False)
        db.query(LearningWebBookmark).filter(LearningWebBookmark.knowledge_id == knowledge_base.id).delete(synchronize_session=False)
        db.query(LearningDatabaseNote).filter(LearningDatabaseNote.knowledge_id == knowledge_base.id).delete(synchronize_session=False)
        db.query(KnowledgeItem).filter(KnowledgeItem.knowledge_id == knowledge_base.id).delete()
        
        # 4. 删除 chat_session 和 chat_message (可选，用户可能想保留聊天记录但清除文档？)
        # 用户说 "清除该知识库下的所有文档"，所以应该只清除文档。
        
        # 5. 删除文件 (可选，如果只是逻辑删除)
        # 这里比较复杂，因为 file_path 是绝对路径。
        # 简单起见，暂不物理删除文件，或者后续添加垃圾清理任务
        
        db.commit()
        return jsonify({'message': '知识库文档已成功清除'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# 历史记录接口
@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({'history': chat_history})

# --- 新功能接口预留 ---

# 1. 系统看板接口
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    db = get_db_session()
    try:
        today = date.today()
        week_start = today - timedelta(days=6)
        owner_id = current_user_id()
        kb_ids = get_owned_knowledge_ids(db, owner_id)
        safe_kb_ids = kb_ids or [-1]
        session_ids = [
            session_id
            for (session_id,) in db.query(ChatSession.id).filter(ChatSession.knowledge_id.in_(safe_kb_ids)).all()
        ]
        safe_session_ids = session_ids or [-1]
        datasource_ids = [
            datasource_id
            for (datasource_id,) in db.query(KnowledgeDatasource.id).filter(KnowledgeDatasource.knowledge_id.in_(safe_kb_ids)).all()
        ]
        safe_datasource_ids = datasource_ids or [-1]

        kb_count = db.query(KnowledgeBase).filter(KnowledgeBase.user_id == owner_id).count()
        doc_count = db.query(KnowledgeItem).filter(
            KnowledgeItem.knowledge_id.in_(safe_kb_ids),
            KnowledgeItem.source_type.in_(['file', 'manual'])
        ).count()
        ds_count = db.query(KnowledgeDatasource).filter(KnowledgeDatasource.knowledge_id.in_(safe_kb_ids)).count()
        total_qa_count = db.query(ChatMessage).filter(
            ChatMessage.session_id.in_(safe_session_ids),
            ChatMessage.role == 'assistant'
        ).count()
        total_question_count = db.query(ChatMessage).filter(
            ChatMessage.session_id.in_(safe_session_ids),
            ChatMessage.role == 'user'
        ).count()

        today_qa_count = db.query(ChatMessage).filter(
            ChatMessage.session_id.in_(safe_session_ids),
            ChatMessage.role == 'user',
            cast(ChatMessage.create_time, Date) == today
        ).count()

        today_note_count = db.query(KnowledgeItem).filter(
            KnowledgeItem.knowledge_id.in_(safe_kb_ids),
            KnowledgeItem.source_type.in_(['file', 'manual']),
            cast(KnowledgeItem.create_time, Date) == today
        ).count()

        today_kb_count = db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == owner_id,
            cast(KnowledgeBase.create_time, Date) == today
        ).count()

        today_ds_count = db.query(KnowledgeDatasource).filter(
            KnowledgeDatasource.knowledge_id.in_(safe_kb_ids),
            cast(KnowledgeDatasource.create_time, Date) == today
        ).count()

        chunk_count = db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_id.in_(safe_kb_ids)).count()
        table_count = db.query(
            func.count(distinct(func.concat(KnowledgeTableSchema.datasource_id, '_', KnowledgeTableSchema.table_name)))
        ).filter(KnowledgeTableSchema.datasource_id.in_(safe_datasource_ids)).scalar()
        column_count = db.query(KnowledgeTableSchema).filter(KnowledgeTableSchema.datasource_id.in_(safe_datasource_ids)).count()

        recent_qa = []
        recent_msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id.in_(safe_session_ids), ChatMessage.role == 'user')
            .order_by(ChatMessage.create_time.desc())
            .limit(5)
            .all()
        )
        for msg in recent_msgs:
            session = db.query(ChatSession).filter(ChatSession.id == msg.session_id).first()
            kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == session.knowledge_id).first() if session else None
            recent_qa.append({
                'question': msg.content,
                'kb_name': kb.name if kb else '未知知识库',
                'time': msg.create_time.strftime('%H:%M') if msg.create_time else ''
            })

        trend_data = []
        for i in range(6, -1, -1):
            current_day = today - timedelta(days=i)
            day_str = current_day.strftime('%m-%d')
            count = db.query(ChatMessage).filter(
                ChatMessage.session_id.in_(safe_session_ids),
                ChatMessage.role == 'user',
                cast(ChatMessage.create_time, Date) == current_day
            ).count()
            trend_data.append({'date': day_str, 'count': count})

        recent_documents = []
        recent_docs = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.knowledge_id.in_(safe_kb_ids))
            .order_by(KnowledgeDocument.create_time.desc())
            .limit(5)
            .all()
        )
        for document in recent_docs:
            kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == document.knowledge_id).first()
            recent_documents.append({
                'name': document.file_name or '未命名文档',
                'knowledge_base': kb.name if kb else '未指定知识库',
                'time': document.create_time.strftime('%m-%d %H:%M') if document.create_time else '',
                'status': document.parse_status or 'waiting'
            })

        recent_kb_map = {}
        recent_sessions = (
            db.query(ChatSession)
            .filter(ChatSession.knowledge_id.in_(safe_kb_ids))
            .order_by(ChatSession.update_time.desc())
            .limit(12)
            .all()
        )
        for session in recent_sessions:
            if session.knowledge_id in recent_kb_map:
                continue
            kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == session.knowledge_id).first()
            if not kb:
                continue
            recent_kb_map[session.knowledge_id] = {
                'id': kb.id,
                'name': kb.name,
                'time': session.update_time.strftime('%m-%d %H:%M') if session.update_time else ''
            }
        recent_visited_kbs = list(recent_kb_map.values())[:5]

        topic_candidates = []
        latest_sessions = (
            db.query(ChatSession)
            .filter(ChatSession.knowledge_id.in_(safe_kb_ids))
            .order_by(ChatSession.update_time.desc())
            .limit(8)
            .all()
        )
        for session in latest_sessions:
            if session.session_name:
                topic_candidates.append(session.session_name)
        latest_items = (
            db.query(KnowledgeItem)
            .filter(KnowledgeItem.knowledge_id.in_(safe_kb_ids))
            .order_by(KnowledgeItem.create_time.desc())
            .limit(8)
            .all()
        )
        for item in latest_items:
            if item.title:
                topic_candidates.append(item.title)
        recent_learning_topics = []
        for topic in topic_candidates:
            normalized = topic.strip()
            if normalized and normalized not in recent_learning_topics:
                recent_learning_topics.append(normalized)
            if len(recent_learning_topics) >= 6:
                break

        weekly_hot_question_rows = (
            db.query(ChatMessage.content, func.count(ChatMessage.id).label('ask_count'))
            .filter(
                ChatMessage.session_id.in_(safe_session_ids),
                ChatMessage.role == 'user',
                cast(ChatMessage.create_time, Date) >= week_start
            )
            .group_by(ChatMessage.content)
            .order_by(func.count(ChatMessage.id).desc(), func.max(ChatMessage.create_time).desc())
            .limit(5)
            .all()
        )
        weekly_hot_questions = [{'question': row[0], 'count': row[1]} for row in weekly_hot_question_rows if row[0]]

        recent_summary_messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id.in_(safe_session_ids), ChatMessage.role == 'assistant')
            .order_by(ChatMessage.create_time.desc())
            .limit(5)
            .all()
        )
        recent_summaries = []
        for message in recent_summary_messages:
            session = db.query(ChatSession).filter(ChatSession.id == message.session_id).first()
            kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == session.knowledge_id).first() if session else None
            recent_summaries.append({
                'summary': (message.content or '').strip()[:180],
                'knowledge_base': kb.name if kb else '未指定知识库',
                'time': message.create_time.strftime('%m-%d %H:%M') if message.create_time else ''
            })
            if len(recent_summaries) >= 3:
                break

        active_days = set()
        recent_item_days = db.query(cast(KnowledgeItem.create_time, Date)).filter(KnowledgeItem.knowledge_id.in_(safe_kb_ids)).distinct().all()
        recent_question_days = db.query(cast(ChatMessage.create_time, Date)).filter(
            ChatMessage.session_id.in_(safe_session_ids),
            ChatMessage.role == 'user'
        ).distinct().all()
        for row in recent_item_days + recent_question_days:
            active_days.add(row[0])

        streak_days = 0
        cursor = today
        while cursor in active_days:
            streak_days += 1
            cursor -= timedelta(days=1)

        return jsonify({
            'overall': {
                'kb_count': kb_count,
                'doc_count': doc_count,
                'ds_count': ds_count,
                'qa_count': total_qa_count,
                'question_count': total_question_count
            },
            'today': {
                'qa_count': today_qa_count,
                'doc_count': today_note_count,
                'kb_count': today_kb_count,
                'ds_count': today_ds_count
            },
            'knowledge': {
                'chunk_count': chunk_count,
                'table_count': table_count or 0,
                'column_count': column_count
            },
            'recent_qa': recent_qa,
            'trend': trend_data,
            'workspace': {
                'today_new_notes': today_note_count,
                'today_question_count': today_qa_count,
                'recent_learning_topics': recent_learning_topics,
                'recent_upload_documents': recent_documents,
                'recent_visited_knowledge_bases': recent_visited_kbs,
                'learning_streak_days': streak_days,
                'weekly_hot_questions': weekly_hot_questions,
                'recent_summaries': recent_summaries
            }
        })
    except Exception as e:
        print(f"Dashboard Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# 2. 知识库管理接口
@app.route('/api/knowledge/list', methods=['GET'])
def list_knowledge_bases():
    db = get_db_session()
    try:
        kbs = (
            db.query(KnowledgeBase)
            .filter(KnowledgeBase.user_id == current_user_id())
            .order_by(KnowledgeBase.update_time.desc())
            .all()
        )
        return jsonify([kb.to_dict() for kb in kbs])
    finally:
        db.close()

@app.route('/api/knowledge/create', methods=['POST'])
def create_knowledge_base():
    data = request.get_json()
    payload = build_kb_payload(data)
    if not payload['name']:
        return jsonify({'error': 'Knowledge base name is required'}), 400
    
    db = get_db_session()
    try:
        new_kb = KnowledgeBase(user_id=current_user_id(), **payload)
        db.add(new_kb)
        db.commit()
        db.refresh(new_kb)
        return jsonify(new_kb.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/knowledge/update', methods=['PUT'])
def update_knowledge_base():
    data = request.get_json()
    kb_id = data.get('id')
    if not kb_id:
        return jsonify({'error': 'Knowledge base ID is required'}), 400
    
    db = get_db_session()
    try:
        kb = get_owned_knowledge_base(db, kb_id)
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404

        payload = build_kb_payload(data)
        for field, value in payload.items():
            setattr(kb, field, value)
            
        db.commit()
        db.refresh(kb)
        return jsonify(kb.to_dict())
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/knowledge/delete/<int:kb_id>', methods=['DELETE'])
def delete_knowledge_base(kb_id):
    db = get_db_session()
    try:
        kb = get_owned_knowledge_base(db, kb_id)
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404

        datasource_ids = [
            datasource_id
            for (datasource_id,) in db.query(KnowledgeDatasource.id).filter(KnowledgeDatasource.knowledge_id == kb_id).all()
        ]
        session_ids = [
            session_id
            for (session_id,) in db.query(ChatSession.id).filter(ChatSession.knowledge_id == kb_id).all()
        ]

        try:
            vector_service.collection.delete(where={"knowledge_id": str(kb_id)})
        except Exception as vector_error:
            print(f"Vector delete error for knowledge base {kb_id}: {vector_error}")

        # 1. 先删依赖会话的消息
        if session_ids:
            db.query(ChatMessage).filter(ChatMessage.session_id.in_(session_ids)).delete(synchronize_session=False)

        # 2. 再删依赖数据源的表结构
        if datasource_ids:
            db.query(KnowledgeTableSchema).filter(KnowledgeTableSchema.datasource_id.in_(datasource_ids)).delete(synchronize_session=False)

        # 3. 删除与知识库直接关联的数据
        db.query(LearningQuickNote).filter(LearningQuickNote.knowledge_id == kb_id).delete(synchronize_session=False)
        db.query(LearningWebBookmark).filter(LearningWebBookmark.knowledge_id == kb_id).delete(synchronize_session=False)
        db.query(LearningDatabaseNote).filter(LearningDatabaseNote.knowledge_id == kb_id).delete(synchronize_session=False)
        db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_id == kb_id).delete(synchronize_session=False)
        db.query(KnowledgeData).filter(KnowledgeData.knowledge_id == kb_id).delete(synchronize_session=False)
        db.query(KnowledgeDocument).filter(KnowledgeDocument.knowledge_id == kb_id).delete(synchronize_session=False)
        db.query(KnowledgeItem).filter(KnowledgeItem.knowledge_id == kb_id).delete(synchronize_session=False)

        # 4. 删除会话与数据源
        if session_ids:
            db.query(ChatSession).filter(ChatSession.id.in_(session_ids)).delete(synchronize_session=False)
        if datasource_ids:
            db.query(KnowledgeDatasource).filter(KnowledgeDatasource.id.in_(datasource_ids)).delete(synchronize_session=False)

        # 5. 最后删除知识库
        db.delete(kb)

        db.commit()
        return jsonify({'message': 'Knowledge base deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# ----------------- 文档/数据项管理接口 -----------------

@app.route('/api/knowledge/items/<int:kb_id>', methods=['GET'])
def list_knowledge_items(kb_id):
    db = get_db_session()
    try:
        if not get_owned_knowledge_base(db, kb_id):
            return jsonify({'error': 'Knowledge base not found'}), 404
        items = db.query(KnowledgeItem).filter(KnowledgeItem.knowledge_id == kb_id).order_by(KnowledgeItem.create_time.desc()).all()
        return jsonify([item.to_dict() for item in items])
    finally:
        db.close()

@app.route('/api/knowledge/item/<int:item_id>', methods=['DELETE'])
def delete_knowledge_item(item_id):
    db = get_db_session()
    try:
        item = get_owned_knowledge_item(db, item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        # 注意：这里也需要从向量数据库中删除对应的 chunk
        # 由于我们之前将 item_id 存入了 metadata，我们可以根据 item_id 删除
        if vector_service.use_chroma:
            vector_service.collection.delete(
                where={"item_id": str(item_id)}
            )

        item_config = item.datasource_config or {}
        document_id = item_config.get('document_id')
        data_id = item_config.get('data_id')

        if document_id:
            db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document_id).delete(synchronize_session=False)
            db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).delete(synchronize_session=False)
        elif item.file_path:
            linked_document = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_id == item.knowledge_id,
                KnowledgeDocument.file_path == item.file_path
            ).first()
            if linked_document:
                db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == linked_document.id).delete(synchronize_session=False)
                db.delete(linked_document)

        if data_id:
            db.query(KnowledgeChunk).filter(KnowledgeChunk.data_id == data_id).delete(synchronize_session=False)
            db.query(KnowledgeData).filter(KnowledgeData.id == data_id).delete(synchronize_session=False)

        db.query(LearningQuickNote).filter(LearningQuickNote.knowledge_item_id == item.id).delete(synchronize_session=False)
            
        db.delete(item)
        db.commit()
        return jsonify({'message': 'Item deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# 3. 数据源管理接口
@app.route('/api/datasources', methods=['GET', 'POST'])
def manage_datasources():
    db = get_db_session()
    try:
        if request.method == 'GET':
            knowledge_id = request.args.get('knowledge_id')
            query = db.query(KnowledgeDatasource).join(KnowledgeBase, KnowledgeBase.id == KnowledgeDatasource.knowledge_id).filter(
                KnowledgeBase.user_id == current_user_id()
            )
            if knowledge_id:
                query = query.filter(KnowledgeDatasource.knowledge_id == knowledge_id)
            datasources = query.order_by(KnowledgeDatasource.create_time.desc()).all()
            return jsonify([item.to_dict() for item in datasources])

        return jsonify({'error': 'Method not supported here'}), 405
    finally:
        db.close()

@app.route('/api/datasource/test', methods=['POST'])
def test_datasource_connection():
    data = request.get_json()
    try:
        success, message = sql_service.test_connection(
            data['dbType'], data['host'], data['port'], 
            data['username'], data['password'], data['databaseName']
        )
        if success:
            return jsonify({'message': '连接成功'})
        else:
            return jsonify({'error': message}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/datasource/add', methods=['POST'])
def add_datasource():
    data = request.get_json()
    knowledge_id = data.get('knowledgeId')
    
    if not knowledge_id:
        return jsonify({'error': 'knowledgeId is required'}), 400
        
    db = get_db_session()
    try:
        if not get_owned_knowledge_base(db, knowledge_id):
            return jsonify({'error': 'Knowledge base not found'}), 404

        # 1. 验证连接
        success, message = sql_service.test_connection(
            data['dbType'], data['host'], data['port'], 
            data['username'], data['password'], data['databaseName']
        )
        if not success:
            return jsonify({'error': f'连接测试失败: {message}'}), 400
            
        # 2. 获取 Schema (结构化)
        structured_schema = sql_service.get_schema(
            data['dbType'], data['host'], data['port'], 
            data['username'], data['password'], data['databaseName']
        )
        
        # 3. 保存数据源配置
        new_ds = KnowledgeDatasource(
            knowledge_id=knowledge_id,
            datasource_name=data['datasourceName'],
            db_type=data['dbType'],
            host=data['host'],
            port=data['port'],
            database_name=data['databaseName'],
            username=data['username'],
            password=data['password'] # 实际生产中应加密存储
        )
        db.add(new_ds)
        db.commit()
        db.refresh(new_ds)
        
        # 4. 保存结构化 Schema 到 knowledge_table_schema 表
        for col_info in structured_schema:
            new_schema = KnowledgeTableSchema(
                datasource_id=new_ds.id,
                table_name=col_info['table_name'],
                column_name=col_info['column_name'],
                column_type=col_info['column_type'],
                column_comment=col_info['column_comment'],
                is_primary_key=col_info['is_primary_key']
            )
            db.add(new_schema)
            
        # 5. 为了保持兼容性和 RAG 检索，我们仍然生成一个 Schema 文本并存入 KnowledgeItem
        # 但这次我们从 structured_schema 构建文本
        schema_map = {}
        for item in structured_schema:
            table = item['table_name']
            if table not in schema_map:
                schema_map[table] = []
            col_def = f"{item['column_name']} {item['column_type']}"
            if item['column_comment']:
                col_def += f" -- {item['column_comment']}"
            if item['is_primary_key']:
                col_def += " (PK)"
            schema_map[table].append(col_def)
        
        schema_text = ""
        for table, cols in schema_map.items():
            schema_text += f"Table {table}\n" + "\n".join(cols) + "\n\n"
            
        new_item = KnowledgeItem(
            knowledge_id=knowledge_id,
            title=f"Database Schema: {data['databaseName']}",
            source_type='database_schema',
            content=schema_text,
            datasource_config={
                'id': new_ds.id,
                'type': data['dbType'],
                'host': data['host'],
                'port': data['port'],
                'db': data['databaseName'],
                'user': data['username']
            },
            status='finished'
        )
        db.add(new_item)
        db.commit()
        
        # 将 Schema item 存入向量库
        chunks = [schema_text] # 简单起见，整个 schema 作为一个 chunk，如果很大可能需要切分
        doc_ids = [str(uuid.uuid4())]
        metadatas = [{
            'knowledge_id': str(knowledge_id),
            'item_id': str(new_item.id),
            'source': 'database_schema',
            'title': new_item.title,
            'chunk': 0,
            'datasource_id': str(new_ds.id)
        }]
        vector_service.add_documents(chunks, ids=doc_ids, metadatas=metadatas)
        
        return jsonify({'message': '数据源添加成功', 'id': new_ds.id})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/materials/quick-notes', methods=['GET', 'POST'])
def manage_quick_notes():
    db = get_db_session()
    try:
        if request.method == 'GET':
            knowledge_id = request.args.get('knowledge_id')
            query = db.query(LearningQuickNote).filter(LearningQuickNote.knowledge_id.in_(get_owned_knowledge_ids(db) or [-1]))
            if knowledge_id:
                if not get_owned_knowledge_base(db, knowledge_id):
                    return jsonify({'error': 'Knowledge base not found'}), 404
                query = query.filter(LearningQuickNote.knowledge_id == knowledge_id)
            notes = query.order_by(LearningQuickNote.is_pinned.desc(), LearningQuickNote.update_time.desc()).all()
            return jsonify([item.to_dict() for item in notes])

        data = request.get_json() or {}
        knowledge_id = data.get('knowledgeId')
        title = str(data.get('title', '')).strip()
        content = str(data.get('content', '')).strip()
        if not knowledge_id or not content:
            return jsonify({'error': 'knowledgeId and content are required'}), 400
        if not get_owned_knowledge_base(db, knowledge_id):
            return jsonify({'error': 'Knowledge base not found'}), 404

        new_item, quick_note, chunk_count = create_manual_material(
            db,
            int(knowledge_id),
            title,
            content,
            tags=data.get('tags'),
            is_favorite=bool(data.get('isFavorite') or data.get('is_favorite')),
            is_pinned=bool(data.get('isPinned') or data.get('is_pinned'))
        )
        response = quick_note.to_dict()
        response['chunks_count'] = chunk_count
        response['knowledge_item_id'] = new_item.id
        return jsonify(response), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/materials/quick-notes/<int:note_id>', methods=['DELETE'])
def delete_quick_note(note_id):
    db = get_db_session()
    try:
        note = db.query(LearningQuickNote).filter(
            LearningQuickNote.id == note_id,
            LearningQuickNote.knowledge_id.in_(get_owned_knowledge_ids(db) or [-1])
        ).first()
        if not note:
            return jsonify({'error': 'Quick note not found'}), 404

        knowledge_item_id = note.knowledge_item_id
        linked_item = None
        if knowledge_item_id:
            linked_item = db.query(KnowledgeItem).filter(KnowledgeItem.id == knowledge_item_id).first()

        if linked_item:
            try:
                vector_service.collection.delete(where={"item_id": str(linked_item.id)})
            except Exception as vector_error:
                print(f"Vector delete error for quick note {note_id}: {vector_error}")

            item_config = linked_item.datasource_config or {}
            data_id = item_config.get('data_id')
            if data_id:
                db.query(KnowledgeChunk).filter(KnowledgeChunk.data_id == data_id).delete(synchronize_session=False)
                db.query(KnowledgeData).filter(KnowledgeData.id == data_id).delete(synchronize_session=False)
            db.delete(linked_item)

        db.delete(note)
        db.commit()
        return jsonify({'message': 'Quick note deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/materials/bookmarks', methods=['GET', 'POST'])
def manage_bookmarks():
    db = get_db_session()
    try:
        if request.method == 'GET':
            knowledge_id = request.args.get('knowledge_id')
            query = db.query(LearningWebBookmark).filter(LearningWebBookmark.user_id == current_user_id())
            if knowledge_id:
                if not get_owned_knowledge_base(db, knowledge_id):
                    return jsonify({'error': 'Knowledge base not found'}), 404
                query = query.filter(LearningWebBookmark.knowledge_id == knowledge_id)
            bookmarks = query.order_by(LearningWebBookmark.update_time.desc()).all()
            return jsonify([item.to_dict() for item in bookmarks])

        data = request.get_json() or {}
        url = str(data.get('url', '')).strip()
        if not url:
            return jsonify({'error': 'url is required'}), 400

        title = str(data.get('title', '')).strip()
        tags = json.dumps(parse_kb_tags(data.get('tags')), ensure_ascii=False)
        knowledge_id = data.get('knowledgeId') or None
        if knowledge_id and not get_owned_knowledge_base(db, knowledge_id):
            return jsonify({'error': 'Knowledge base not found'}), 404

        try:
            parsed_title, content = fetch_webpage_content(url)
            final_title = title or parsed_title or url
            summary_prompt = f"""请为以下网页学习资料生成一个简洁摘要，突出核心知识点和适合后续复习的内容。

标题：{final_title}
URL：{url}
正文：
{content[:6000]}

请输出 3 到 5 条中文要点。"""
            summary = rag_service.call_deepseek_api(summary_prompt, stream=False, user_id=current_user_id())
            status = 'ready'
        except Exception as exc:
            final_title = title or url
            content = ''
            summary = f'网页抓取失败：{str(exc)}'
            status = 'error'

        bookmark = LearningWebBookmark(
            user_id=current_user_id(),
            knowledge_id=knowledge_id,
            title=final_title,
            url=url,
            content=content,
            summary=summary,
            tags=tags,
            status=status
        )
        db.add(bookmark)
        db.commit()
        db.refresh(bookmark)
        return jsonify(bookmark.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/materials/bookmarks/<int:bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
    db = get_db_session()
    try:
        bookmark = db.query(LearningWebBookmark).filter(
            LearningWebBookmark.id == bookmark_id,
            LearningWebBookmark.user_id == current_user_id()
        ).first()
        if not bookmark:
            return jsonify({'error': 'Bookmark not found'}), 404
        db.delete(bookmark)
        db.commit()
        return jsonify({'message': 'Bookmark deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/materials/database-notes', methods=['GET', 'POST'])
def manage_database_notes():
    db = get_db_session()
    try:
        ensure_learning_database_note_schema(db)

        if request.method == 'GET':
            knowledge_id = request.args.get('knowledge_id')
            query = db.query(LearningDatabaseNote).filter(LearningDatabaseNote.user_id == current_user_id())
            if knowledge_id:
                if not get_owned_knowledge_base(db, knowledge_id):
                    return jsonify({'error': 'Knowledge base not found'}), 404
                query = query.filter(LearningDatabaseNote.knowledge_id == knowledge_id)
            notes = query.order_by(LearningDatabaseNote.update_time.desc()).all()
            return jsonify([item.to_dict() for item in notes])

        data = request.get_json() or {}
        title = str(data.get('title', '')).strip()
        sql_text = str(data.get('sqlText', '')).strip()
        if not title or not sql_text:
            return jsonify({'error': 'title and sqlText are required'}), 400
        if data.get('knowledgeId') and not get_owned_knowledge_base(db, data.get('knowledgeId')):
            return jsonify({'error': 'Knowledge base not found'}), 404

        schema_snapshot = str(data.get('schemaSnapshot', '')).strip()
        query_result_raw = data.get('queryResult')
        if isinstance(query_result_raw, str):
            try:
                query_result = json.loads(query_result_raw)
            except json.JSONDecodeError:
                query_result = {'raw': query_result_raw}
        else:
            query_result = query_result_raw

        note_type = str(data.get('noteType', 'sql')).strip() or 'sql'
        code_language = str(data.get('codeLanguage', 'sql')).strip() or 'sql'
        issue_note = str(data.get('issueNote', '')).strip()
        summary = str(data.get('summary', '')).strip()
        if not summary:
            summary_prompt = f"""你是一名代码与数据库学习助手。请根据下面的代码或 SQL、问题背景、表结构说明和结果，生成适合复习的总结。

标题：{title}
类型：{note_type}
语言：{code_language}
代码或 SQL：
{sql_text}

问题背景 / Bug 记录：
{issue_note or '未提供'}

表结构：
{schema_snapshot or '未提供'}

查询结果：
{json.dumps(query_result, ensure_ascii=False) if query_result else '未提供'}

请用中文输出 3 到 5 条总结。"""
            summary = rag_service.call_deepseek_api(summary_prompt, stream=False, user_id=current_user_id())

        note = LearningDatabaseNote(
            user_id=current_user_id(),
            knowledge_id=data.get('knowledgeId') or None,
            title=title,
            note_type=note_type,
            code_language=code_language,
            sql_text=sql_text,
            issue_note=issue_note,
            schema_snapshot=schema_snapshot,
            query_result=query_result,
            summary=summary,
            tags=json.dumps(parse_kb_tags(data.get('tags')), ensure_ascii=False)
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/materials/database-notes/<int:note_id>', methods=['DELETE'])
def delete_database_note(note_id):
    db = get_db_session()
    try:
        note = db.query(LearningDatabaseNote).filter(
            LearningDatabaseNote.id == note_id,
            LearningDatabaseNote.user_id == current_user_id()
        ).first()
        if not note:
            return jsonify({'error': 'Database note not found'}), 404
        db.delete(note)
        db.commit()
        return jsonify({'message': 'Database note deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/learning/trajectory', methods=['GET'])
def get_learning_trajectory():
    db = get_db_session()
    try:
        today = date.today()
        kb_ids = get_owned_knowledge_ids(db)
        safe_kb_ids = kb_ids or [-1]
        session_ids = [
            session_id
            for (session_id,) in db.query(ChatSession.id).filter(ChatSession.knowledge_id.in_(safe_kb_ids)).all()
        ]
        safe_session_ids = session_ids or [-1]
        daily_activity = []
        for offset in range(27, -1, -1):
            current_day = today - timedelta(days=offset)
            note_count = db.query(KnowledgeItem).filter(
                KnowledgeItem.knowledge_id.in_(safe_kb_ids),
                cast(KnowledgeItem.create_time, Date) == current_day
            ).count()
            ask_count = db.query(ChatMessage).filter(
                ChatMessage.session_id.in_(safe_session_ids),
                ChatMessage.role == 'user',
                cast(ChatMessage.create_time, Date) == current_day
            ).count()
            bookmark_count = db.query(LearningWebBookmark).filter(
                LearningWebBookmark.user_id == current_user_id(),
                cast(LearningWebBookmark.create_time, Date) == current_day
            ).count()
            daily_activity.append({
                'date': current_day.strftime('%m-%d'),
                'score': note_count + ask_count + bookmark_count,
                'notes': note_count,
                'questions': ask_count,
                'bookmarks': bookmark_count
            })

        weekly_minutes = sum(item['score'] for item in daily_activity[-7:]) * 8

        tag_counter = {}
        for kb in db.query(KnowledgeBase).filter(KnowledgeBase.user_id == current_user_id()).all():
            for tag in parse_kb_tags(kb.tags):
                tag_counter[tag] = tag_counter.get(tag, 0) + 1
        hot_tags = [{'tag': key, 'count': value} for key, value in sorted(tag_counter.items(), key=lambda item: item[1], reverse=True)[:8]]

        weak_points = []
        repeated_questions = (
            db.query(ChatMessage.content, func.count(ChatMessage.id).label('ask_count'))
            .filter(ChatMessage.session_id.in_(safe_session_ids), ChatMessage.role == 'user')
            .group_by(ChatMessage.content)
            .order_by(func.count(ChatMessage.id).desc())
            .limit(5)
            .all()
        )
        for row in repeated_questions:
            weak_points.append({'topic': row[0], 'count': row[1]})

        return jsonify({
            'daily_activity': daily_activity,
            'weekly_minutes': weekly_minutes,
            'hot_tags': hot_tags,
            'weak_points': weak_points
        })
    finally:
        db.close()


@app.route('/api/ai/tools', methods=['POST'])
def run_ai_tools():
    data = request.get_json() or {}
    action = data.get('action')
    knowledge_ids = data.get('knowledgeIds') or []

    db = get_db_session()
    try:
        context = build_ai_context(db, knowledge_ids, user_id=current_user_id())
        user_prompt = str(data.get('prompt', '')).strip()
        selected_kbs = db.query(KnowledgeBase).filter(
            KnowledgeBase.id.in_([int(item) for item in knowledge_ids if str(item).strip()]),
            KnowledgeBase.user_id == current_user_id()
        ).all()
        kb_names = [item.name for item in selected_kbs]

        prompt_map = {
            'summary': f"请基于以下知识资料，输出结构化摘要，并给出适合复习的要点。\n\n{context}\n\n附加要求：{user_prompt or '请总结核心内容。'}",
            'quiz': f"请基于以下知识资料生成 10 道中文学习题，覆盖基础理解、应用和追问，并附参考答案。\n\n{context}\n\n附加要求：{user_prompt or '题目适合面试和复习。'}",
            'review_plan': f"请基于以下知识资料和遗忘曲线，生成一个 7 天中文复习计划，包含第1天、第3天、第7天等关键节点。\n\n{context}\n\n附加要求：{user_prompt or '计划要适合个人学习执行。'}",
            'association': f"请分析以下多知识库内容，找出重复出现或可以建立联系的概念，并用“概念A -> 概念B：关系说明”形式输出。\n\n{context}\n\n附加要求：{user_prompt or '请突出跨知识库的关联。'}"
        }

        if action == 'build_agent':
            agent_name = str(data.get('agentName', '')).strip() or '专属学习助手'
            agent_goal = str(data.get('agentGoal', '')).strip() or '围绕选定知识库回答相关学习问题'
            response_style = str(data.get('responseStyle', '')).strip() or '严谨讲解'
            answer_strategy = str(data.get('answerStrategy', '')).strip() or '先结论后展开'
            output_language = str(data.get('outputLanguage', '')).strip() or '中文'
            markdown_requirement = '必须使用清晰的 Markdown 结构输出。'

            prompt = f"""你是一名 AI 学习助手设计师，现在需要为用户生成一个“可用于后续问答的学习助手配置方案”。

请基于以下知识库内容与用户目标，输出一个适合直接展示的 Markdown 文档。

助手名称：{agent_name}
助手目标：{agent_goal}
回答风格：{response_style}
回答策略：{answer_strategy}
输出语言：{output_language}
关联知识库：{', '.join(kb_names) if kb_names else '未选择'}
补充要求：{user_prompt or '请突出助手定位、回答边界和推荐提问方式。'}

知识上下文：
{context}

输出要求：
1. 必须使用 Markdown。
2. 包含这些一级或二级标题：
   - 助手定位
   - 知识范围
   - 回答策略
   - 默认工作流
   - 推荐提问方式
   - 示例对话
   - 系统提示词
3. “系统提示词”部分请给出一段可直接复用的提示词。
4. 结果应像一个真正已经配置好的学习助手说明书，便于后续拿来回答问题。
5. {markdown_requirement}
"""
            result = rag_service.call_deepseek_api(prompt, stream=False, user_id=current_user_id())
            return jsonify({
                'result': result,
                'agent_name': agent_name,
                'knowledge_names': kb_names
            })

        if action not in prompt_map:
            return jsonify({'error': 'Unsupported action'}), 400

        result = rag_service.call_deepseek_api(prompt_map[action], stream=False, user_id=current_user_id())
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# 5. 模型管理接口
@app.route('/api/models', methods=['GET', 'POST'])
def manage_models():
    try:
        model_service = get_user_model_config_service(current_user_id())
        if request.method == 'GET':
            return jsonify(model_service.list_models())

        data = request.get_json() or {}
        action = data.get('action', 'save_custom')

        if action == 'save_custom':
            required_fields = ['name', 'model_name', 'base_url']
            missing_fields = [field for field in required_fields if not str(data.get(field, '')).strip()]
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
            return jsonify(model_service.save_custom_model(data))

        if action == 'activate':
            model_id = data.get('model_id')
            if not model_id:
                return jsonify({'error': 'model_id is required'}), 400
            return jsonify(model_service.activate_model(model_id))

        if action == 'set_embedding':
            embedding_model_id = data.get('embedding_model_id')
            if not embedding_model_id:
                return jsonify({'error': 'embedding_model_id is required'}), 400
            return jsonify(model_service.set_embedding_model(embedding_model_id))

        if action == 'delete_custom':
            model_id = data.get('model_id')
            if not model_id:
                return jsonify({'error': 'model_id is required'}), 400
            return jsonify(model_service.delete_custom_model(model_id))

        return jsonify({'error': 'Unsupported action'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 6. 系统管理接口
@app.route('/api/system/config', methods=['GET', 'POST'])
def manage_system_config():
    try:
        if request.method == 'GET':
            return jsonify(load_system_settings(user_id=current_user_id()))

        data = request.get_json() or {}
        return jsonify(save_system_settings(data, user_id=current_user_id()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
