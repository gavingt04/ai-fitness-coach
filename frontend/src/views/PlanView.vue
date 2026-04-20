<template>
  <div class="plan-container">
    <van-nav-bar title="AI 专属计划生成" left-arrow @click-left="$router.back()" />

    <div v-if="!generatedPlan.length" class="form-box">
      <h3>告诉 AI 你的情况</h3>
      <van-form @submit="onSubmit">
        <van-field v-model="metrics.height" name="height" label="身高(cm)" type="number" placeholder="例如: 175" :rules="[{ required: true }]" />
        <van-field v-model="metrics.weight" name="weight" label="体重(kg)" type="number" placeholder="例如: 70" :rules="[{ required: true }]" />
        
        <van-field name="goal" label="训练目标">
          <template #input>
            <van-radio-group v-model="metrics.goal" direction="horizontal">
              <van-radio name="减脂">减脂</van-radio>
              <van-radio name="增肌">增肌</van-radio>
            </van-radio-group>
          </template>
        </van-field>

        <van-field name="level" label="经验水平">
          <template #input>
            <van-radio-group v-model="metrics.level" direction="horizontal">
              <van-radio name="新手">新手</van-radio>
              <van-radio name="老手">老手</van-radio>
            </van-radio-group>
          </template>
        </van-field>

        <div style="margin: 30px 16px;">
          <van-button round block type="primary" native-type="submit" :loading="isGenerating" loading-text="Gemini 思考中...">
            ✨ 一键生成专属计划
          </van-button>
        </div>
      </van-form>
    </div>

    <div v-else class="plan-result">
      <div class="success-header">
        <van-icon name="checked" color="#07c160" size="40" />
        <h2>你的 AI 专属计划已就绪</h2>
      </div>

      <van-cell-group inset class="plan-list">
        <van-cell 
          v-for="(item, index) in generatedPlan" 
          :key="index" 
          :title="`Day ${item.day}: ${item.exercise_name}`" 
          :label="item.advice"
          center
        >
          <template #value>
            <div class="sets-reps">
              <span class="highlight">{{ item.sets }}</span> 组 × <span class="highlight">{{ item.reps }}</span> 次
            </div>
          </template>
          <template #right-icon>
            <van-button size="small" type="primary" plain @click="goToWorkout(item.exercise_code)">
              去练
            </van-button>
          </template>
        </van-cell>
      </van-cell-group>

      <div style="margin: 30px 16px;">
        <van-button round block type="default" @click="generatedPlan = []">重新生成</van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { useAuthStore } from '../stores/auth';
import axios from 'axios';

const router = useRouter();
const authStore = useAuthStore();
const isGenerating = ref(false);
const generatedPlan = ref([]);

// 绑定的表单数据
const metrics = reactive({
  height: '',
  weight: '',
  goal: '减脂',
  level: '新手',
  days: 3
});

// 提交给后端
const onSubmit = async () => {
  isGenerating.value = true;
  try {
    const res = await axios.post('/api/plan/generate', {
      height: Number(metrics.height),
      weight: Number(metrics.weight),
      goal: metrics.goal,
      level: metrics.level,
      days: metrics.days
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    
    generatedPlan.value = res.data.plan;
    showToast('生成成功！');
  } catch (error) {
    showToast('生成失败，请检查网络或 API Key');
    console.error(error);
  } finally {
    isGenerating.value = false;
  }
};

// 点击去训练，带着动作 Code 跳转
const goToWorkout = (exerciseCode) => {
  router.push({
    path: '/workout',
    // 利用 URL 传参，告诉 Workout.vue 我们要练什么
    query: { exercise: exerciseCode } 
  });
};
</script>

<style scoped>
.plan-container { min-height: 100vh; background-color: #f7f8fa; }
.form-box { padding: 20px 0; }
.form-box h3 { text-align: center; color: #323233; margin-bottom: 20px; }
.plan-result { padding: 20px 0; }
.success-header { text-align: center; margin-bottom: 20px; }
.success-header h2 { font-size: 18px; margin-top: 10px; color: #323233; }
.plan-list { margin-top: 10px; }
.sets-reps { font-size: 14px; font-weight: bold; color: #969799; margin-right: 10px; }
.highlight { color: #1989fa; font-size: 18px; }
</style>