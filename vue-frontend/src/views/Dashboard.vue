<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <div class="header-left">
        <h1>欢迎回来，{{ authUser.nickname || authUser.username }}！</h1>
        <p class="subtitle">今天也要高效学习，持续进步～</p>
      </div>
      <div class="header-right">
        <div class="user-profile-dropdown" :class="{ open: settingsOpen }">
          <div class="user-profile-mini" @click="toggleSettings">
            <div class="avatar">{{ (authUser.nickname || authUser.username || '学')[0] }}</div>
            <div class="info">
              <strong>{{ authUser.nickname || authUser.username }}</strong>
              <span>个人账号</span>
            </div>
            <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="dropdown-menu" v-if="settingsOpen">
            <div class="dropdown-item" @click="openSettingsModal">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 15.5C13.933 15.5 15.5 13.933 15.5 12C15.5 10.067 13.933 8.5 12 8.5C10.067 8.5 8.5 10.067 8.5 12C8.5 13.933 10.067 15.5 12 15.5Z" fill="currentColor"/>
                <path d="M19.4 15C19.2 14.55 19 14.1 18.8 13.65C18.6833 13.3833 18.7 13.05 18.8 12.8L19.9 10.9C20.1 10.55 20.05 10.1 19.85 9.75L18.85 8C18.65 7.65 18.3 7.5 17.95 7.5L15.8 7.95C15.5 8 15.2 7.9 15 7.65L13.7 6.1C13.4 5.7 12.85 5.5 12.3 5.65L10.5 6.15C10.1 6.25 9.7 6.15 9.4 5.9L7.8 4.7C7.45 4.45 6.95 4.5 6.6 4.8L5.25 6.4C4.95 6.75 4.95 7.3 5.2 7.7L6.4 9.2C6.6 9.5 6.55 9.85 6.4 10.2L5.3 12C5.1 12.4 5.15 12.85 5.4 13.2L6.45 15C6.7 15.35 7.05 15.5 7.45 15.5L9.65 15.1C9.95 15.05 10.3 15.15 10.5 15.45L11.85 17.05C12.1 17.4 12.65 17.6 13.15 17.5L14.95 17C15.3 16.9 15.65 17 15.9 17.3L17.45 18.7C17.8 19.05 18.35 19.05 18.7 18.75L20.1 17.15C20.4 16.85 20.45 16.3 20.25 15.9L19.4 15Z" fill="currentColor"/>
              </svg>
              账号设置
            </div>
            <div class="dropdown-divider"></div>
            <div class="dropdown-item danger" @click="handleLogout">
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

    <div class="dashboard-content">
      <!-- 知识空间管理 - 最顶层 -->
      <div class="knowledge-section surface-panel" style="margin-bottom: 24px;">
        <div class="section-header">
          <h2>知识空间管理</h2>
          <button class="btn btn-primary" @click="openKnowledgeModal()" style="white-space: nowrap;">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 16px; height: 16px;">
              <path d="M12 5V19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            新建空间
          </button>
        </div>

        <!-- 横向滚动容器 -->
        <div class="knowledge-scroll-container">
          <div class="knowledge-scroll-wrapper">
            <div
              v-for="kb in knowledgeBases"
              :key="kb.id"
              class="knowledge-card-horizontal"
              @click="enterKnowledgeBase(kb)"
            >
              <div class="card-background-overlay"></div>
              <div class="card-content">
                <div class="card-header">
                  <div class="card-title">
                    <h3>{{ kb.name }}</h3>
                    <span class="category-tag">{{ kb.category || '通用' }}</span>
                  </div>
                  <div class="card-actions">
                    <button class="btn btn-secondary compact-btn" type="button" @click.stop="openKnowledgeModal(kb)">
                      编辑
                    </button>
                    <button class="btn btn-secondary compact-btn" type="button" @click.stop="confirmDeleteKnowledgeBase(kb)" style="color: var(--danger);">
                      删除
                    </button>
                  </div>
                </div>
                <p class="card-description">{{ kb.description || '暂无描述' }}</p>
                <div class="card-footer">
                  <div class="persona-tag" v-if="kb.persona">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 12px; height: 12px;">
                      <path d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12Z" fill="currentColor"/>
                      <path d="M12 14C9.33 14 4 15.34 4 18V20H20V18C20 15.34 14.67 14 12 14Z" fill="currentColor"/>
                    </svg>
                    已设置人格
                  </div>
                  <div class="thinking-style-tag" v-if="kb.thinking_style && kb.thinking_style !== 'teaching'">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 12px; height: 12px;">
                      <path d="M15 3H9V5H15V3Z" fill="currentColor"/>
                      <path d="M17 7H7V21H17V7Z" fill="currentColor"/>
                      <path d="M12 9H15V12H12V9Z" fill="currentColor"/>
                    </svg>
                    {{ getThinkingStyleLabel(kb.thinking_style) }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="knowledgeBases.length === 0" class="empty-horizontal-state">
              <div class="empty-icon" style="width: 60px; height: 60px;">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: 100%; color: var(--primary);">
                  <path d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3Z" fill="currentColor" opacity="0.3"/>
                  <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" fill="currentColor" opacity="0.6"/>
                </svg>
              </div>
              <h3>还没有知识空间</h3>
              <p>创建你的第一个知识空间，开始高效学习！</p>
              <button class="btn btn-primary" @click="openKnowledgeModal()">创建第一个空间</button>
            </div>
          </div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-content">
            <strong>{{ knowledgeBases.length }}</strong>
            <span>知识空间</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-content">
            <strong>{{ stats.overall?.doc_count || 0 }}</strong>
            <span>文档总数</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-content">
            <strong>{{ stats.overall?.qa_count || 0 }}</strong>
            <span>对话轮次</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-content">
            <strong>{{ stats.workspace?.learning_streak_days || 0 }}</strong>
            <span>连续学习</span>
          </div>
        </div>
      </div>

      <div class="dashboard-grid">
        <div class="panel-card surface-panel">
          <div class="panel-card-header">
            <div>
              <span class="section-label">常用空间</span>
              <h3>最近使用的知识空间</h3>
            </div>
          </div>
          <div class="activity-list">
            <div v-for="(kb, index) in recentKnowledgeBases?.slice(0, 4) || []" :key="index" class="activity-item" @click="enterKnowledgeBase(kb)" style="cursor: pointer;">
              <strong>{{ kb.name }}</strong>
              <p>{{ kb.description || '暂无描述' }}</p>
            </div>
            <div v-if="!recentKnowledgeBases?.length" class="empty-text">暂无最近使用的知识空间</div>
          </div>
        </div>

        <div class="panel-card surface-panel">
          <div class="panel-card-header">
            <div>
              <span class="section-label">使用统计</span>
              <h3>知识空间使用情况</h3>
            </div>
            <span class="soft-badge">今日提问 {{ stats.today?.qa_count || 0 }}</span>
          </div>
          <div class="trend-chart">
            <div v-for="(item, index) in knowledgeSpaceUsage.slice(0, 4)" :key="index" class="trend-bar">
              <div class="trend-bar-value" :style="{ height: item.percentage + '%' }"></div>
              <span>{{ item.name }}</span>
            </div>
            <div v-if="knowledgeSpaceUsage.length === 0" class="empty-text">暂无使用数据</div>
          </div>
        </div>
      </div>




    </div>

    <div v-if="knowledgeModal.visible" class="overlay-shell">
      <div class="overlay-card surface-panel modal-card large-modal">
        <div class="panel-header">
          <div>
            <span class="section-label">{{ knowledgeModal.mode === 'create' ? '新建主题' : '编辑主题' }}</span>
            <h2>{{ knowledgeModal.mode === 'create' ? '创建知识空间' : '编辑知识空间' }}</h2>
          </div>
          <button class="modal-close" type="button" @click="closeKnowledgeModal">关闭</button>
        </div>
        <form class="modal-form" @submit.prevent="submitKnowledgeBase">
          <div class="modal-grid">
            <div>
              <label class="field-label">名称</label>
              <input v-model="knowledgeModal.form.name" class="field-input" type="text" placeholder="例如：毕业设计" />
            </div>
            <div>
              <label class="field-label">分类</label>
              <input v-model="knowledgeModal.form.category" class="field-input" type="text" placeholder="例如：项目研究" />
            </div>
          </div>
          <div>
            <label class="field-label">描述</label>
            <textarea v-model="knowledgeModal.form.description" class="field-textarea" placeholder="描述这个知识空间的内容边界"></textarea>
          </div>
          <div>
            <label class="field-label">标签（Tags）</label>
            <input v-model="knowledgeModal.form.tags" class="field-input" type="text" placeholder="例如：计算机科学, 机器学习（用逗号分隔）" />
          </div>
          <div>
            <label class="field-label">检索模式（Retrieval Mode）</label>
            <select v-model="knowledgeModal.form.retrieval_mode" class="field-select">
              <option value="hybrid">混合检索（默认）</option>
              <option value="vector">向量检索</option>
              <option value="keyword">关键词检索</option>
            </select>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="closeKnowledgeModal">取消</button>
            <button class="btn btn-primary" type="submit" :disabled="loading">
              {{ loading ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="settingsModal.visible" class="overlay-shell">
      <div class="overlay-card surface-panel modal-card">
        <div class="panel-header">
          <div>
            <span class="section-label">系统设置</span>
            <h2>系统和用户相关设置</h2>
          </div>
          <button class="modal-close" type="button" @click="closeSettingsModal">关闭</button>
        </div>
        <form class="modal-form">
          <div class="setting-item">
            <label class="field-label">账号信息修改</label>
            <div class="form-group">
              <input v-model="settingsForm.username" class="field-input" type="text" placeholder="用户名" />
            </div>
            <div class="form-group">
              <input v-model="settingsForm.nickname" class="field-input" type="text" placeholder="昵称" />
            </div>
          </div>
          <div class="setting-item">
            <label class="field-label">主题设置</label>
            <select class="field-select" v-model="settingsForm.theme">
              <option value="light">浅色模式（当前）</option>
              <option value="dark">深色模式（开发中）</option>
              <option value="system">跟随系统</option>
            </select>
          </div>
          <div class="setting-item">
            <label class="field-label">语言切换</label>
            <select class="field-select" v-model="settingsForm.language">
              <option value="zh-CN">中文</option>
              <option value="en">English</option>
            </select>
          </div>
          <div class="setting-item">
            <label class="field-label">修改密码</label>
            <div class="form-group">
              <input v-model="passwordForm.oldPassword" class="field-input" type="password" placeholder="旧密码" />
            </div>
            <div class="form-group">
              <input v-model="passwordForm.newPassword" class="field-input" type="password" placeholder="新密码" />
            </div>
            <div class="form-group">
              <input v-model="passwordForm.confirmPassword" class="field-input" type="password" placeholder="确认新密码" />
            </div>
            <button class="btn btn-primary" type="button" @click="changePassword" style="margin-top: 8px;">修改密码</button>
          </div>
          <div class="setting-item">
            <label class="field-label">危险操作</label>
            <div style="color: #ef4444; font-size: 14px; margin-bottom: 12px;">
              ⚠️ 注销账号后，所有数据将被永久删除，无法恢复！
            </div>
            <button class="btn" type="button" @click="showDeleteConfirm" style="background: #ef4444; color: white; border: none;">
              注销账号
            </button>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="closeSettingsModal">取消</button>
            <button class="btn btn-primary" type="button" @click="saveSettings">保存修改</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- 注销账号确认对话框 -->
  <div v-if="deleteConfirmModal.visible" class="overlay-shell" @click.self="cancelDeleteConfirm">
    <div class="overlay-card surface-panel modal-card" style="max-width: 500px;">
      <div class="panel-header">
        <div>
          <h2>注销账号</h2>
        </div>
        <button class="modal-close" type="button" @click="cancelDeleteConfirm">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 20px; height: 20px;">
            <path d="M6 18L18 6M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      <div class="modal-form">
        <div v-if="!deleteConfirmModal.step2">
          <p style="margin-bottom: 16px; line-height: 1.6;">
            ⚠️ 此操作将永久删除您的账号及所有相关数据，包括：
          </p>
          <ul style="margin-bottom: 16px; padding-left: 20px;">
            <li>所有知识空间</li>
            <li>所有上传的文档</li>
            <li>所有对话记录</li>
            <li>个人信息</li>
          </ul>
          <p style="margin-bottom: 24px; color: #ef4444; font-weight: 500;">
            此操作不可撤销，请谨慎考虑！
          </p>
          <div class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="cancelDeleteConfirm">取消</button>
            <button class="btn" type="button" @click="confirmDeleteStep1" style="background: #ef4444; color: white; border: none;">
              确认继续
            </button>
          </div>
        </div>
        <div v-else>
          <p style="margin-bottom: 12px; color: #ef4444;">
            ⏱️ 请等待 <strong>{{ deleteConfirmModal.countdown }}</strong> 秒后再继续
          </p>
          <p style="margin-bottom: 16px;">
            请输入 <strong>"确认注销"</strong> 以确认此操作
          </p>
          <input
            v-model="deleteConfirmModal.confirmText"
            class="field-input"
            type="text"
            placeholder="请输入确认文字"
            :disabled="deleteConfirmModal.countdown > 0"
          />
          <div class="modal-actions" style="margin-top: 24px;">
            <button class="btn btn-secondary" type="button" @click="cancelDeleteConfirm">取消</button>
            <button
              class="btn"
              type="button"
              @click="confirmDeleteAccount"
              :disabled="deleteConfirmModal.countdown > 0 || deleteConfirmModal.confirmText !== '确认注销'"
              :style="{
                background: (deleteConfirmModal.countdown > 0 || deleteConfirmModal.confirmText !== '确认注销') ? '#9ca3af' : '#ef4444',
                color: 'white',
                border: 'none',
                cursor: (deleteConfirmModal.countdown > 0 || deleteConfirmModal.confirmText !== '确认注销') ? 'not-allowed' : 'pointer'
              }"
            >
              永久注销
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { reactive, ref, onMounted, onActivated, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getAuthUser, clearAuthSession } from '../utils/auth'

// 设置组件名称，让keep-alive能识别
defineOptions({
  name: 'Dashboard'
})

const router = useRouter()
const authUser = getAuthUser()

const knowledgeBases = ref([])
const loading = ref(false)
const settingsOpen = ref(false)

// 最近使用的知识空间
const recentKnowledgeBases = computed(() => {
  if (!knowledgeBases.value.length) return []
  return knowledgeBases.value.slice(0, 4).map(kb => ({
    ...kb,
    lastUsed: new Date()
  }))
})

// 知识空间使用情况
const knowledgeSpaceUsage = computed(() => {
  if (!knowledgeBases.value.length) return []
  const totalCount = Math.max(...knowledgeBases.value.map((_, i) => i + 1), 1)
  return knowledgeBases.value.slice(0, 4).map((kb, index) => ({
    id: kb.id,
    name: kb.name,
    count: Math.floor(Math.random() * 100) + 10,
    percentage: ((index + 1) / totalCount) * 100
  }))
})



const stats = reactive({
  overall: { doc_count: 0, qa_count: 0 },
  workspace: { learning_streak_days: 0 },
  recent_qa: [],
  today: { qa_count: 0 },
  daily_activity: []
})

const trendData = computed(() => {
  if (!stats.daily_activity?.length) {
    const days = ['一', '二', '三', '四', '五', '六', '日']
    return days.map(day => ({
      label: '周' + day,
      height: 0
    }))
  }
  const maxQuestions = Math.max(...stats.daily_activity.map(d => d.questions || 0), 1)
  return stats.daily_activity.slice(0, 7).map((d, i) => ({
    label: d.date?.slice(5) || `第${i + 1}天`,
    height: ((d.questions || 0) / maxQuestions) * 100
  }))
})

const knowledgeModal = reactive({
  visible: false,
  mode: 'create',
  form: {
    id: '',
    name: '',
    description: '',
    category: '通用学习',
    tags: '',
    retrieval_mode: 'hybrid',
    persona: '',
    thinking_style: 'teaching',
    task_policy: [],
    model_strategy: ''
  }
})

const settingsModal = reactive({
  visible: false
})

// 注销账号确认模态框
const deleteConfirmModal = reactive({
  visible: false,
  step2: false,
  countdown: 10,
  confirmText: '',
  countdownTimer: null
})

const settingsForm = reactive({
  username: authUser?.username || '',
  nickname: authUser?.nickname || '',
  theme: 'light',
  language: 'zh-CN'
})

// 密码修改表单
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const getThinkingStyleLabel = (style) => {
  const styleMap = {
    teaching: '教学型',
    interview: '面试型',
    summary: '总结型',
    reasoning: '推理型'
  }
  return styleMap[style] || '教学型'
}

const toggleSettings = () => {
  settingsOpen.value = !settingsOpen.value
}

const openSettingsModal = () => {
  settingsModal.visible = true
  settingsOpen.value = false
  settingsForm.username = authUser?.username || ''
  settingsForm.nickname = authUser?.nickname || ''
}

const closeSettingsModal = () => {
  settingsModal.visible = false
}

const saveSettings = async () => {
  try {
    await axios.post('/api/user/update', {
      username: settingsForm.username,
      nickname: settingsForm.nickname
    })
    authUser.nickname = settingsForm.nickname
    authUser.username = settingsForm.username
    closeSettingsModal()
  } catch (error) {
    console.error('保存设置失败', error)
  }
}

// 修改密码
const changePassword = async () => {
  if (!passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    alert('请填写所有密码字段')
    return
  }
  
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    alert('新密码和确认密码不一致')
    return
  }
  
  try {
    await axios.put('/api/user/password', {
      oldPassword: passwordForm.oldPassword,
      newPassword: passwordForm.newPassword
    })
    alert('密码修改成功')
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (error) {
    console.error('修改密码失败', error)
    alert('修改密码失败：' + error.response?.data?.message || '未知错误')
  }
}

// 注销账号相关函数
const showDeleteConfirm = () => {
  deleteConfirmModal.visible = true
  deleteConfirmModal.step2 = false
  deleteConfirmModal.countdown = 10
  deleteConfirmModal.confirmText = ''
  if (deleteConfirmModal.countdownTimer) {
    clearInterval(deleteConfirmModal.countdownTimer)
  }
}

const cancelDeleteConfirm = () => {
  deleteConfirmModal.visible = false
  deleteConfirmModal.step2 = false
  deleteConfirmModal.countdown = 10
  deleteConfirmModal.confirmText = ''
  if (deleteConfirmModal.countdownTimer) {
    clearInterval(deleteConfirmModal.countdownTimer)
  }
}

const confirmDeleteStep1 = () => {
  deleteConfirmModal.step2 = true
  deleteConfirmModal.countdown = 10
  
  // 开始倒计时
  deleteConfirmModal.countdownTimer = setInterval(() => {
    if (deleteConfirmModal.countdown > 0) {
      deleteConfirmModal.countdown--
    } else {
      if (deleteConfirmModal.countdownTimer) {
        clearInterval(deleteConfirmModal.countdownTimer)
      }
    }
  }, 1000)
}

const confirmDeleteAccount = async () => {
  try {
    await axios.delete('/api/user/account')
    alert('账号已成功注销')
    clearAuthSession()
    router.push('/login')
  } catch (error) {
    console.error('注销账号失败', error)
    alert('注销账号失败：' + error.response?.data?.message || '未知错误')
  }
}

const loadKnowledgeBases = async () => {
  try {
    const { data } = await axios.get('/api/knowledge/list')
    knowledgeBases.value = data
  } catch (error) {
    console.error('加载知识空间失败', error)
  }
}

const loadDashboard = async () => {
  try {
    // 使用与Main页面相同的API
    const { data } = await axios.get('/api/workspace/dashboard')
    Object.assign(stats, data)
  } catch (error) {
    console.error('加载工作台数据失败', error)
    // 保留原有数据，避免闪烁
  }
}

const openKnowledgeModal = (item = null) => {
  knowledgeModal.visible = true
  knowledgeModal.mode = item ? 'edit' : 'create'
  knowledgeModal.form.id = item?.id || ''
  knowledgeModal.form.name = item?.name || ''
  knowledgeModal.form.description = item?.description || ''
  knowledgeModal.form.category = item?.category || '通用学习'
  knowledgeModal.form.tags = (item?.tags || []).join(', ')
  knowledgeModal.form.retrieval_mode = item?.retrieval_mode || 'hybrid'
  knowledgeModal.form.persona = item?.persona || ''
  knowledgeModal.form.thinking_style = item?.thinking_style || 'teaching'
  knowledgeModal.form.task_policy = item?.task_policy || []
  knowledgeModal.form.model_strategy = item?.model_strategy || ''
}

const closeKnowledgeModal = () => {
  knowledgeModal.visible = false
}

const submitKnowledgeBase = async () => {
  if (!knowledgeModal.form.name.trim()) {
    return
  }

  loading.value = true
  try {
    const payload = {
      id: knowledgeModal.form.id,
      name: knowledgeModal.form.name.trim(),
      description: knowledgeModal.form.description.trim(),
      category: knowledgeModal.form.category.trim(),
      tags: knowledgeModal.form.tags,
      retrieval_mode: knowledgeModal.form.retrieval_mode,
      persona: knowledgeModal.form.persona,
      thinking_style: knowledgeModal.form.thinking_style,
      task_policy: knowledgeModal.form.task_policy,
      model_strategy: knowledgeModal.form.model_strategy
    }

    const { data } = knowledgeModal.mode === 'create'
      ? await axios.post('/api/knowledge/create', payload)
      : await axios.put('/api/knowledge/update', payload)

    closeKnowledgeModal()
    await loadKnowledgeBases()
  } catch (error) {
    console.error('保存知识空间失败', error)
  } finally {
    loading.value = false
  }
}

const confirmDeleteKnowledgeBase = (item) => {
  if (!window.confirm(`确认删除知识空间“${item.name}”吗？`)) return
  deleteKnowledgeBase(item)
}

const deleteKnowledgeBase = async (item) => {
  try {
    await axios.delete(`/api/knowledge/delete/${item.id}`)
    await loadKnowledgeBases()
  } catch (error) {
    console.error('删除知识空间失败', error)
  }
}

const enterKnowledgeBase = (kb) => {
  router.push({
    path: '/main',
    query: { knowledgeId: kb.id }
  })
}

const handleLogout = () => {
  settingsOpen.value = false
  if (window.confirm('确定要退出吗？')) {
    clearAuthSession()
    router.push('/')
  }
}

document.addEventListener('click', (e) => {
  if (!e.target.closest('.user-profile-dropdown')) {
    settingsOpen.value = false
  }
})

onMounted(() => {
  // 第一次加载时获取数据
  loadKnowledgeBases()
  loadDashboard()
})

onActivated(() => {
  // 页面被激活时，只刷新后台数据，保持现有显示
  // 不重置现有数据，避免闪烁
  Promise.all([
    loadKnowledgeBases(),
    loadDashboard()
  ])
})
</script>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  background: white;
  padding: 24px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: white;
  border-radius: 24px;
  box-shadow: var(--shadow-card);
}

.header-left h1 {
  margin: 0 0 8px;
  font-size: 32px;
  color: var(--text-primary);
}

.subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
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
  border-radius: 16px;
  transition: 0.2s ease;
}

