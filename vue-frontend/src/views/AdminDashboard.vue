<template>
  <div class="admin-page">
    <div class="admin-layout">
      <!-- 左侧菜单栏 -->
      <aside class="admin-sidebar">
        <div class="sidebar-header">
          <h2>系统管理</h2>
        </div>
        <nav class="sidebar-nav">
          <button 
            v-for="item in menuItems" 
            :key="item.id"
            class="nav-item"
            :class="{ active: activeMenu === item.id }"
            @click="activeMenu = item.id"
          >
            <svg :viewBox="item.iconViewBox" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path :d="item.iconPath" fill="currentColor"/>
            </svg>
            {{ item.label }}
          </button>
        </nav>
      </aside>

      <!-- 右侧内容区 -->
      <main class="admin-main">
        <div class="admin-header">
          <div class="header-left">
            <h1>欢迎回来，{{ authUser.nickname || authUser.username }}！</h1>
            <p class="subtitle">超级管理员控制台</p>
          </div>
          <div class="header-right">
            <div class="user-profile-dropdown" :class="{ open: settingsOpen }">
              <div class="user-profile-mini" @click="toggleSettings">
                <div class="avatar">{{ (authUser.nickname || authUser.username || '管')[0] }}</div>
                <div class="info">
                  <strong>{{ authUser.nickname || authUser.username }}</strong>
                  <span>超级管理员</span>
                </div>
                <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="dropdown-menu" v-if="settingsOpen">
                <div class="dropdown-item" @click="handleLogout">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17 7L15.59 8.41L18.17 11H8V13H18.17L15.59 15.58L17 17L22 12L17 7Z" fill="currentColor"/>
                    <path d="M6 3H12V5H6V19H12V21H6C4.9 21 4 20.1 4 19V5C4 3.9 4.9 3 6 3Z" fill="currentColor"/>
                  </svg>
                  退出登录
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="admin-content">
          <!-- 用户管理 -->
          <div v-if="activeMenu === 'user-management'" class="menu-content user-management">
            <div class="content-header">
              <h2>用户管理</h2>
            </div>
            <div class="user-management-layout">
              <!-- 上半部分：用户使用情况 -->
              <div class="user-usage-section">
                <h3>用户使用情况</h3>
                <div class="usage-chart-container">
                  <div v-for="user in users" :key="user.id" class="usage-bar">
                    <div class="user-info">
                      <span class="username">{{ user.nickname || user.username }}</span>
                      <span class="chat-count">{{ user.chat_count }} 次对话</span>
                    </div>
                    <div class="bar-container">
                      <div class="bar" :style="{ width: getBarWidth(user.chat_count) + '%' }"></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 下半部分：用户状态管理 -->
              <div class="user-status-section">
                <h3>用户状态管理</h3>
                <div class="user-list-container">
                  <div v-for="user in users" :key="user.id" class="user-item">
                    <div class="user-basic-info">
                      <div class="avatar-small">{{ (user.nickname || user.username || '用')[0] }}</div>
                      <div class="user-details">
                        <div class="name">{{ user.nickname || user.username }}</div>
                        <div class="username-text">@{{ user.username }}</div>
                      </div>
                      <div class="user-status-badge" :class="user.status">
                        {{ user.status === 'active' ? '正常' : '冻结' }}
                      </div>
                    </div>
                    <div class="user-actions">
                      <button class="btn-action" @click="toggleUserStatus(user)">
                        {{ user.status === 'active' ? '冻结' : '解冻' }}
                      </button>
                      <button class="btn-action btn-edit" @click="openEditUser(user)">
                        编辑
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 系统配置 -->
          <div v-else-if="activeMenu === 'system-config'" class="menu-content">
            <div class="content-header">
              <div class="header-actions">
                <h2>系统配置</h2>
                <button class="btn-primary btn-sm" @click="openCreateModel">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  添加模型
                </button>
              </div>
            </div>
            <div class="models-grid">
              <div v-for="model in models" :key="model.id" class="model-card">
                <div class="model-header">
                  <div class="model-title">
                    <h4>{{ model.model_name }}</h4>
                    <span class="model-id">{{ model.model_id }}</span>
                  </div>
                  <div class="model-badges">
                    <span class="badge" :class="model.is_active ? 'active' : 'inactive'">
                      {{ model.is_active ? '启用' : '禁用' }}
                    </span>
                    <span v-if="model.is_default" class="badge default">默认</span>
                  </div>
                </div>
                <div class="model-body">
                  <div class="model-info-item">
                    <span class="info-label">模型类型</span>
                    <span class="info-value">{{ modelTypeLabel(model.model_type) }}</span>
                  </div>
                  <div class="model-info-item">
                    <span class="info-label">API地址</span>
                    <span class="info-value">{{ model.api_base }}</span>
                  </div>
                  <div class="model-info-item">
                    <span class="info-label">API密钥</span>
                    <span class="info-value">{{ model.api_key }}</span>
                  </div>
                  <div v-if="model.description" class="model-info-item">
                    <span class="info-label">描述</span>
                    <span class="info-value">{{ model.description }}</span>
                  </div>
                </div>
                <div class="model-footer">
                  <div class="model-meta">
                    <span>优先级: {{ model.priority }}</span>
                    <span v-if="model.max_tokens">最大Token: {{ model.max_tokens }}</span>
                  </div>
                  <div class="model-actions">
                    <button class="btn-action btn-sm" @click="openEditModel(model)">
                      编辑
                    </button>
                    <button v-if="!model.is_default" class="btn-action btn-sm" @click="setDefaultModel(model)">
                      设为默认
                    </button>
                    <button class="btn-action btn-sm btn-danger" @click="deleteModel(model)">
                      删除
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 日志系统 -->
          <div v-else-if="activeMenu === 'log-system'" class="menu-content">
            <div class="content-header">
              <div class="header-actions">
                <h2>日志系统</h2>
                <button class="btn-primary btn-sm" v-if="selectedLogs.length > 0" @click="batchDeleteLogs">
                  批量删除 ({{ selectedLogs.length }})
                </button>
              </div>
            </div>
            
            <!-- 筛选条件 -->
            <div class="surface-panel filter-section">
              <div class="filter-row">
                <div class="filter-item">
                  <label>错误级别</label>
                  <select v-model="filters.errorLevel" @change="loadLogs">
                    <option value="">全部</option>
                    <option value="ERROR">ERROR</option>
                    <option value="WARNING">WARNING</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
                <div class="filter-item">
                  <label>开始日期</label>
                  <input type="date" v-model="filters.startDate" @change="loadLogs">
                </div>
                <div class="filter-item">
                  <label>结束日期</label>
                  <input type="date" v-model="filters.endDate" @change="loadLogs">
                </div>
                <div class="filter-item">
                  <button class="btn-secondary btn-sm" @click="resetFilters">重置</button>
                  <button class="btn-primary btn-sm" @click="loadLogs">刷新</button>
                </div>
              </div>
            </div>
            
            <!-- 日志列表 -->
            <div class="surface-panel logs-table-container">
              <table class="logs-table">
                <thead>
                  <tr>
                    <th style="width: 40px;">
                      <input type="checkbox" v-model="selectAll" @change="toggleSelectAll">
                    </th>
                    <th style="width: 80px;">级别</th>
                    <th style="width: 150px;">类型</th>
                    <th>错误消息</th>
                    <th style="width: 100px;">用户ID</th>
                    <th style="width: 150px;">IP地址</th>
                    <th style="width: 180px;">时间</th>
                    <th style="width: 120px;">操作</th>
                  </tr>
                </thead>
                <tbody v-if="logs.length > 0">
                  <tr v-for="log in logs" :key="log.id" :class="`log-row log-${log.error_level.toLowerCase()}`">
                    <td>
                      <input type="checkbox" v-model="selectedLogs" :value="log.id">
                    </td>
                    <td>
                      <span class="log-badge" :class="`badge-${log.error_level.toLowerCase()}`">
                        {{ log.error_level }}
                      </span>
                    </td>
                    <td>{{ log.error_type || '-' }}</td>
                    <td class="log-message">
                      {{ truncateMessage(log.error_message, 100) }}
                    </td>
                    <td>{{ log.user_id || '-' }}</td>
                    <td>{{ log.ip_address || '-' }}</td>
                    <td>{{ formatDate(log.created_at) }}</td>
                    <td>
                      <button class="btn-action btn-sm" @click="viewLogDetail(log)">查看</button>
                      <button class="btn-action btn-sm btn-danger" @click="deleteLog(log)">删除</button>
                    </td>
                  </tr>
                </tbody>
                <tbody v-else>
                  <tr>
                    <td colspan="8" class="empty-table">暂无日志数据</td>
                  </tr>
                </tbody>
              </table>
              
              <!-- 分页 -->
              <div class="pagination" v-if="total > 0">
                <button class="btn-secondary btn-sm" :disabled="page === 1" @click="prevPage">上一页</button>
                <span class="page-info">第 {{ page }} 页 / 共 {{ totalPages }} 页 (共 {{ total }} 条)</span>
                <button class="btn-secondary btn-sm" :disabled="page === totalPages" @click="nextPage">下一页</button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- 编辑用户弹窗 -->
    <div v-if="editModalOpen" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑用户</h3>
          <button class="close-btn" @click="closeEditModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户名</label>
            <input type="text" v-model="editForm.username" placeholder="请输入用户名" />
          </div>
          <div class="form-group">
            <label>昵称</label>
            <input type="text" v-model="editForm.nickname" placeholder="请输入昵称" />
          </div>
          <div class="form-group">
            <label>新密码（留空不修改）</label>
            <input type="password" v-model="editForm.password" placeholder="请输入新密码" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeEditModal">取消</button>
          <button class="btn-primary" @click="saveUserEdit">保存</button>
        </div>
      </div>
    </div>

    <!-- 模型配置弹窗 -->
    <div v-if="modelModalOpen" class="modal-overlay modal-large" @click.self="closeModelModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ isEditModel ? '编辑模型配置' : '添加模型配置' }}</h3>
          <button class="close-btn" @click="closeModelModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>模型名称 <span class="required">*</span></label>
              <input type="text" v-model="modelForm.model_name" placeholder="例如：GPT-4" />
            </div>
            <div class="form-group">
              <label>模型类型 <span class="required">*</span></label>
              <select v-model="modelForm.model_type">
                <option value="llm">大语言模型(LLM)</option>
                <option value="embedding">嵌入模型</option>
                <option value="both">两者</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>模型ID <span class="required">*</span></label>
              <input type="text" v-model="modelForm.model_id" placeholder="例如：gpt-4" />
            </div>
            <div class="form-group">
              <label>API版本</label>
              <input type="text" v-model="modelForm.api_version" placeholder="例如：2024-02-15-preview" />
            </div>
          </div>
          <div class="form-group">
            <label>API基础地址 <span class="required">*</span></label>
            <input type="text" v-model="modelForm.api_base" placeholder="例如：https://api.openai.com/v1" />
          </div>
          <div class="form-group">
            <label>API密钥 <span class="required">*</span></label>
            <input type="password" v-model="modelForm.api_key" placeholder="请输入API密钥" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>优先级</label>
              <input type="number" v-model.number="modelForm.priority" placeholder="数值越小越优先" />
            </div>
            <div class="form-group">
              <label>最大Token数</label>
              <input type="number" v-model.number="modelForm.max_tokens" placeholder="例如：4096" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>默认温度</label>
              <input type="number" v-model.number="modelForm.temperature" step="0.1" placeholder="0.0-2.0" min="0" max="2" />
            </div>
            <div class="form-group">
              <label>默认Top-P</label>
              <input type="number" v-model.number="modelForm.top_p" step="0.1" placeholder="0.0-1.0" min="0" max="1" />
            </div>
          </div>
          <div class="form-group">
            <label>模型描述</label>
            <textarea v-model="modelForm.description" placeholder="请输入模型描述" rows="3"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group checkbox-group">
              <input type="checkbox" id="is_active" v-model="modelForm.is_active" />
              <label for="is_active">启用该模型</label>
            </div>
            <div class="form-group checkbox-group">
              <input type="checkbox" id="is_default" v-model="modelForm.is_default" />
              <label for="is_default">设为默认模型</label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModelModal">取消</button>
          <button class="btn-primary" @click="saveModel">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 日志详情弹窗 -->
    <div v-if="logDetailModalOpen" class="modal-overlay modal-large" @click.self="closeLogDetailModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>日志详情</h3>
          <button class="close-btn" @click="closeLogDetailModal">×</button>
        </div>
        <div class="modal-body" v-if="currentLog">
          <div class="log-detail-section">
            <div class="log-detail-row">
              <span class="log-detail-label">错误级别：</span>
              <span class="log-detail-value">
                <span class="log-badge" :class="`badge-${currentLog.error_level.toLowerCase()}`">
                  {{ currentLog.error_level }}
                </span>
              </span>
            </div>
            <div class="log-detail-row">
              <span class="log-detail-label">错误类型：</span>
              <span class="log-detail-value">{{ currentLog.error_type || '-' }}</span>
            </div>
            <div class="log-detail-row">
              <span class="log-detail-label">错误消息：</span>
              <span class="log-detail-value log-detail-message">{{ currentLog.error_message }}</span>
            </div>
            <div class="log-detail-row">
              <span class="log-detail-label">用户ID：</span>
              <span class="log-detail-value">{{ currentLog.user_id || '-' }}</span>
            </div>
            <div class="log-detail-row">
              <span class="log-detail-label">IP地址：</span>
              <span class="log-detail-value">{{ currentLog.ip_address || '-' }}</span>
            </div>
            <div class="log-detail-row">
              <span class="log-detail-label">请求路径：</span>
              <span class="log-detail-value">{{ currentLog.request_path || '-' }}</span>
            </div>
            <div class="log-detail-row">
              <span class="log-detail-label">请求方法：</span>
              <span class="log-detail-value">{{ currentLog.request_method || '-' }}</span>
            </div>
            <div class="log-detail-row">
              <span class="log-detail-label">用户代理：</span>
              <span class="log-detail-value">{{ currentLog.user_agent || '-' }}</span>
            </div>
            <div class="log-detail-row">
              <span class="log-detail-label">创建时间：</span>
              <span class="log-detail-value">{{ formatDate(currentLog.created_at) }}</span>
            </div>
            <div v-if="currentLog.stack_trace" class="log-detail-stack">
              <span class="log-detail-label">堆栈跟踪：</span>
              <pre class="stack-trace">{{ currentLog.stack_trace }}</pre>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeLogDetailModal">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getAuthUser, clearAuthSession } from '../utils/auth'
