<template>
  <div class="home-container">
    <van-nav-bar title="AI 视觉私教引擎" :border="false" />

    <div class="header-card">
      <div class="user-info">
        <h2 class="greeting">System Online.</h2>
        <p class="subtitle">计算视觉就绪，Lean Bulk 模块已激活</p>
      </div>
      <van-image round width="60" height="60" src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg" />
    </div>

    <div class="feature-grid">
      <h3 class="section-title">核心运算模块</h3>
      <van-grid clickable :column-num="2" :gutter="16">
        <van-grid-item to="/workout">
          <template #icon>
            <div class="icon-box blue"><van-icon name="play-circle-o" size="28"/></div>
          </template>
          <template #text><span class="grid-text">边缘计算训练</span></template>
        </van-grid-item>
        
        <van-grid-item to="/plan">
          <template #icon>
            <div class="icon-box green"><van-icon name="orders-o" size="28"/></div>
          </template>
          <template #text><span class="grid-text">大模型计划生成</span></template>
        </van-grid-item>

        <van-grid-item to="/history">
          <template #icon>
            <div class="icon-box orange"><van-icon name="chart-trending-o" size="28"/></div>
          </template>
          <template #text><span class="grid-text">生物力学数据</span></template>
        </van-grid-item>

        <van-grid-item @click="handleLogout">
          <template #icon>
            <div class="icon-box gray"><van-icon name="revoke" size="28"/></div>
          </template>
          <template #text><span class="grid-text">断开系统连接</span></template>
        </van-grid-item>
      </van-grid>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const handleLogout = () => {
  authStore.logout(); 
  router.push('/login');
};
</script>

<style scoped>
.home-container { min-height: 100vh; background-color: #f0f3f6; }
.header-card { 
  background: linear-gradient(135deg, #1989fa, #054a9e); 
  padding: 30px 20px; 
  display: flex; justify-content: space-between; align-items: center;
  color: white; border-bottom-left-radius: 24px; border-bottom-right-radius: 24px;
  box-shadow: 0 10px 20px rgba(25, 137, 250, 0.2);
}
.greeting { margin: 0; font-size: 24px; font-weight: 900; letter-spacing: 1px;}
.subtitle { margin: 8px 0 0; font-size: 14px; opacity: 0.8; }
.feature-grid { padding: 24px 16px; }
.section-title { font-size: 16px; color: #323233; margin-bottom: 16px; font-weight: bold; }
.icon-box { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; color: white;}
.blue { background-color: #1989fa; }
.green { background-color: #07c160; }
.orange { background-color: #ff976a; }
.gray { background-color: #969799; }
.grid-text { font-size: 14px; font-weight: bold; color: #323233; }
:deep(.van-grid-item__content) { border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
</style>