.user-profile-mini:hover {
  background: rgba(15, 23, 42, 0.05);
}

.user-profile-mini .avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #e8eefc;
  color: var(--primary-strong);
  display: grid;
  place-items: center;
  font-size: 20px;
  font-weight: 700;
}

.user-profile-mini .info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-profile-mini .info strong {
  font-size: 15px;
  color: var(--text-primary);
}

.user-profile-mini .info span {
  font-size: 13px;
  color: var(--text-secondary);
}

.dropdown-arrow {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
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
  border-radius: 16px;
  box-shadow: var(--shadow-float);
  min-width: 220px;
  padding: 8px;
  z-index: 1000;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: 0.2s ease;
  color: var(--text-primary);
  font-size: 14px;
}

.dropdown-item:hover {
  background: rgba(15, 23, 42, 0.05);
}

.dropdown-item.danger {
  color: var(--danger);
}

.dropdown-item.danger:hover {
  background: rgba(220, 38, 38, 0.08);
}

.dropdown-item svg {
  width: 18px;
  height: 18px;
}

.dropdown-divider {
  height: 1px;
  background: var(--line-soft);
  margin: 4px 0;
}

.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: #fafafa;
  border: 1px solid var(--line-soft);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  gap: 16px;
  align-items: center;
  transition: 0.2s ease;
}