import axios from 'axios'

const router = useRouter()
const authUser = getAuthUser()
const settingsOpen = ref(false)
const activeMenu = ref('user-management')
const users = ref([])
const editModalOpen = ref(false)
const editForm = ref({
  id: null,
  username: '',
  nickname: '',
  password: ''
})

const models = ref([])
const modelModalOpen = ref(false)
const isEditModel = ref(false)
const modelForm = ref({
  id: null,
  model_name: '',
  model_type: 'llm',
  api_base: '',
  api_key: '',
  api_version: '',
  model_id: '',
  description: '',
  is_active: true,
  is_default: false,
  priority: 0,
  max_tokens: null,
  temperature: null,
  top_p: null
})

// 日志系统相关状态
const logs = ref([])
const logsLoading = ref(false)
const logDetailModalOpen = ref(false)
const currentLog = ref(null)
const selectedLogs = ref([])
const selectAll = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = ref({
  errorLevel: '',
  startDate: '',
  endDate: ''
})

const menuItems = [
  {
    id: 'user-management',
    label: '用户管理',
    iconViewBox: '0 0 24 24',
    iconPath: 'M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12ZM12 14C9.33 14 4 15.34 4 18V20H20V18C20 15.34 14.67 14 12 14Z'
  },
  {
    id: 'system-config',
    label: '系统配置',
    iconViewBox: '0 0 24 24',
    iconPath: 'M12 15.5C13.933 15.5 15.5 13.933 15.5 12C15.5 10.067 13.933 8.5 12 8.5C10.067 8.5 8.5 10.067 8.5 12C8.5 13.933 10.067 15.5 12 15.5ZM19.4 15C19.2 14.55 19 14.1 18.8 13.65C18.6833 13.3833 18.7 13.05 18.8 12.8L19.9 10.9C20.1 10.55 20.05 10.1 19.85 9.75L18.85 8C18.65 7.65 18.3 7.5 17.95 7.5L15.8 7.95C15.5 8 15.2 7.9 15 7.65L13.7 6.1C13.4 5.7 12.85 5.5 12.3 5.65L10.5 6.15C10.1 6.25 9.7 6.15 9.4 5.9L7.8 4.7C7.45 4.45 6.95 4.5 6.6 4.8L5.25 6.4C4.95 6.75 4.95 7.3 5.2 7.7L6.4 9.2C6.6 9.5 6.55 9.85 6.4 10.2L5.3 12C5.1 12.4 5.15 12.85 5.4 13.2L6.45 15C6.7 15.35 7.05 15.5 7.45 15.5L9.65 15.1C9.95 15.05 10.3 15.15 10.5 15.45L11.85 17.05C12.1 17.4 12.65 17.6 13.15 17.5L14.95 17C15.3 16.9 15.65 17 15.9 17.3L17.45 18.7C17.8 19.05 18.35 19.05 18.7 18.75L20.1 17.15C20.4 16.85 20.45 16.3 20.25 15.9L19.4 15Z'
  },
  {
    id: 'log-system',
    label: '日志系统',
    iconViewBox: '0 0 24 24',
    iconPath: 'M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3ZM7 13H17V15H7V13ZM7 9H17V11H7V9ZM7 17H13V19H7V17Z'
  }
]

