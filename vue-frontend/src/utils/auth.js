const TOKEN_KEY = 'rag_platform_token'
const USER_KEY = 'rag_platform_user'

export const getAuthToken = () => localStorage.getItem(TOKEN_KEY) || ''

export const setAuthSession = (token, user) => {
  localStorage.setItem(TOKEN_KEY, token || '')
  localStorage.setItem(USER_KEY, JSON.stringify(user || {}))
}

export const clearAuthSession = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem('isLoggedIn')
}

export const getAuthUser = () => {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || '{}')
  } catch (error) {
    return {}
  }
}

export const isAuthenticated = () => Boolean(getAuthToken())
