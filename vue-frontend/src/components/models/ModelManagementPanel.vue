<template>
  <div class="model-panel">
    <section class="hero section-shell">
      <div>
        <span class="eyebrow">Model Hub</span>
        <h2>模型管理中心</h2>
        <p>这里统一管理对话模型与向量模型。可以直接切换内置模型，也可以录入你自己的 OpenAI 兼容 API。</p>
      </div>
      <div class="hero-meta">
        <div>
          <span>当前对话模型</span>
          <strong>{{ activeModel?.name || '未配置' }}</strong>
        </div>
        <div>
          <span>Embedding 模型</span>
          <strong>{{ activeEmbeddingLabel }}</strong>
        </div>
      </div>
    </section>

    <section class="grid-shell">
      <article class="panel section-shell">
        <div class="panel-head">
          <div>
            <span class="eyebrow">Chat Models</span>
            <h3>可用对话模型</h3>
          </div>
          <button class="btn btn-secondary" type="button" :disabled="loading" @click="loadConfig">
            {{ loading ? '刷新中...' : '刷新配置' }}
          </button>
        </div>

        <div v-if="error" class="notice danger">{{ error }}</div>
        <div v-else-if="successMessage" class="notice success">{{ successMessage }}</div>

        <div class="model-list">
          <article
            v-for="model in models"
            :key="model.id"
            class="model-card"
            :class="{ active: model.id === config.active_chat_model_id }"
          >
            <div class="card-top">
              <div>
                <strong>{{ model.name }}</strong>
                <p>{{ model.description || '暂无说明' }}</p>
              </div>
              <span class="status-badge" :class="model.id === config.active_chat_model_id ? 'status-success' : 'status-neutral'">
                {{ model.id === config.active_chat_model_id ? '当前使用' : model.source === 'builtin' ? '内置' : '自定义' }}
              </span>
            </div>

            <div class="meta-grid">
              <div>
                <span>Provider</span>
                <strong>{{ model.provider || 'openai-compatible' }}</strong>
              </div>
              <div>
                <span>模型名</span>
                <strong>{{ model.model_name }}</strong>
              </div>
              <div>
                <span>接口地址</span>
                <strong class="truncate">{{ model.base_url }}</strong>
              </div>
              <div>
                <span>API Key</span>
                <strong>{{ model.has_api_key ? model.api_key_preview || '已配置' : '未配置' }}</strong>
              </div>
            </div>

            <div class="actions">
              <button
                class="btn"
                :class="model.id === config.active_chat_model_id ? 'btn-secondary' : 'btn-primary'"
                type="button"
                :disabled="loading || model.id === config.active_chat_model_id"
                @click="handleActivate(model.id)"
              >
                {{ model.id === config.active_chat_model_id ? '正在使用' : '设为当前模型' }}
              </button>
              <button
                v-if="model.source === 'custom'"
                class="btn btn-danger"
                type="button"
                :disabled="loading"
                @click="handleDelete(model)"
              >
                删除
              </button>
            </div>
          </article>
        </div>
      </article>

      <article class="panel section-shell">
        <div class="panel-head">
          <div>
            <span class="eyebrow">Embedding</span>
            <h3>向量模型配置</h3>
          </div>
        </div>

        <label class="field-label" for="embedding-model">Embedding 模型</label>
        <select id="embedding-model" v-model="embeddingDraft" class="field-select">
          <option v-for="item in config.embedding_options" :key="item.id" :value="item.id">
            {{ item.name }}
          </option>
        </select>
        <p class="helper-text">{{ activeEmbeddingDescription }}</p>

        <div class="actions">
          <button
            class="btn btn-primary"
            type="button"
            :disabled="loading || !embeddingDraft || embeddingDraft === config.active_embedding_model"
            @click="handleEmbeddingSave"
          >
            保存向量模型
          </button>
        </div>

        <div class="capability-list">
          <div class="capability-item">
            <strong>内置模型</strong>
            <p>适合直接演示毕业设计全链路，无需手动再录入接口。</p>
          </div>
          <div class="capability-item">
            <strong>自定义接入</strong>
            <p>支持录入兼容 OpenAI Chat Completions 的第三方 API。</p>
          </div>
          <div class="capability-item">
            <strong>即时生效</strong>
            <p>模型切换后，新的问答请求会直接读取最新配置。</p>
          </div>
        </div>
      </article>
    </section>

    <section class="panel section-shell">
      <div class="panel-head">
        <div>
          <span class="eyebrow">Custom API</span>
          <h3>接入自定义大模型 API</h3>
        </div>
      </div>

      <form class="form-grid" @submit.prevent="handleSubmit">
        <div>
          <label class="field-label" for="model-name">展示名称</label>
          <input id="model-name" v-model="form.name" class="field-input" type="text" placeholder="例如：实验室 GPT-4.1" />
        </div>
        <div>
          <label class="field-label" for="provider">Provider</label>
          <input id="provider" v-model="form.provider" class="field-input" type="text" placeholder="openai-compatible / deepseek / aliyun" />
        </div>
        <div>
          <label class="field-label" for="model-id">模型标识</label>
          <input id="model-id" v-model="form.model_name" class="field-input" type="text" placeholder="例如：gpt-4.1-mini" />
        </div>
        <div>
          <label class="field-label" for="base-url">接口地址</label>
          <input id="base-url" v-model="form.base_url" class="field-input" type="text" placeholder="https://api.xxx.com/v1/chat/completions" />
        </div>
        <div class="span-two">
          <label class="field-label" for="api-key">API Key</label>
          <input id="api-key" v-model="form.api_key" class="field-input" type="password" placeholder="输入可选或必需的 API Key" />
        </div>
        <div class="span-two">
          <label class="field-label" for="description">模型说明</label>
          <textarea id="description" v-model="form.description" class="field-textarea" placeholder="写明适合的任务场景，例如推理、多轮问答、成本优先等。"></textarea>
        </div>
        <label class="toggle">
          <input v-model="form.set_active" type="checkbox" />
          <span>保存后立即切换为当前对话模型</span>
        </label>
        <div class="actions">
          <button class="btn btn-secondary" type="button" :disabled="loading" @click="resetForm">清空表单</button>
          <button class="btn btn-primary" type="submit" :disabled="loading">{{ loading ? '保存中...' : '保存模型配置' }}</button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  activateModel,
  deleteCustomModel,
  getModelConfig,
  saveCustomModel,
  setEmbeddingModel
} from '../../api/platform'