const toggleSettings = () => {
  settingsOpen.value = !settingsOpen.value
}

const handleLogout = () => {
  settingsOpen.value = false
  if (window.confirm('确定要退出吗？')) {
    clearAuthSession()
    router.push('/')
  }
}

const getBarWidth = (count) => {
  if (users.value.length === 0) return 0
  const maxCount = Math.max(...users.value.map(u => u.chat_count || 0))
  if (maxCount === 0) return 0
  return (count / maxCount) * 100
}

const fetchUsers = async () => {
  try {
    const { data } = await axios.get('/api/admin/users')
    users.value = data.users || []
  } catch (error) {
    console.error('获取用户列表失败', error)
  }
}

const toggleUserStatus = async (user) => {
  const newStatus = user.status === 'active' ? 'inactive' : 'active'
  try {
    await axios.patch(`/api/admin/users/${user.id}/status`, { status: newStatus })
    user.status = newStatus
  } catch (error) {
    console.error('更新用户状态失败', error)
    alert('操作失败，请重试')
  }
}

const openEditUser = (user) => {
  editForm.value = {
    id: user.id,
    username: user.username,
    nickname: user.nickname || '',
    password: ''
  }
  editModalOpen.value = true
}

const closeEditModal = () => {
  editModalOpen.value = false
}