.stat-card:hover {
  background: #f3f4f6;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: grid;
  place-items: center;
}

.stat-icon.knowledge {
  background: rgba(123, 125, 243, 0.12);
  color: var(--primary);
}

.stat-icon.document {
  background: rgba(76, 175, 80, 0.12);
  color: #4caf50;
}

.stat-icon.chat {
  background: rgba(255, 152, 0, 0.12);
  color: #ff9800;
}

.stat-icon.streak {
  background: rgba(233, 30, 99, 0.12);
  color: #e91e63;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-content strong {
  font-size: 24px;
  color: var(--text-primary);
}

.stat-content span {
  font-size: 13px;
  color: var(--text-secondary);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.panel-card {
  padding: 24px;
  border-radius: 24px;
}

.panel-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.section-label {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  background: #eef2ff;
  color: var(--primary-strong);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-card-header h3 {
  margin: 10px 0 0;
  font-size: 22px;
  color: var(--text-primary);
}

.soft-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: #f3f4f6;
  color: var(--text-secondary);
  font-size: 13px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  padding: 14px;
  border-radius: 16px;
  background: #fafafa;
  transition: 0.2s ease;
}

.activity-item:hover {
  background: #f3f4f6;
}

.activity-item strong {
  display: block;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-item p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  height: 200px;
  padding: 20px 0 10px;
}

.trend-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.trend-bar-value {
  width: 100%;
  max-width: 48px;
  background: linear-gradient(180deg, var(--primary) 0%, var(--primary-strong) 100%);
  border-radius: 12px;
  min-height: 8px;
  transition: 0.3s ease;
}

.trend-bar span {
  font-size: 12px;
  color: var(--text-secondary);
}

.empty-text {
  color: var(--text-muted);
  font-size: 14px;
  text-align: center;
  padding: 30px;
}



.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-header h2 {
  margin: 0;
  font-size: 24px;
  color: var(--text-primary);
}

.knowledge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.knowledge-card {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  background: #fafafa;
  border: 1px solid var(--line-soft);
  cursor: pointer;
  transition: 0.2s ease;
  min-height: 220px;
}

.knowledge-card:hover {
  background: #f3f4f6;
}

.card-background-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(248, 249, 255, 0.96) 0%, rgba(248, 249, 255, 0.88) 100%);
  z-index: 1;
}

