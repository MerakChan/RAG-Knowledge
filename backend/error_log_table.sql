-- 错误日志表
CREATE TABLE IF NOT EXISTS `error_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `error_level` varchar(20) NOT NULL COMMENT '错误级别：ERROR/WARNING/CRITICAL',
  `error_type` varchar(100) COMMENT '错误类型',
  `error_message` text NOT NULL COMMENT '错误消息',
  `stack_trace` text COMMENT '堆栈跟踪',
  `request_path` varchar(500) COMMENT '请求路径',
  `request_method` varchar(10) COMMENT '请求方法',
  `user_id` bigint COMMENT '用户ID',
  `ip_address` varchar(50) COMMENT 'IP地址',
  `user_agent` varchar(500) COMMENT '用户代理',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_error_level` (`error_level`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='错误日志表';

-- 示例数据
INSERT INTO `error_log` (`error_level`, `error_type`, `error_message`, `stack_trace`, `request_path`, `request_method`, `user_id`, `ip_address`) VALUES
('ERROR', 'ValueError', 'Invalid parameter value', 'Traceback (most recent call last):\n  File "app.py", line 123\n    raise ValueError("Invalid parameter")\nValueError: Invalid parameter value', '/api/chat', 'POST', 1, '127.0.0.1'),
('WARNING', 'ConnectionWarning', 'Database connection timeout', 'Connection timeout after 30s', '/api/models', 'GET', NULL, '192.168.1.100');