const saveUserEdit = async () => {
  if (!editForm.value.username.trim()) {
    alert('请输入用户名')
    return
  }
  try {
    await axios.patch(`/api/admin/users/${editForm.value.id}`, {
      username: editForm.value.username,
      nickname: editForm.value.nickname,
      password: editForm.value.password || undefined
    })
    closeEditModal()
    await fetchUsers()
  } catch (error) {
    console.error('更新用户信息失败', error)
    alert('更新失败，请重试')
  }
}

// 模型配置相关函数
const modelTypeLabel = (type) => {
  const labels = {
    'llm': '大语言模型',
    'embedding': '嵌入模型',
    'both': '两者'
  }
  return labels[type] || type
}

const fetchModels = async () => {
  try {
    const { data } = await axios.get('/api/admin/models')
    models.value = data.models || []
  } catch (error) {
    console.error('获取模型列表失败', error)
  }
}

const openCreateModel = () => {
  isEditModel.value = false
  modelForm.value = {
    id: null,
    model_name: '',
    model_type: 'llm',
    api_base: '',
    api_key: '',
    api_version: '',
    model_id: '',
    description: '',
    is_active: true,
    is_default: false,
    priority: 0,
    max_tokens: null,
    temperature: null,
    top_p: null
  }
  modelModalOpen.value = true
}

