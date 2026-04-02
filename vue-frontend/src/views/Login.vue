<template>
  <div class="login-page">
    <section class="login-brand">
      <div class="brand-badge">AI Second Brain</div>
      <h1>多元知识库与混合大模型智能学习平台</h1>
      <p class="brand-copy">
        面向毕业设计场景，统一连接文档、网页收藏、数据库笔记与 RAG 问答能力，并通过账号体系保护个人学习资产。
      </p>

      <div class="brand-grid">
        <article v-for="item in highlights" :key="item.title" class="brand-card">
          <span class="brand-card__value">{{ item.value }}</span>
          <strong>{{ item.title }}</strong>
          <p>{{ item.description }}</p>
        </article>
      </div>
    </section>

    <section class="login-panel glass-card">
      <div class="panel-top">
        <span class="panel-tag">{{ isRegister ? 'Register' : 'Welcome Back' }}</span>
        <h2>{{ isRegister ? '创建你的学习账号' : '登录进入系统' }}</h2>
        <p>{{ isRegister ? '注册后即可使用 JWT 认证访问个人知识库、学习资料中心和 AI 问答功能。' : '使用账号密码登录，进入你的 AI 第二大脑系统。' }}</p>
      </div>

      <div class="auth-switch">
        <button class="auth-switch__item" :class="{ active: !isRegister }" type="button" @click="switchMode(false)">登录</button>
        <button class="auth-switch__item" :class="{ active: isRegister }" type="button" @click="switchMode(true)">注册</button>
      </div>

      <form class="login-form" @submit.prevent="submitAuth">
        <div v-if="isRegister" class="form-row">
          <label class="field-label" for="nickname">昵称</label>
          <input id="nickname" v-model="form.nickname" class="field-input" type="text" placeholder="请输入昵称" autocomplete="nickname" />
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
          {{ loading ? '提交中...' : isRegister ? '注册并进入系统' : '登录系统' }}
        </button>
      </form>

      <div class="account-tip">
        <div>
          <span>认证方式</span>
          <strong>JWT</strong>
        </div>
        <div>
          <span>密码存储</span>
          <strong>Hash</strong>
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
    title: '多源知识接入',
    value: 'RAG',
    description: '支持文件、网页、快速笔记和 SQL 代码记录统一接入知识库。'
  },
  {
    title: '混合大模型配置',
    value: 'LLM + API',
    description: '独立支持模型与 API 配置，体现多模型接入和混合开发能力。'
  },
  {
    title: '账号安全访问',
    value: 'JWT',
    description: '通过注册、登录和令牌校验实现真实账号密码访问。'
  }
]

const switchMode = (registerMode) => {
  isRegister.value = registerMode
  errorMessage.value = ''
}

const completeAuth = async (payload) => {
  setAuthSession(payload.token, payload.user)
  await router.replace('/main')
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
  min-height: 100vh;
  padding: 32px;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 460px);
  gap: 28px;
  align-items: stretch;
}

.login-brand,
.login-panel {
  border-radius: var(--radius-xl);
}

.login-brand {
  position: relative;
  overflow: hidden;
  padding: 44px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.22), transparent 24%),
    linear-gradient(145deg, #15337f 0%, #285ee6 48%, #46a8ff 100%);
  color: #f7fbff;
  box-shadow: var(--shadow-float);
}

.login-brand::after {
  content: "";
  position: absolute;
  inset: auto -120px -120px auto;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}

.brand-badge {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 0 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: 13px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.login-brand h1 {
  max-width: 680px;
  margin: 26px 0 16px;
  font-size: clamp(36px, 5vw, 58px);
  line-height: 1.08;
}

.brand-copy {
  max-width: 620px;
  margin: 0;
  font-size: 18px;
  line-height: 1.8;
  color: rgba(247, 251, 255, 0.86);
}

.brand-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-top: 44px;
}

.brand-card {
  padding: 22px 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.11);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
}

.brand-card__value {
  display: block;
  margin-bottom: 18px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(247, 251, 255, 0.7);
}

.brand-card strong {
  display: block;
  margin-bottom: 10px;
  font-size: 20px;
}

.brand-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: rgba(247, 251, 255, 0.76);
}

.login-panel {
  align-self: center;
  padding: 34px;
}

.panel-top {
  margin-bottom: 22px;
}

.panel-tag {
  display: inline-flex;
  margin-bottom: 14px;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(47, 107, 255, 0.1);
  color: var(--primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-top h2 {
  margin: 0 0 10px;
  font-size: 30px;
  line-height: 1.15;
}

.panel-top p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.auth-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 8px;
  border-radius: 999px;
  background: rgba(244, 247, 252, 0.96);
  border: 1px solid var(--line-soft);
  margin-bottom: 22px;
}

.auth-switch__item {
  min-height: 42px;
  border-radius: 999px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: .2s;
}

.auth-switch__item.active {
  background: var(--bg-accent);
  color: #fff;
  box-shadow: 0 10px 20px rgba(47, 107, 255, 0.18);
}

.login-form {
  display: grid;
  gap: 18px;
}

.form-row {
  display: grid;
}

.submit-btn {
  width: 100%;
  margin-top: 8px;
}

.error-banner {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
  font-size: 14px;
}

.account-tip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 24px;
}

.account-tip div {
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(244, 247, 252, 0.9);
  border: 1px solid var(--line-soft);
}

.account-tip span {
  display: block;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

.account-tip strong {
  font-size: 18px;
}

@media (max-width: 1080px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .brand-grid {
    grid-template-columns: 1fr;
  }

  .login-panel {
    max-width: 560px;
    width: 100%;
    justify-self: center;
  }
}

@media (max-width: 640px) {
  .login-page {
    padding: 18px;
  }

  .login-brand,
  .login-panel {
    padding: 24px;
  }

  .account-tip {
    grid-template-columns: 1fr;
  }
}
</style>
