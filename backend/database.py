import json
import os
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DB_URL = os.environ.get(
    "DB_URL",
    "mysql+pymysql://root:123456@localhost:3306/rag_platform?charset=utf8mb4",
)

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AppUser(Base):
    __tablename__ = "app_user"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=True)
    status = Column(String(20), default="active")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname or self.username,
            "status": self.status,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    embedding_model = Column(String(100), default="bge-large")
    vector_store = Column(String(50), default="faiss")
    tags = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    retrieval_mode = Column(String(50), default="hybrid")
    chunk_strategy = Column(String(100), default="paragraph-balanced")
    # 新增字段
    persona = Column(Text, nullable=True)  # 角色设定
    thinking_style = Column(String(50), default="teaching")  # 思考方式
    task_policy = Column(JSON, nullable=True)  # 任务策略
    model_strategy = Column(String(100), nullable=True)  # 模型策略
    background_url = Column(String(500), nullable=True)  # 背景图片URL
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        try:
            tags = json.loads(self.tags) if self.tags else []
        except Exception:
            tags = [item.strip() for item in str(self.tags or "").split(",") if item.strip()]
        try:
            task_policy = json.loads(self.task_policy) if self.task_policy else []
        except Exception:
            task_policy = self.task_policy or []
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "embedding_model": self.embedding_model,
            "vector_store": self.vector_store,
            "tags": tags,
            "cover_url": self.cover_url,
            "category": self.category,
            "retrieval_mode": self.retrieval_mode,
            "chunk_strategy": self.chunk_strategy,
            "persona": self.persona,
            "thinking_style": self.thinking_style,
            "task_policy": task_policy,
            "model_strategy": self.model_strategy,
            "background_url": self.background_url,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }


class KnowledgeData(Base):
    __tablename__ = "knowledge_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=True)
    source_id = Column(BigInteger, nullable=True)
    create_time = Column(DateTime, default=datetime.now)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False)
    data_id = Column(BigInteger, nullable=True)
    document_id = Column(BigInteger, nullable=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=True)
    vector_status = Column(String(50), default="waiting")
    create_time = Column(DateTime, default=datetime.now)


class KnowledgeItem(Base):
    __tablename__ = "knowledge_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False)
    title = Column(String(255), nullable=True)
    source_type = Column(String(50), nullable=True)
    content = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    datasource_config = Column(JSON, nullable=True)
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="processing")
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "source_type": self.source_type,
            "file_name": self.file_name,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
        }


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False)
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    parse_status = Column(String(50), default="waiting")
    create_time = Column(DateTime, default=datetime.now)


class KnowledgeDatasource(Base):
    __tablename__ = "knowledge_datasource"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False)
    datasource_name = Column(String(255), nullable=True)
    db_type = Column(String(50), nullable=True)
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    status = Column(String(20), default="active")
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "knowledge_id": self.knowledge_id,
            "datasource_name": self.datasource_name,
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "database_name": self.database_name,
            "username": self.username,
            "status": self.status,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
        }


class KnowledgeTableSchema(Base):
    __tablename__ = "knowledge_table_schema"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    datasource_id = Column(BigInteger, nullable=False)
    table_name = Column(String(255), nullable=False)
    column_name = Column(String(255), nullable=False)
    column_type = Column(String(100), nullable=True)
    column_comment = Column(String(255), nullable=True)
    is_primary_key = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.now)


class LearningQuickNote(Base):
    __tablename__ = "learning_quick_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False)
    knowledge_item_id = Column(BigInteger, nullable=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    tags = Column(Text, nullable=True)
    is_favorite = Column(Integer, default=0)
    is_pinned = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        try:
            tags = json.loads(self.tags) if self.tags else []
        except Exception:
            tags = [item.strip() for item in str(self.tags or "").split(",") if item.strip()]
        return {
            "id": self.id,
            "knowledge_id": self.knowledge_id,
            "knowledge_item_id": self.knowledge_item_id,
            "title": self.title,
            "content": self.content,
            "tags": tags,
            "is_favorite": bool(self.is_favorite),
            "is_pinned": bool(self.is_pinned),
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }


class LearningWebBookmark(Base):
    __tablename__ = "learning_web_bookmark"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    knowledge_id = Column(BigInteger, nullable=True)
    title = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    status = Column(String(20), default="ready")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        try:
            tags = json.loads(self.tags) if self.tags else []
        except Exception:
            tags = [item.strip() for item in str(self.tags or "").split(",") if item.strip()]
        return {
            "id": self.id,
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "summary": self.summary,
            "tags": tags,
            "status": self.status,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }


class LearningDatabaseNote(Base):
    __tablename__ = "learning_database_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    knowledge_id = Column(BigInteger, nullable=True)
    title = Column(String(255), nullable=False)
    note_type = Column(String(50), default="sql")
    code_language = Column(String(50), default="sql")
    sql_text = Column(Text, nullable=False)
    issue_note = Column(Text, nullable=True)
    schema_snapshot = Column(Text, nullable=True)
    query_result = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        try:
            tags = json.loads(self.tags) if self.tags else []
        except Exception:
            tags = [item.strip() for item in str(self.tags or "").split(",") if item.strip()]
        return {
            "id": self.id,
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "note_type": self.note_type,
            "code_language": self.code_language,
            "sql_text": self.sql_text,
            "issue_note": self.issue_note,
            "schema_snapshot": self.schema_snapshot,
            "query_result": self.query_result,
            "summary": self.summary,
            "tags": tags,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }


class ChatSession(Base):
    __tablename__ = "chat_session"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False)
    session_name = Column(String(255), nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "knowledge_id": self.knowledge_id,
            "session_name": self.session_name,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=True)
    message_type = Column(String(20), default="text")
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "message_type": self.message_type,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
        }


class KnowledgeGraphNode(Base):
    __tablename__ = "knowledge_graph_node"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False, index=True)
    node_id = Column(String(255), nullable=False)
    node_type = Column(String(50), nullable=False)
    node_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        try:
            extra_data = json.loads(self.extra_data) if self.extra_data else {}
        except Exception:
            extra_data = self.extra_data or {}
        return {
            "id": self.id,
            "knowledge_id": self.knowledge_id,
            "node_id": self.node_id,
            "node_type": self.node_type,
            "node_name": self.node_name,
            "description": self.description,
            "metadata": extra_data,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }


class KnowledgeGraphEdge(Base):
    __tablename__ = "knowledge_graph_edge"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False, index=True)
    source_node_id = Column(String(255), nullable=False)
    target_node_id = Column(String(255), nullable=False)
    relation_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        try:
            extra_data = json.loads(self.extra_data) if self.extra_data else {}
        except Exception:
            extra_data = self.extra_data or {}
        return {
            "id": self.id,
            "knowledge_id": self.knowledge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "relation_type": self.relation_type,
            "description": self.description,
            "metadata": extra_data,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
        }


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