const openEditModel = (model) => {
  isEditModel.value = true
  modelForm.value = {
    id: model.id,
    model_name: model.model_name,
    model_type: model.model_type,
    api_base: model.api_base,
    api_key: '', // 不填充已有的密钥，需要用户重新输入
    api_version: model.api_version || '',
    model_id: model.model_id,
    description: model.description || '',
    is_active: model.is_active,
    is_default: model.is_default,
    priority: model.priority,
    max_tokens: model.max_tokens,
    temperature: model.temperature,
    top_p: model.top_p
  }
  modelModalOpen.value = true
}

const closeModelModal = () => {
  modelModalOpen.value = false
}

const saveModel = async () => {
  if (!modelForm.value.model_name.trim() || !modelForm.value.model_id.trim() || 
      !modelForm.value.api_base.trim()) {
    alert('请填写必需字段')
    return
  }
  if (!isEditModel.value && !modelForm.value.api_key.trim()) {
    alert('请输入API密钥')
    return
  }
  try {
    if (isEditModel.value) {
      await axios.patch(`/api/admin/models/${modelForm.value.id}`, {
        ...modelForm.value,
        api_key: modelForm.value.api_key || undefined
      })
    } else {
      await axios.post('/api/admin/models', modelForm.value)
    }
    closeModelModal()
    await fetchModels()
  } catch (error) {
    console.error('保存模型配置失败', error)
    alert('保存失败，请重试')
  }
}

