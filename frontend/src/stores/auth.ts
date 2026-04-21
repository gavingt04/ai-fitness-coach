import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useAuthStore = defineStore('auth', () => {
  // 1. 状态 (State)：从本地缓存中读取初始 token，如果没有则为空字符串
  const token = ref(localStorage.getItem('token') || '');

  // 2. 动作 (Actions)：登录成功时保存 token
  const setToken = (newToken) => {
    token.value = newToken;
    localStorage.setItem('token', newToken); // 物理存入浏览器缓存
  };

  // 3. 动作 (Actions)：登出时清除 token
  const logout = () => {
    token.value = '';
    localStorage.removeItem('token'); // 从浏览器缓存中物理抹除
  };

  // 必须将这些变量和函数 return 出去，外部组件才能调用！
  return { token, setToken, logout };
});