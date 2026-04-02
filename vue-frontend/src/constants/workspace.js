export const tabs = [
  { key: 'dashboard', label: '首页工作台', desc: '查看今日学习状态', icon: 'HM' },
  { key: 'datasource', label: '学习资料中心', desc: '接入文件与网页资料', icon: 'DS' },
  { key: 'knowledge', label: '我的知识库', desc: '组织个人知识体系', icon: 'KB' },
  { key: 'chat', label: 'AI问答中心', desc: '围绕知识库智能问答', icon: 'AI' },
  { key: 'agent', label: '学习助手Agent', desc: '生成专属学习助手', icon: 'AG' },
  { key: 'models', label: '模型与API配置', desc: '混合大模型选择与设置', icon: 'ML' },
  { key: 'trajectory', label: '学习轨迹', desc: '追踪成长与薄弱点', icon: 'TR' },
  { key: 'settings', label: '个人设置', desc: '偏好、备份与同步', icon: 'ME' }
]

export const sourceMap = {
  file: '文件资料',
  manual: '快速笔记',
  database_schema: '数据库结构'
}

export const statusMap = {
  finished: '已完成',
  processing: '处理中',
  error: '失败'
}