const setDefaultModel = async (model) => {
  if (confirm(`确定要将 "${model.model_name}" 设置为默认模型吗？`)) {
    try {
      await axios.post(`/api/admin/models/${model.id}/default`)
      await fetchModels()
    } catch (error) {
      console.error('设置默认模型失败', error)
      alert('设置失败，请重试')
    }
  }
}

const deleteModel = async (model) => {
  if (confirm(`确定要删除模型 "${model.model_name}" 吗？`)) {
    try {
      await axios.delete(`/api/admin/models/${model.id}`)
      await fetchModels()
    } catch (error) {
      console.error('删除模型失败', error)
      alert('删除失败，请重试')
    }
  }
}

// 日志系统相关函数
const loadLogs = async () => {
  logsLoading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value
    }
    if (filters.value.errorLevel) {
      params.error_level = filters.value.errorLevel
    }
    if (filters.value.startDate) {
      params.start_date = filters.value.startDate
    }
    if (filters.value.endDate) {
      params.end_date = filters.value.endDate
    }
    const { data } = await axios.get('/api/admin/error-logs', { params })
    logs.value = data.logs || []
    total.value = data.total || 0
  } catch (error) {
    console.error('获取日志列表失败', error)
  } finally {
    logsLoading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    errorLevel: '',
    startDate: '',
    endDate: ''
  }
  page.value = 1
  loadLogs()
}

const prevPage = () => {
  if (page.value > 1) {
    page.value--
    loadLogs()
  }
}

const totalPages = computed(() => {
  return Math.ceil(total.value / pageSize.value)
})

const nextPage = () => {
  if (page.value < totalPages.value) {
    page.value++
    loadLogs()
  }
}

const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedLogs.value = logs.value.map(log => log.id)
  } else {
    selectedLogs.value = []
  }
}

const viewLogDetail = (log) => {
  currentLog.value = log
  logDetailModalOpen.value = true
}

const closeLogDetailModal = () => {
  logDetailModalOpen.value = false
  currentLog.value = null
}

const deleteLog = async (log) => {
  if (confirm(`确定要删除该条日志吗？`)) {
    try {
      await axios.delete(`/api/admin/error-logs/${log.id}`)
      await loadLogs()
    } catch (error) {
      console.error('删除日志失败', error)
      alert('删除失败，请重试')
    }
  }
}

