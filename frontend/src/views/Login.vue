<template>
  <div class="login-container">
    <van-nav-bar title="AI 健身引擎" />

    <div class="logo-area">
      <van-icon name="fire" size="60" color="#ee0a24" />
      <h2>欢迎来到 AI 健身</h2>
      <p>您的全栈数字教练</p>
    </div>

    <van-form @submit="onSubmit">
      <van-field
        v-model="username"
        name="username"
        label="用户名"
        placeholder="请输入用户名"
        :rules="[{ required: true, message: '请填写用户名' }]"
      />
      <van-field
        v-model="password"
        :type="showPassword ? 'text' : 'password'"
        name="password"
        label="密码"
        placeholder="请输入密码"
        :right-icon="showPassword ? 'eye-o' : 'closed-eye'"
        @click-right-icon="showPassword = !showPassword"
        :rules="[{ required: true, message: '请填写密码' }]"
      />
      
      <div style="margin: 30px 16px 16px;">
        <van-button round block type="primary" native-type="submit">
          {{ isLoginMode ? '登 录' : '注 册' }}
        </van-button>
      </div>
    </van-form>

    <div class="toggle-mode" @click="isLoginMode = !isLoginMode">
      {{ isLoginMode ? '没有账号？点击注册' : '已有账号？点击登录' }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';


const router = useRouter();
const authStore = useAuthStore();
// 在原有的变量下面加上这一行
const showPassword = ref(false);
// 引入 Vant 的轻提示组件，用来弹出成功或失败的消息
import { showToast, showSuccessToast, showFailToast } from 'vant';

const username = ref('');
const password = ref('');
const isLoginMode = ref(true);

const onSubmit = async (values) => {
  // 开启加载提示
  showToast({ type: 'loading', message: '处理中...', forbidClick: true });

  try {
    if (isLoginMode.value) {
      // ----------------- 登录逻辑 -----------------
      const params = new URLSearchParams();
      params.append('username', values.username);
      params.append('password', values.password);

      // 发送 POST 请求
      const response = await axios.post('/api/login', params);
      
      showSuccessToast('登录成功！');
      
      // --- 【关键修改点：开始】 ---
      const token = response.data.access_token;
      
      // 1. 调用 Pinia 将 Token 存入“钱包” (会自动存入 localStorage)
      authStore.setToken(token);
      
      // 2. 打印一下确认，然后立刻跳转到健身主页面
      console.log('Token 已存入 Pinia:', authStore.token);
      router.push('/home'); 
      // --- 【关键修改点：结束】 ---
      
    } else {
      // ----------------- 注册逻辑 -----------------
      await axios.post('/api/register', {
        username: values.username,
        password: values.password
      });
      
      showSuccessToast('注册成功，请登录');
      isLoginMode.value = true;
      password.value = '';
    }
  } catch (error) {
    const errorMsg = error.response?.data?.detail || '网络请求失败，请检查后端是否启动';
    showFailToast(errorMsg);
  }
};
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background-color: #fff;
}
.logo-area {
  text-align: center;
  padding: 40px 0;
}
.logo-area h2 {
  margin: 10px 0 5px;
  font-size: 24px;
}
.logo-area p {
  margin: 0;
  color: #666;
  font-size: 14px;
}
.toggle-mode {
  text-align: center;
  margin-top: 15px;
  color: #1989fa;
  font-size: 14px;
  cursor: pointer;
}
</style>