const loading = ref(false)
const error = ref('')
const successMessage = ref('')
const config = ref({
  active_chat_model_id: '',
  active_embedding_model: '',
  embedding_options: [],
  models: []
})
const embeddingDraft = ref('')

const form = reactive({
  name: '',
  provider: 'openai-compatible',
  model_name: '',
  base_url: '',
  api_key: '',
  description: '',
  set_active: true
})

const models = computed(() => config.value.models || [])
const activeModel = computed(() => models.value.find((item) => item.id === config.value.active_chat_model_id) || null)
const activeEmbedding = computed(() => (config.value.embedding_options || []).find((item) => item.id === config.value.active_embedding_model) || null)
const activeEmbeddingLabel = computed(() => activeEmbedding.value?.name || config.value.active_embedding_model || '未配置')
const activeEmbeddingDescription = computed(() => activeEmbedding.value?.description || '用于知识入库与检索召回的默认向量模型。')

const clearTips = () => {
  error.value = ''
  successMessage.value = ''
}

const normalizeBaseUrl = (value) => {
  const raw = String(value || '').trim()
  const match = raw.match(/https?:\/\/\S+/i)
  return match ? match[0].replace(/[),;]+$/, '') : raw
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    provider: 'openai-compatible',
    model_name: '',
    base_url: '',
    api_key: '',
    description: '',
    set_active: true
  })
}

const syncConfig = (data) => {
  config.value = {
    active_chat_model_id: data.active_chat_model_id || '',
    active_embedding_model: data.active_embedding_model || '',
    embedding_options: data.embedding_options || [],
    models: data.models || []
  }
  embeddingDraft.value = config.value.active_embedding_model
}

const loadConfig = async () => {
  loading.value = true
  clearTips()
  try {
    const data = await getModelConfig()
    syncConfig(data)
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || requestError.message || '加载模型配置失败'
  } finally {
    loading.value = false
  }
}