const batchDeleteLogs = async () => {
  if (selectedLogs.value.length === 0) {
    alert('请选择要删除的日志')
    return
  }
  if (confirm(`确定要删除选中的 ${selectedLogs.value.length} 条日志吗？`)) {
    try {
      await axios.delete('/api/admin/error-logs/batch', {
        data: { log_ids: selectedLogs.value }
      })
      selectedLogs.value = []
      selectAll.value = false
      await loadLogs()
    } catch (error) {
      console.error('批量删除日志失败', error)
      alert('删除失败，请重试')
    }
  }
}

const truncateMessage = (message, maxLength) => {
  if (!message) return '-'
  if (message.length <= maxLength) return message
  return message.substring(0, maxLength) + '...'
}

// 监听菜单切换
const handleMenuChange = (menuId) => {
  activeMenu.value = menuId
  if (menuId === 'user-management') {
    fetchUsers()
  } else if (menuId === 'system-config') {
    fetchModels()
  } else if (menuId === 'log-system') {
    loadLogs()
  }
}

onMounted(() => {
  if (activeMenu.value === 'user-management') {
    fetchUsers()
  } else if (activeMenu.value === 'system-config') {
    fetchModels()
  } else if (activeMenu.value === 'log-system') {
    loadLogs()
  }
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-profile-dropdown')) {
      settingsOpen.value = false
    }
  })
})
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background-color: #f8fafc;
}

.admin-layout {
  display: flex;
  min-height: 100vh;
}

/* 左侧菜单栏 */
.admin-sidebar {
  width: 240px;
  background-color: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.sidebar-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.sidebar-nav {
  padding: 16px 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.nav-item svg {
  width: 20px;
  height: 20px;
}

.nav-item:hover {
  background-color: #f1f5f9;
  color: #334155;
}

.nav-item.active {
  background-color: #eef2ff;
  color: #6366f1;
}

/* 右侧内容区 */
.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.admin-header {
  background-color: white;
  padding: 24px 32px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h1 {
  margin: 0 0 6px 0;
  font-size: 24px;
  color: #1e293b;
}

.subtitle {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-profile-dropdown {
  position: relative;
}

.user-profile-mini {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 12px;
  transition: 0.2s ease;
}

.user-profile-mini:hover {
  background-color: #f1f5f9;
}

.user-profile-mini .avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  display: grid;
  place-items: center;
  font-size: 18px;
  font-weight: 700;
}

.user-profile-mini .info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.user-profile-mini .info strong {
  font-size: 14px;
  color: #1e293b;
}

.user-profile-mini .info span {
  font-size: 12px;
  color: #64748b;
}

.dropdown-arrow {
  width: 16px;
  height: 16px;
  color: #64748b;
  transition: 0.2s ease;
}

.user-profile-dropdown.open .dropdown-arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  min-width: 200px;
  padding: 8px;
  z-index: 1000;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.2s ease;
  color: #1e293b;
  font-size: 14px;
}

.dropdown-item:hover {
  background-color: #f1f5f9;
}

.dropdown-item svg {
  width: 18px;
  height: 18px;
}

.admin-content {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
}

.menu-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.content-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1e293b;
}

.content-header .header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 14px;
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.model-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  gap: 16px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.model-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.model-title {
  flex: 1;
}

.model-title h4 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: #1e293b;
}

.model-id {
  font-size: 13px;
  color: #64748b;
  font-family: monospace;
}

.model-badges {
  display: flex;
  gap: 8px;
}

.badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.badge.active {
  background: #dcfce7;
  color: #166534;
}

.badge.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.badge.default {
  background: #dbeafe;
  color: #1d4ed8;
}

.model-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.model-info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #1e293b;
  word-break: break-all;
}

.model-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.model-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #64748b;
}

.model-actions {
  display: flex;
  gap: 8px;
}

.btn-danger {
  color: #dc2626;
}

.btn-danger:hover {
  background: #fee2e2;
}

/* 弹窗样式 */
.modal-large .modal-content {
  max-width: 700px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
}

.checkbox-group label {
  margin-bottom: 0;
}

.required {
  color: #dc2626;
}

.surface-panel {
  background-color: white;
  border-radius: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  padding: 32px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  color: #6366f1;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #1e293b;
}

.empty-state p {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}

/* 用户管理页面 */
.user-management {
  height: 100%;
}

.user-management-layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: calc(100vh - 200px);
}

