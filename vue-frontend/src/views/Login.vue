<template>
  <div class="login-page">
    <div class="login-mesh"></div>
    <div class="login-orb login-orb--violet"></div>
    <div class="login-orb login-orb--blue"></div>

    <section class="login-card glass-card">
      <div class="login-copy">
        <span class="eyebrow">AI 第二大脑</span>
        <h1>连接多源知识，把灵感沉淀成真正可用的内容。</h1>
        <p>
          把 PDF、笔记与 AI 对话放进同一个沉浸式空间
        </p>

        <div class="highlight-grid">
          <article v-for="item in highlights" :key="item.title" class="highlight-card">
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
          </article>
        </div>
      </div>

      <div class="auth-panel">
        <div class="panel-top">
          <span class="panel-tag">{{ isRegister ? '创建账号' : '欢迎回来' }}</span>
          <h2>{{ isRegister ? '创建你的第二大脑' : '进入灵感空间' }}</h2>
          <p>{{ isRegister ? '注册后即可同步你的专属知识库、笔记和 AI 对话。' : '继续在你的个人 AI 笔记本中写作、收藏与提问。' }}</p>
        </div>

        <div class="auth-switch">
          <button class="auth-switch__item" :class="{ active: !isRegister }" type="button" @click="switchMode(false)">登录</button>
          <button class="auth-switch__item" :class="{ active: isRegister }" type="button" @click="switchMode(true)">注册</button>
        </div>

        <form class="login-form" @submit.prevent="submitAuth">
          <div v-if="isRegister" class="form-row">
            <label class="field-label" for="nickname">昵称</label>
            <input id="nickname" v-model="form.nickname" class="field-input" type="text" placeholder="设置一个显示名称" autocomplete="nickname" />
          </div>

          <div class="form-row">
            <label class="field-label" for="username">用户名</label>
            <input id="username" v-model="form.username" class="field-input" type="text" placeholder="请输入用户名" autocomplete="username" />
          </div>

          <div class="form-row">
            <label class="field-label" for="password">密码</label>
            <input id="password" v-model="form.password" class="field-input" type="password" placeholder="请输入密码" autocomplete="current-password" />
          </div>

          <div v-if="isRegister" class="form-row">
            <label class="field-label" for="confirm-password">确认密码</label>
            <input id="confirm-password" v-model="form.confirmPassword" class="field-input" type="password" placeholder="请再次输入密码" autocomplete="new-password" />
          </div>

          <div v-if="errorMessage" class="error-banner">
            {{ errorMessage }}
          </div>

          <button class="btn btn-primary submit-btn" type="submit" :disabled="loading">
            {{ loading ? '提交中...' : isRegister ? '注册并进入' : '进入系统' }}
          </button>
        </form>

        <div class="panel-foot">
          <div>
            <span>产品定位</span>
            <strong>个人 AI 笔记本</strong>
          </div>
          <div>
            <span>技术闭环</span>
            <strong>RAG + LLM</strong>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import axios from 'axios'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { setAuthSession } from '../utils/auth'

const router = useRouter()

