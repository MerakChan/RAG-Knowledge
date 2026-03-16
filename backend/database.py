from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, BigInteger, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 数据库配置
DB_URL = "mysql+pymysql://root:123456@localhost:3306/myfinal-work?charset=utf8mb4"

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class KnowledgeBase(Base):
    __tablename__ = 'knowledge_base'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='知识库ID')
    name = Column(String(100), nullable=False, comment='知识库名称')
    description = Column(Text, nullable=True, comment='知识库描述')
    embedding_model = Column(String(100), default='bge-large', comment='向量模型')
    vector_store = Column(String(50), default='faiss', comment='向量数据库类型')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'embedding_model': self.embedding_model,
            'vector_store': self.vector_store,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }

class KnowledgeData(Base):
    __tablename__ = 'knowledge_data'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='知识数据ID')
    knowledge_id = Column(BigInteger, nullable=False, comment='所属知识库ID')
    title = Column(String(255), nullable=True, comment='标题')
    content = Column(Text, nullable=False, comment='知识内容') # 使用 Text 代替 longtext，SQLAlchemy 会根据方言自动处理
    source_type = Column(String(50), comment='数据来源(manual/document/database)')
    source_id = Column(BigInteger, nullable=True, comment='来源ID')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

class KnowledgeChunk(Base):
    __tablename__ = 'knowledge_chunk'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='chunk ID')
    knowledge_id = Column(BigInteger, nullable=False, comment='知识库ID')
    data_id = Column(BigInteger, nullable=True, comment='知识数据ID')
    document_id = Column(BigInteger, nullable=True, comment='文档ID')
    chunk_text = Column(Text, nullable=False, comment='文本块内容')
    chunk_index = Column(Integer, nullable=True, comment='文本块顺序')
    vector_status = Column(String(50), default='waiting', comment='向量化状态')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

class KnowledgeItem(Base):
    __tablename__ = 'knowledge_item'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False, comment='所属知识库')
    title = Column(String(255), nullable=True, comment='知识标题')
    source_type = Column(String(50), nullable=True, comment='数据来源类型 manual/file/mysql')
    content = Column(Text, nullable=True, comment='文本内容（手动输入或解析后的文本）')
    file_name = Column(String(255), nullable=True, comment='文件名称')
    file_path = Column(String(500), nullable=True, comment='文件路径')
    datasource_config = Column(JSON, nullable=True, comment='数据源配置(JSON)')
    chunk_count = Column(Integer, default=0, comment='文本分块数量')
    status = Column(String(20), default='processing', comment='processing / finished')
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'knowledge_id': self.knowledge_id,
            'title': self.title,
            'source_type': self.source_type,
            'file_name': self.file_name,
            'chunk_count': self.chunk_count,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }

class KnowledgeDocument(Base):
    __tablename__ = 'knowledge_document'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='文档ID')
    knowledge_id = Column(BigInteger, nullable=False, comment='所属知识库ID')
    file_name = Column(String(255), nullable=True, comment='文件名')
    file_path = Column(String(500), nullable=True, comment='文件存储路径')
    file_type = Column(String(50), nullable=True, comment='文件类型(pdf/docx/txt)')
    file_size = Column(BigInteger, nullable=True, comment='文件大小')
    parse_status = Column(String(50), default='waiting', comment='解析状态')
    create_time = Column(DateTime, default=datetime.now, comment='上传时间')

class KnowledgeDatasource(Base):
    __tablename__ = 'knowledge_datasource'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    knowledge_id = Column(BigInteger, nullable=False, comment='所属知识库')
    datasource_name = Column(String(255), comment='数据源名称')
    db_type = Column(String(50), comment='数据库类型 mysql/postgres')
    host = Column(String(255))
    port = Column(Integer)
    database_name = Column(String(255))
    username = Column(String(255))
    password = Column(String(255))
    status = Column(String(20), default='active')
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'knowledge_id': self.knowledge_id,
            'datasource_name': self.datasource_name,
            'db_type': self.db_type,
            'host': self.host,
            'port': self.port,
            'database_name': self.database_name,
            'username': self.username,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }

class KnowledgeTableSchema(Base):
    __tablename__ = 'knowledge_table_schema'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    datasource_id = Column(BigInteger, nullable=False, comment='数据源ID')
    table_name = Column(String(255), nullable=False, comment='表名')
    column_name = Column(String(255), nullable=False, comment='字段名')
    column_type = Column(String(100), comment='字段类型')
    column_comment = Column(String(255), comment='字段备注')
    is_primary_key = Column(Integer, default=0, comment='是否主键')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

class ChatSession(Base):
    __tablename__ = 'chat_session'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='会话ID')
    knowledge_id = Column(BigInteger, nullable=False, comment='知识库ID')
    session_name = Column(String(255), comment='会话名称')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        return {
            'id': self.id,
            'knowledge_id': self.knowledge_id,
            'session_name': self.session_name,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }

class ChatMessage(Base):
    __tablename__ = 'chat_message'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='消息ID')
    session_id = Column(BigInteger, nullable=False, comment='会话ID')
    role = Column(String(20), nullable=False, comment='角色 user/assistant')
    content = Column(Text, nullable=True, comment='消息内容')
    message_type = Column(String(20), default='text', comment='消息类型 text/sql/table')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'message_type': self.message_type,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
