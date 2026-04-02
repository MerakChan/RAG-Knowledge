USE rag_platform;

ALTER TABLE knowledge_base
  ADD COLUMN tags MEDIUMTEXT NULL COMMENT '知识库标签，JSON 数组' AFTER vector_store,
  ADD COLUMN cover_url VARCHAR(500) NULL COMMENT '知识库封面 URL' AFTER tags,
  ADD COLUMN category VARCHAR(100) NULL COMMENT '知识库分类' AFTER cover_url,
  ADD COLUMN retrieval_mode VARCHAR(50) NOT NULL DEFAULT 'hybrid' COMMENT '检索模式' AFTER category,
  ADD COLUMN chunk_strategy VARCHAR(100) NOT NULL DEFAULT 'paragraph-balanced' COMMENT 'Chunk 策略' AFTER retrieval_mode;

CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_base_update_time ON knowledge_base(update_time);

UPDATE knowledge_base
SET
  category = COALESCE(NULLIF(category, ''), '通用学习'),
  retrieval_mode = COALESCE(NULLIF(retrieval_mode, ''), 'hybrid'),
  chunk_strategy = COALESCE(NULLIF(chunk_strategy, ''), 'paragraph-balanced'),
  tags = CASE
    WHEN tags IS NULL OR tags = '' THEN JSON_ARRAY()
    ELSE tags
  END;