const isRegister = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const form = reactive({
  nickname: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const highlights = [
  {
    title: '沉浸创作',
    description: '让知识库、笔记与 AI 辅助处在同一个视觉平面。'
  },
  {
    title: '多源沉淀',
    description: '把 PDF、网页资料与快速笔记统一收进一个学习主题。'
  },
  {
    title: '可信问答',
    description: '用真实的 RAG 闭环替代普通的后台式展示。'
  }
]

const switchMode = (registerMode) => {
  isRegister.value = registerMode
  errorMessage.value = ''
}

const completeAuth = async (payload) => {
  setAuthSession(payload.token, payload.user)
  await router.replace('/dashboard')
}

const submitAuth = async () => {
  errorMessage.value = ''

  if (!form.username.trim() || !form.password.trim()) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  if (isRegister.value) {
    if (form.password.trim().length < 6) {
      errorMessage.value = '密码至少需要 6 个字符'
      return
    }
    if (form.password !== form.confirmPassword) {
      errorMessage.value = '两次输入的密码不一致'
      return
    }
  }

  loading.value = true
  try {
    if (isRegister.value) {
      const { data } = await axios.post('/api/auth/register', {
        username: form.username.trim(),
        password: form.password,
        nickname: form.nickname.trim()
      })
      await completeAuth(data)
      return
    }

    const { data } = await axios.post('/api/auth/login', {
      username: form.username.trim(),
      password: form.password
    })
    await completeAuth(data)
  } catch (error) {
    errorMessage.value = error?.response?.data?.error || '认证失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  padding: 28px;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.login-mesh,
.login-orb {
  position: absolute;
  pointer-events: none;
}

.login-mesh {
  inset: 0;
  background:
    radial-gradient(circle at 12% 16%, rgba(200, 215, 240, 0.45), transparent 25%),
    radial-gradient(circle at 86% 14%, rgba(220, 210, 250, 0.4), transparent 28%),
    radial-gradient(circle at 76% 78%, rgba(230, 245, 240, 0.3), transparent 24%),
    radial-gradient(circle at 30% 84%, rgba(245, 235, 245, 0.35), transparent 25%);
  animation: meshFloat 16s ease-in-out infinite alternate;
}

.login-orb {
  width: 480px;
  height: 480px;
  border-radius: 50%;
  filter: blur(56px);
  opacity: 0.35;
}

.login-orb--violet {
  top: -5%;
  left: -5%;
  background: rgba(190, 180, 240, 0.6);
}

.login-orb--blue {
  right: -5%;
  bottom: -5%;
  background: rgba(170, 210, 240, 0.6);
}

.login-card {
  position: relative;
  z-index: 1;
  width: min(1120px, 100%);
  padding: 24px;
  border-radius: var(--radius-xl);
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(360px, 430px);
  gap: 24px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(32px);
  -webkit-backdrop-filter: blur(32px);
  box-shadow: var(--shadow-float);
}

.login-copy,
.auth-panel {
  border-radius: 24px;
}

.login-copy {
  padding: 40px;
  background: transparent;
  border: none;
}

.login-copy h1 {
  margin: 20px 0 14px;
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1.06;
}

.login-copy p {
  margin: 0;
  max-width: 620px;
  color: var(--text-secondary);
  font-size: 17px;
  line-height: 1.9;
}

.highlight-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 34px;
}

.highlight-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.highlight-card strong {
  display: block;
  margin-bottom: 10px;
  font-size: 17px;
}

.highlight-card p {
  font-size: 14px;
  line-height: 1.8;
}

.auth-panel {
  padding: 40px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: var(--shadow-card);
}

.panel-top {
  margin-bottom: 20px;
}

.panel-tag {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(123, 125, 243, 0.12);
  color: var(--primary-strong);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-top h2 {
  margin: 18px 0 10px;
  font-size: 30px;
}

.panel-top p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.75;
}

.auth-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 6px;
  margin-bottom: 20px;
  border-radius: 999px;
  background: rgba(241, 243, 255, 0.88);
  border: 1px solid rgba(130, 143, 187, 0.16);
}

.auth-switch__item {
  min-height: 42px;
  border-radius: 999px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: 0.2s ease;
}

.auth-switch__item.active {
  background: linear-gradient(135deg, var(--primary) 0%, #9c8cff 100%);
  color: #fff;
  box-shadow: 0 14px 28px rgba(123, 125, 243, 0.22);
}

.login-form {
  display: grid;
  gap: 16px;
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
}

.error-banner {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(227, 102, 126, 0.12);
  color: #ba4663;
  font-size: 14px;
}

.panel-foot {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 22px;
}

.panel-foot div {
  padding: 16px;
  border-radius: 20px;
  background: rgba(248, 249, 255, 0.92);
  border: 1px solid rgba(129, 142, 186, 0.12);
}

.panel-foot span {
  display: block;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

.panel-foot strong {
  font-size: 16px;
}

@keyframes meshFloat {
  from {
    transform: scale(1) translate3d(0, 0, 0);
  }

  to {
    transform: scale(1.08) translate3d(0, -14px, 0);
  }
}

@media (max-width: 980px) {
  .login-card {
    grid-template-columns: 1fr;
  }

  .highlight-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .login-page {
    padding: 16px;
  }

  .login-card,
  .login-copy,
  .auth-panel {
    padding: 20px;
  }

  .panel-foot {
    grid-template-columns: 1fr;
  }
}
</style>