.user-usage-section,
.user-status-section {
  background-color: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.user-usage-section h3,
.user-status-section h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #1e293b;
}

.usage-chart-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.usage-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info .username {
  font-weight: 600;
  color: #1e293b;
}

.user-info .chat-count {
  color: #64748b;
  font-size: 14px;
}

.bar-container {
  height: 12px;
  background-color: #f1f5f9;
  border-radius: 6px;
  overflow: hidden;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 6px;
  transition: width 0.3s ease;
}

.user-list-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-radius: 12px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.user-item:hover {
  border-color: #cbd5e1;
  background-color: #f1f5f9;
}

.user-basic-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-small {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  display: grid;
  place-items: center;
  font-size: 16px;
  font-weight: 700;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-details .name {
  font-weight: 600;
  color: #1e293b;
}

.user-details .username-text {
  color: #64748b;
  font-size: 13px;
}

.user-status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.user-status-badge.active {
  background-color: #dcfce7;
  color: #166534;
}

.user-status-badge.inactive {
  background-color: #fee2e2;
  color: #991b1b;
}

.user-actions {
  display: flex;
  gap: 12px;
}

.btn-action {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background-color: white;
  color: #1e293b;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-action:hover {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
}

.btn-action.btn-edit {
  background-color: #6366f1;
  color: white;
  border-color: #6366f1;
}

.btn-action.btn-edit:hover {
  background-color: #4f46e5;
  border-color: #4f46e5;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-content {
  background-color: white;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background-color: #f1f5f9;
  border-radius: 50%;
  cursor: pointer;
  font-size: 20px;
  color: #64748b;
  display: grid;
  place-items: center;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background-color: #e2e8f0;
  color: #1e293b;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #1e293b;
}

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #6366f1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
}

.btn-secondary,
.btn-primary {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary {
  background-color: #f1f5f9;
  color: #1e293b;
}

.btn-secondary:hover {
  background-color: #e2e8f0;
}

.btn-primary {
  background-color: #6366f1;
  color: white;
}

.btn-primary:hover {
  background-color: #4f46e5;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-danger {
  background-color: #ef4444;
  color: white;
}

.btn-danger:hover {
  background-color: #dc2626;
}

.btn-action {
  background-color: #f1f5f9;
  color: #1e293b;
  border: 1px solid #e2e8f0;
}

.btn-action:hover {
  background-color: #e2e8f0;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-section {
  margin-bottom: 24px;
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item label {
  font-size: 13px;
  font-weight: 500;
  color: #475569;
}

.filter-item select,
.filter-item input[type="date"] {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  background-color: white;
  min-width: 150px;
}

.logs-table-container {
  overflow: hidden;
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
}

.logs-table thead {
  background-color: #f8fafc;
}

.logs-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
}

.logs-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  font-size: 14px;
  color: #334155;
}

.log-row {
  transition: background-color 0.2s ease;
}

.log-row:hover {
  background-color: #f8fafc;
}

.log-row.log-error {
  background-color: #fef2f2;
}

.log-row.log-warning {
  background-color: #fffbeb;
}

.log-row.log-critical {
  background-color: #fef2f2;
  border-left: 3px solid #dc2626;
}

.log-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.badge-error {
  background-color: #fee2e2;
  color: #dc2626;
}

.badge-warning {
  background-color: #fef3c7;
  color: #d97706;
}

.badge-critical {
  background-color: #fee2e2;
  color: #b91c1c;
}

.log-message {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-table {
  text-align: center;
  color: #94a3b8;
  padding: 48px 16px !important;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-top: 1px solid #e2e8f0;
}

.page-info {
  color: #64748b;
  font-size: 14px;
}

.log-detail-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.log-detail-row {
  display: flex;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.log-detail-label {
  font-weight: 600;
  color: #475569;
  min-width: 100px;
}

.log-detail-value {
  flex: 1;
  color: #1e293b;
  word-break: break-word;
}

.log-detail-message {
  font-family: monospace;
  background-color: #f8fafc;
  padding: 8px 12px;
  border-radius: 6px;
}

.log-detail-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.stack-trace {
  background-color: #1e293b;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
