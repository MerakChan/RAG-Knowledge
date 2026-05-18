import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Main from '../views/Main.vue'
import Dashboard from '../views/Dashboard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import { isAuthenticated } from '../utils/auth'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/main',
    name: 'Main',
    component: Main
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const authed = isAuthenticated()
  if (to.path === '/' && authed) {
    return '/dashboard'
  }
  if (to.path !== '/' && !authed) {
    return '/'
  }
  return true
})

export default router
