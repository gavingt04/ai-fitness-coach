import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// 1. 引入所有页面组件
import Login from '../views/Login.vue'
import Workout from '../views/Workout.vue'
import History from '../views/History.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: Login
    },
    {
      path: '/workout',
      name: 'workout',
      component: Workout
    },
    {
      path: '/history',
      name: 'history',
      component: History
    }
  ]
})

// --- 【高级进阶】：全局路由守卫 ---
// 逻辑：如果去健身或看历史，但钱包里没有 Token，强制跳回登录页
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.name !== 'login' && !authStore.token) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router