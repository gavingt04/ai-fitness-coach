import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { 
      path: '/auth', 
      name: 'Login', 
      component: () => import('../views/Login.vue'),
      alias: '/login' // 增加别名，防止组件内跳 /login 报错
    },
    { 
      path: '/', 
      name: 'Home', 
      component: () => import('../views/HomeView.vue'),
      alias: '/home' // 增加别名，防止报错 No match found for /home
    },
    { 
      path: '/training', 
      name: 'Workout', 
      component: () => import('../views/Workout.vue'),
      alias: '/workout'
    },
    { 
      path: '/plan', 
      name: 'Plan', 
      component: () => import('../views/PlanView.vue') 
    },
    { 
      path: '/data', 
      name: 'History', 
      component: () => import('../views/History.vue'),
      alias: '/history' // 👈 【核心修复】：加上这个别名，完美解决 Workout 跳转白屏问题
    },
    { 
      path: '/profile', 
      name: 'Profile', 
      component: () => import('../views/Profile.vue') 
    },
    { 
      path: '/profile/change-password', 
      name: 'ChangePassword', 
      component: () => import('../views/ChangePassword.vue') 
    }
  ]
})

// 路由守卫：修复 next() 警告，改用 return 模式
router.beforeEach((to, from) => {
  const isAuthenticated = localStorage.getItem('token'); 
  if (to.path !== '/auth' && !isAuthenticated) {
    return '/auth';
  }
});

export default router