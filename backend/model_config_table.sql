-- 模型配置表
CREATE TABLE IF NOT EXISTS `model_config` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `model_name` varchar(100) NOT NULL COMMENT '模型名称',
  `model_type` varchar(50) NOT NULL COMMENT '模型类型：llm(大语言模型)/embedding(嵌入模型)/both(两者)',
  `api_base` varchar(500) NOT NULL COMMENT 'API基础地址',
  `api_key` varchar(500) NOT NULL COMMENT 'API密钥',
  `api_version` varchar(50) COMMENT 'API版本',
  `model_id` varchar(200) NOT NULL COMMENT '模型ID/标识',
  `description` text COMMENT '模型描述',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用：0-禁用，1-启用',
  `is_default` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否默认：0-否，1-是',
  `priority` int NOT NULL DEFAULT 0 COMMENT '优先级，数字越小越优先',
  `max_tokens` int DEFAULT NULL COMMENT '最大token数',
  `temperature` float DEFAULT NULL COMMENT '默认温度',
  `top_p` float DEFAULT NULL COMMENT '默认top_p',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by` bigint COMMENT '创建者用户ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_model_id` (`model_id`),
  KEY `idx_model_type` (`model_type`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型配置表';

-- 插入一个示例记录
INSERT INTO `model_config` (
  `model_name`, `model_type`, `api_base`, `api_key`, `model_id`, 
  `description`, `is_active`, `is_default`, `priority`, `max_tokens`
) VALUES (
  '示例模型',
  'llm',
  'https://api.example.com/v1',
  'your-api-key-here',
  'gpt-3.5-turbo',
  '这是一个示例模型配置',
  1,
  1,
  0,
  4096
);
