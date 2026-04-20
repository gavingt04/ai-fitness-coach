import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// --- 【关键修复 1：召回 Vant 视觉组件库与样式】 ---
import Vant, { showToast } from 'vant'
import 'vant/lib/index.css'

import { useAuthStore } from './stores/auth'

const app = createApp(App)

// 必须先注册 Pinia，保证状态库在拦截器触发前就绪
const pinia = createPinia()
app.use(pinia)
app.use(router)

// --- 【关键修复 2：告诉 Vue 使用 Vant】 ---
app.use(Vant) 

// --- 【Axios 全局保安】 ---
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      showToast('登录已过期，请重新登录');
      const authStore = useAuthStore();
      authStore.clearToken(); // 清空过期凭证
      router.push('/');       // 强制踢回首页
    }
    return Promise.reject(error);
  }
);
// --------------------------------

app.mount('#app')