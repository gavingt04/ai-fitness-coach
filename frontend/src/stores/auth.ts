import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 从浏览器本地缓存中读取 token，如果没有就是空字符串
  const token = ref(localStorage.getItem('fitness_token') || '')

  // 存入 Token 的方法
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('fitness_token', newToken) // 写入硬盘，刷新不掉登录态
  }

  // 登出的方法（清除 Token）
  const clearToken = () => {
    token.value = ''
    localStorage.removeItem('fitness_token')
  }

  return { token, setToken, clearToken }
})