CREATE DATABASE IF NOT EXISTS rag_platform DEFAULT CHARACTER SET utf8mb4;
USE rag_platform;

CREATE TABLE app_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(64) NOT NULL UNIQUE COMMENT '登录用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    nickname VARCHAR(100) NULL COMMENT '昵称',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/inactive',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

CREATE TABLE knowledge_base (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '知识库ID',
    name VARCHAR(100) NOT NULL COMMENT '知识库名称',
    description MEDIUMTEXT COMMENT '知识库描述',
    embedding_model VARCHAR(100) DEFAULT 'bge-large' COMMENT 'Embedding 模型',
    vector_store VARCHAR(50) DEFAULT 'faiss' COMMENT '向量数据库类型',
    tags MEDIUMTEXT COMMENT '知识库标签，JSON 数组',
    cover_url VARCHAR(500) COMMENT '知识库封面 URL',
    category VARCHAR(100) DEFAULT '通用学习' COMMENT '知识库分类',
    retrieval_mode VARCHAR(50) DEFAULT 'hybrid' COMMENT '检索模式',
    chunk_strategy VARCHAR(100) DEFAULT 'paragraph-balanced' COMMENT 'Chunk 策略',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库表';

CREATE TABLE knowledge_document (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '文档ID',
    knowledge_id BIGINT NOT NULL COMMENT '所属知识库ID',
    file_name VARCHAR(255) COMMENT '文件名',
    file_path VARCHAR(500) COMMENT '文件存储路径',
    file_type VARCHAR(50) COMMENT '文件类型',
    file_size BIGINT COMMENT '文件大小',
    parse_status VARCHAR(50) DEFAULT 'waiting' COMMENT '解析状态',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    CONSTRAINT fk_doc_kb FOREIGN KEY (knowledge_id) REFERENCES knowledge_base(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识文档表';

CREATE TABLE knowledge_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '知识数据ID',
    knowledge_id BIGINT NOT NULL COMMENT '所属知识库ID',
    title VARCHAR(255) COMMENT '标题',
    content LONGTEXT NOT NULL COMMENT '知识内容',
    source_type VARCHAR(50) COMMENT 'manual/document/database',
    source_id BIGINT COMMENT '来源ID',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_data_kb FOREIGN KEY (knowledge_id) REFERENCES knowledge_base(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识数据表';

CREATE TABLE knowledge_datasource (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '数据源ID',
    knowledge_id BIGINT NOT NULL COMMENT '所属知识库',
    datasource_name VARCHAR(255) COMMENT '数据源名称',
    db_type VARCHAR(50) COMMENT 'mysql/postgres',
    host VARCHAR(255),
    port INT,
    database_name VARCHAR(255),
    username VARCHAR(255),
    password VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ds_kb FOREIGN KEY (knowledge_id) REFERENCES knowledge_base(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库数据源表';

CREATE TABLE knowledge_table_schema (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    datasource_id BIGINT NOT NULL COMMENT '数据源ID',
    table_name VARCHAR(255) NOT NULL COMMENT '表名',
    column_name VARCHAR(255) NOT NULL COMMENT '字段名',
    column_type VARCHAR(100) COMMENT '字段类型',
    column_comment VARCHAR(255) COMMENT '字段备注',
    is_primary_key TINYINT DEFAULT 0 COMMENT '是否主键',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_schema_ds FOREIGN KEY (datasource_id) REFERENCES knowledge_datasource(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库表结构信息';

CREATE TABLE knowledge_chunk (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'chunk ID',
    knowledge_id BIGINT NOT NULL COMMENT '知识库ID',
    data_id BIGINT COMMENT '知识数据ID',
    document_id BIGINT COMMENT '文档ID',
    chunk_text LONGTEXT NOT NULL COMMENT '文本块内容',
    chunk_index INT COMMENT '文本块顺序',
    vector_status VARCHAR(50) DEFAULT 'waiting' COMMENT '向量化状态',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chunk_kb FOREIGN KEY (knowledge_id) REFERENCES knowledge_base(id),
    CONSTRAINT fk_chunk_data FOREIGN KEY (data_id) REFERENCES knowledge_data(id),
    CONSTRAINT fk_chunk_doc FOREIGN KEY (document_id) REFERENCES knowledge_document(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文本 chunk 表';

CREATE TABLE knowledge_item (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    knowledge_id BIGINT NOT NULL COMMENT '所属知识库',
    title VARCHAR(255) COMMENT '知识标题',
    source_type VARCHAR(50) COMMENT 'manual/file/mysql',
    content LONGTEXT COMMENT '文本内容',
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    datasource_config JSON,
    chunk_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processing',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_item_kb FOREIGN KEY (knowledge_id) REFERENCES knowledge_base(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='综合知识条目表';

CREATE TABLE learning_web_bookmark (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '网页收藏ID',
    knowledge_id BIGINT NULL COMMENT '关联知识库ID',
    title VARCHAR(255) NOT NULL COMMENT '网页标题',
    url VARCHAR(1000) NOT NULL COMMENT '网页地址',
    content LONGTEXT COMMENT '解析正文',
    summary LONGTEXT COMMENT 'AI 摘要',
    tags MEDIUMTEXT COMMENT '标签 JSON 数组',
    status VARCHAR(20) DEFAULT 'ready' COMMENT 'ready/error',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='网页收藏表';

CREATE TABLE learning_database_note (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '数据库笔记ID',
    knowledge_id BIGINT NULL COMMENT '关联知识库ID',
    title VARCHAR(255) NOT NULL COMMENT '笔记标题',
    sql_text LONGTEXT NOT NULL COMMENT 'SQL 语句',
    schema_snapshot LONGTEXT COMMENT '表结构快照',
    query_result JSON COMMENT '查询结果',
    summary LONGTEXT COMMENT '总结说明',
    tags MEDIUMTEXT COMMENT '标签 JSON 数组',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库学习笔记表';

CREATE TABLE chat_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '会话ID',
    knowledge_id BIGINT NOT NULL COMMENT '知识库ID',
    session_name VARCHAR(255) COMMENT '会话名称',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_kb FOREIGN KEY (knowledge_id) REFERENCES knowledge_base(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天会话表';

CREATE TABLE chat_message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '消息ID',
    session_id BIGINT NOT NULL COMMENT '会话ID',
    role VARCHAR(20) NOT NULL COMMENT 'user/assistant',
    content LONGTEXT COMMENT '消息内容',
    message_type VARCHAR(20) DEFAULT 'text' COMMENT 'text/sql/table',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_session(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天消息记录';
