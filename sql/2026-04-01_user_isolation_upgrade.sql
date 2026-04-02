USE rag_platform;

ALTER TABLE knowledge_base
    ADD COLUMN IF NOT EXISTS user_id BIGINT NULL COMMENT '所属用户ID' AFTER id,
    ADD INDEX IF NOT EXISTS idx_kb_user_id (user_id);

ALTER TABLE learning_web_bookmark
    ADD COLUMN IF NOT EXISTS user_id BIGINT NULL COMMENT '所属用户ID' AFTER id,
    ADD INDEX IF NOT EXISTS idx_bookmark_user_id (user_id);

ALTER TABLE learning_database_note
    ADD COLUMN IF NOT EXISTS user_id BIGINT NULL COMMENT '所属用户ID' AFTER id,
    ADD COLUMN IF NOT EXISTS note_type VARCHAR(50) NOT NULL DEFAULT 'sql' COMMENT 'sql/code/bugfix/summary' AFTER title,
    ADD COLUMN IF NOT EXISTS code_language VARCHAR(50) NOT NULL DEFAULT 'sql' COMMENT '代码语言' AFTER note_type,
    ADD COLUMN IF NOT EXISTS issue_note LONGTEXT NULL COMMENT 'Bug说明或关键知识点' AFTER sql_text,
    ADD INDEX IF NOT EXISTS idx_db_note_user_id (user_id);

SET @default_user_id = (SELECT MIN(id) FROM app_user);

UPDATE knowledge_base
SET user_id = @default_user_id
WHERE user_id IS NULL AND @default_user_id IS NOT NULL;

UPDATE learning_web_bookmark
SET user_id = @default_user_id
WHERE user_id IS NULL AND @default_user_id IS NOT NULL;

UPDATE learning_database_note
SET user_id = @default_user_id
WHERE user_id IS NULL AND @default_user_id IS NOT NULL;
