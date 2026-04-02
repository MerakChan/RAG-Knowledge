import { createApp } from 'vue'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import './style.css'
import { clearAuthSession, getAuthToken } from './utils/auth'

axios.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error?.response?.status === 401) {
      clearAuthSession()
      if (router.currentRoute.value.path !== '/') {
        await router.replace('/')
      }
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)
app.use(router)
app.mount('#app')