.card-content {
  position: relative;
  z-index: 2;
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.card-title {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-title h3 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.category-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(123, 125, 243, 0.12);
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  width: fit-content;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
  flex: 1;
}

.card-footer {
  margin-top: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.persona-tag,
.thinking-style-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(123, 125, 243, 0.12);
  color: var(--primary);
  font-size: 12px;
  font-weight: 500;
}

.persona-tag svg,
.thinking-style-tag svg {
  width: 14px;
  height: 14px;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 24px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  display: grid;
  place-items: center;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
  color: var(--primary);
}

.empty-state h3 {
  margin: 0 0 12px;
  font-size: 22px;
  color: var(--text-primary);
}

.empty-state p {
  margin: 0 0 24px;
  color: var(--text-secondary);
  font-size: 15px;
}

.overlay-shell {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.22);
  z-index: 100;
}

.modal-card {
  width: min(720px, 100%);
  padding: 24px;
  background: white;
  border-radius: 24px;
  box-shadow: var(--shadow-float);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.panel-header h2 {
  margin: 12px 0 0;
  font-size: 26px;
  color: var(--text-primary);
}

.modal-close {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: none;
  background: rgba(129, 142, 186, 0.12);
  color: var(--text-secondary);
  cursor: pointer;
  display: grid;
  place-items: center;
  transition: 0.2s ease;
}

.modal-close:hover {
  background: rgba(129, 142, 186, 0.2);
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.modal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.field-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.field-input,
.field-textarea,
.field-select {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--line-soft);
  border-radius: 16px;
  font-size: 14px;
  background: white;
  color: var(--text-primary);
  transition: 0.2s ease;
}

.field-input:focus,
.field-textarea:focus,
.field-select:focus {
  outline: none;
  border-color: rgba(37, 99, 235, 0.36);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.field-textarea {
  min-height: 80px;
  resize: vertical;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 18px;
  border-radius: 12px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn:hover {
  opacity: 0.9;
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-secondary {
  background: white;
  color: var(--text-primary);
  border: 1px solid var(--line-soft);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.compact-btn {
  min-height: 40px;
  padding: 0 16px;
  font-size: 14px;
}

.visually-hidden {
  display: none;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

/* 横向滚动容器样式 */
.knowledge-scroll-container {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 8px;
}

.knowledge-scroll-container::-webkit-scrollbar {
  height: 6px;
}

.knowledge-scroll-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.knowledge-scroll-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.knowledge-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

.knowledge-scroll-wrapper {
  display: flex;
  gap: 20px;
  min-width: min-content;
  padding: 4px;
}

.knowledge-card-horizontal {
  flex: 0 0 340px;
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  background: #fafafa;
  border: 1px solid var(--line-soft);
  cursor: pointer;
  transition: 0.2s ease;
  min-height: 220px;
}

.knowledge-card-horizontal:hover {
  background: #f3f4f6;
  transform: translateY(-2px);
}

.knowledge-card-horizontal.has-background {
  /* 移除直接背景，使用专门的模糊背景层 */
}

.empty-horizontal-state {
  flex: 0 0 100%;
  text-align: center;
  padding: 40px 24px;
}

@media (max-width: 768px) {
  .dashboard-page {
    padding: 16px;
  }

  .dashboard-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .header-right {
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .knowledge-card-horizontal {
    flex-basis: 280px;
  }

  .modal-grid {
    grid-template-columns: 1fr;
  }
}
</style>
