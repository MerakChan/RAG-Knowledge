USE rag_platform;

CREATE TABLE IF NOT EXISTS learning_quick_note (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '快速笔记ID',
    knowledge_id BIGINT NOT NULL COMMENT '所属知识库ID',
    knowledge_item_id BIGINT NULL COMMENT '关联知识条目ID',
    title VARCHAR(255) NULL COMMENT '笔记标题',
    content LONGTEXT NOT NULL COMMENT '笔记内容',
    tags MEDIUMTEXT NULL COMMENT '标签 JSON 数组',
    is_favorite TINYINT NOT NULL DEFAULT 0 COMMENT '是否收藏',
    is_pinned TINYINT NOT NULL DEFAULT 0 COMMENT '是否置顶',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_quick_note_knowledge_id (knowledge_id),
    INDEX idx_quick_note_update_time (update_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='手动快速笔记表';

CREATE TABLE IF NOT EXISTS learning_web_bookmark (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '网页收藏ID',
    knowledge_id BIGINT NULL COMMENT '关联知识库ID',
    title VARCHAR(255) NOT NULL COMMENT '网页标题',
    url VARCHAR(1000) NOT NULL COMMENT '网页地址',
    content LONGTEXT NULL COMMENT '抓取后的正文',
    summary LONGTEXT NULL COMMENT 'AI 摘要',
    tags MEDIUMTEXT NULL COMMENT '标签 JSON 数组',
    status VARCHAR(20) NOT NULL DEFAULT 'ready' COMMENT 'ready/error',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_bookmark_knowledge_id (knowledge_id),
    INDEX idx_bookmark_update_time (update_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='网页收藏表';

CREATE TABLE IF NOT EXISTS learning_database_note (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'SQL与代码记录ID',
    knowledge_id BIGINT NULL COMMENT '关联知识库ID',
    title VARCHAR(255) NOT NULL COMMENT '记录标题',
    note_type VARCHAR(50) NOT NULL DEFAULT 'sql' COMMENT 'sql/code/bugfix/summary',
    code_language VARCHAR(50) NOT NULL DEFAULT 'sql' COMMENT '代码语言',
    sql_text LONGTEXT NOT NULL COMMENT 'SQL或代码正文',
    issue_note LONGTEXT NULL COMMENT 'Bug说明或关键知识点',
    schema_snapshot LONGTEXT NULL COMMENT '表结构或上下文',
    query_result JSON NULL COMMENT '结果快照',
    summary LONGTEXT NULL COMMENT '总结说明',
    tags MEDIUMTEXT NULL COMMENT '标签 JSON 数组',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_db_note_knowledge_id (knowledge_id),
    INDEX idx_db_note_update_time (update_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SQL与代码学习记录表';

ALTER TABLE learning_database_note
    ADD COLUMN IF NOT EXISTS note_type VARCHAR(50) NOT NULL DEFAULT 'sql' COMMENT 'sql/code/bugfix/summary',
    ADD COLUMN IF NOT EXISTS code_language VARCHAR(50) NOT NULL DEFAULT 'sql' COMMENT '代码语言',
    ADD COLUMN IF NOT EXISTS issue_note LONGTEXT NULL COMMENT 'Bug说明或关键知识点';
