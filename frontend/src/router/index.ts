import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import Login from '../views/Login.vue'
import HomeView from '../views/HomeView.vue' // 新增主页
import Workout from '../views/Workout.vue'
import History from '../views/History.vue'
import PlanView from '../views/PlanView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', name: 'login', component: Login },
    { path: '/', redirect: '/home' }, // 根路径重定向到主页
    { path: '/home', name: 'home', component: HomeView, meta: { requiresAuth: true } },
    { path: '/workout', name: 'workout', component: Workout, meta: { requiresAuth: true } },
    { path: '/history', name: 'history', component: History, meta: { requiresAuth: true } },
    { path: '/plan', name: 'plan', component: PlanView, meta: { requiresAuth: true } }
  ]
})

// 全局路由守卫
router.beforeEach((to, from) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.token) {
    return '/login'; 
  }
  return true; 
});

export default router