const handleActivate = async (modelId) => {
  loading.value = true
  clearTips()
  try {
    const data = await activateModel(modelId)
    syncConfig(data)
    successMessage.value = '对话模型已切换，新的聊天请求会立即使用该配置。'
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || requestError.message || '切换模型失败'
  } finally {
    loading.value = false
  }
}

const handleEmbeddingSave = async () => {
  loading.value = true
  clearTips()
  try {
    const data = await setEmbeddingModel(embeddingDraft.value)
    syncConfig(data)
    successMessage.value = 'Embedding 模型已更新。'
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || requestError.message || '保存向量模型失败'
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!form.name.trim() || !form.model_name.trim() || !form.base_url.trim()) {
    error.value = '请至少填写展示名称、模型标识和接口地址。'
    return
  }

  loading.value = true
  clearTips()
  try {
    const data = await saveCustomModel({
      name: form.name.trim(),
      provider: form.provider.trim() || 'openai-compatible',
      model_name: form.model_name.trim(),
      base_url: normalizeBaseUrl(form.base_url),
      api_key: form.api_key.trim(),
      description: form.description.trim(),
      set_active: form.set_active
    })
    syncConfig(data)
    successMessage.value = '自定义模型已保存。'
    resetForm()
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || requestError.message || '保存自定义模型失败'
  } finally {
    loading.value = false
  }
}

const handleDelete = async (model) => {
  if (!window.confirm(`确定删除模型“${model.name}”吗？`)) return

  loading.value = true
  clearTips()
  try {
    const data = await deleteCustomModel(model.id)
    syncConfig(data)
    successMessage.value = '自定义模型已删除。'
  } catch (requestError) {
    error.value = requestError?.response?.data?.error || requestError.message || '删除模型失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.model-panel,
.grid-shell,
.model-list,
.meta-grid,
.capability-list,
.form-grid {
  display: grid;
  gap: 18px;
}

.model-panel {
  gap: 20px;
}

.hero,
.panel {
  padding: 24px;
}

.hero {
  display: grid;
  grid-template-columns: 1.35fr 320px;
  gap: 24px;
  background: radial-gradient(circle at top left, rgba(47, 107, 255, 0.12), transparent 34%), linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(246, 249, 255, 0.82));
}

.hero h2,
.panel h3 {
  margin: 10px 0 8px;
}

.hero p,
.card-top p,
.capability-item p,
.helper-text {
  margin: 0;
  line-height: 1.75;
  color: var(--text-secondary);
}

.hero-meta,
.capability-item,
.model-card {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(111, 132, 178, 0.12);
}

.hero-meta {
  display: grid;
  gap: 14px;
}

.hero-meta span,
.meta-grid span {
  display: block;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

.hero-meta strong {
  font-size: 26px;
}

.grid-shell {
  grid-template-columns: 1.45fr 1fr;
}

.panel-head,
.card-top,
.actions {
  display: flex;
  gap: 14px;
  justify-content: space-between;
  align-items: flex-start;
}

.model-list {
  margin-top: 18px;
}

.model-card {
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.model-card.active {
  border-color: rgba(47, 107, 255, 0.24);
  box-shadow: 0 16px 28px rgba(47, 107, 255, 0.12);
}

.model-card:hover {
  transform: translateY(-2px);
}

.meta-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 16px 0 18px;
}

.meta-grid strong {
  display: block;
  color: var(--text-primary);
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.capability-list {
  margin-top: 18px;
}

.notice {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  font-weight: 600;
}

.notice.success {
  background: rgba(15, 159, 110, 0.1);
  color: var(--success);
  border: 1px solid rgba(15, 159, 110, 0.16);
}

.notice.danger {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
  border: 1px solid rgba(239, 68, 68, 0.16);
}

.helper-text {
  margin-top: 10px;
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 18px;
}

.span-two {
  grid-column: 1 / -1;
}

.toggle {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  font-weight: 600;
}

.toggle input {
  width: 18px;
  height: 18px;
}

@media (max-width: 1180px) {
  .hero,
  .grid-shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .hero,
  .panel {
    padding: 18px;
  }

  .form-grid,
  .meta-grid {
    grid-template-columns: 1fr;
  }

  .panel-head,
  .card-top,
  .actions {
    flex-direction: column;
  }
}
</style>
