import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useAuthStore = defineStore('auth', () => {
  // 1. 状态 (State)：指定为 string 类型
  const token = ref<string>(localStorage.getItem('token') || '');

  // 2. 动作 (Actions)：为参数 newToken 指定 string 类型 [修复点]
  const setToken = (newToken: string) => {
    token.value = newToken;
    localStorage.setItem('token', newToken);
  };

  // 3. 动作 (Actions)：登出逻辑
  const logout = () => {
    token.value = '';
    localStorage.removeItem('token');
  };

  return { token, setToken, logout };
});