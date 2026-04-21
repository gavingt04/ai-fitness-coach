<template>
  <div class="workout-container" ref="containerRef">
    <van-nav-bar 
      title="AI 边缘计算版 - 损伤防护引擎" 
      left-arrow 
      @click-left="stopTrainingAndBack" 
    >
      <template #right>
        <van-icon name="expand-o" size="20" @click="toggleFullScreen" />
      </template>
    </van-nav-bar>

    <div class="video-box">
      <div v-if="exerciseInfo.isWarning" class="danger-flash-overlay"></div>
      
      <video ref="videoRef" autoplay playsinline muted style="position: absolute; opacity: 0; pointer-events: none; z-index: -1;"></video>
      <canvas ref="canvasRef" class="ai-canvas"></canvas>

      <div class="stats-overlay" v-if="isTraining">
        <div class="stat-item">
          <span class="label">动作</span>
          <span class="value">{{ currentExerciseName }}</span>
        </div>
        <div class="stat-item">
          <span class="label">计数</span>
          <span class="count" :class="{ 'warning-text': exerciseInfo.isWarning }">{{ exerciseInfo.counter }}</span>
        </div>
        <div class="stat-item">
          <span class="label">状态</span>
          <span class="value status-tag">{{ exerciseInfo.stage }}</span>
        </div>
        <div class="stat-item feedback-mini" :class="{ 'warning-border': exerciseInfo.isWarning }">
          {{ exerciseInfo.feedback || '检测中...' }}
        </div>
      </div>
    </div>

    <div class="control-panel">
      <div class="feedback-main" v-if="isTraining" :class="{ 'warning-text': exerciseInfo.isWarning }">
        <van-icon :name="exerciseInfo.isWarning ? 'warning-o' : 'volume-o'" /> 
        {{ exerciseInfo.feedback || '准备开始...' }}
      </div>

      <div class="exercise-selector" v-if="!isTraining">
        <van-cell 
          title="当前训练项目" 
          :value="currentExerciseName" 
          is-link 
          @click="showPicker = true" 
          style="border-radius: 12px; margin-bottom: 15px; background: #f7f8fa;"
        />
      </div>

      <div class="button-group">
        <van-button 
          v-if="!isTraining" 
          type="primary" 
          block 
          round 
          icon="play" 
          @click="startTraining" 
          :loading="!isModelLoaded" 
          loading-text="视觉引擎预热中..."
        >
          开始 {{ currentExerciseName }}
        </van-button>
        <van-button v-else type="danger" block round icon="stop" @click="stopTraining">
          结束并保存报告
        </van-button>
        <van-button v-if="!isTraining" type="default" round icon="clock-o" @click="$router.push('/history')">
          历史记录
        </van-button>
      </div>
    </div>

    <van-action-sheet 
      v-model:show="showPicker" 
      :actions="exerciseOptions" 
      cancel-text="取消" 
      close-on-click-action
      @select="onSelectExercise" 
    />
  </div>
</template>

<script setup>
// 【修复点】：增加了 onMounted 生命周期钩子的引入
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { showToast, showFailToast, showLoadingToast } from 'vant';
import axios from 'axios';

// --- 全局变量接管 (依赖 index.html 中引入的 MediaPipe CDN) ---
const Pose = window.Pose || null;
const POSE_CONNECTIONS = window.POSE_CONNECTIONS || null;
const Camera = window.Camera || null;
const drawConnectors = window.drawConnectors || null;
const drawLandmarks = window.drawLandmarks || null;

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// --- DOM Refs ---
const containerRef = ref(null); 
const videoRef = ref(null);
const canvasRef = ref(null);

// --- 状态控制变量 ---
const isTraining = ref(false);
const showPicker = ref(false);
const isModelLoaded = ref(false); // 【新增】：模型加载状态标志

let poseModel = null;
let camera = null;

// 优先从路由参数读取动作，默认深蹲
const selectedExerciseCode = ref(route.query.exercise || 'SQUAT'); 

const exerciseOptions = [
  { name: '深蹲 (Squat)', value: 'SQUAT' },
  { name: '二头弯举 (Bicep Curl)', value: 'BICEP_CURL' },
  { name: '硬拉 (Deadlift)', value: 'DEADLIFT' },
  { name: '俯卧撑 (Push Up)', value: 'PUSH_UP' },
  { name: '卧推 (Bench Press)', value: 'BENCH_PRESS' }
];

const currentExerciseName = computed(() => {
  const target = exerciseOptions.find(opt => opt.value === selectedExerciseCode.value);
  return target ? target.name : '未知动作';
});

const onSelectExercise = (action) => {
  selectedExerciseCode.value = action.value;
  exerciseInfo.name = action.value; 
};

// 核心计分板与状态面板
const exerciseInfo = reactive({
  name: selectedExerciseCode.value,
  counter: 0,
  stage: 'UP', 
  feedback: 'Ready',
  isWarning: false
});

// 利用 Set 自动去重，记录本次训练触发的所有动作代偿/错误
const detectedIssues = new Set();

// --- 语音引擎 ---
const synth = window.speechSynthesis;
let lastSpokenText = ''; 
const speakFeedback = (text, isWarning = false) => {
  if (text === lastSpokenText || text === 'Ready' || !text) return;
  synth.cancel(); 
  const utterThis = new SpeechSynthesisUtterance(text);
  utterThis.lang = 'en-US'; 
  utterThis.rate = isWarning ? 1.3 : 1.1; 
  utterThis.pitch = isWarning ? 1.2 : 1.0; 
  synth.speak(utterThis);
  lastSpokenText = text;
};


// ==========================================
//          AI 生物力学损伤引擎区
// ==========================================
const calculateAngle = (a, b, c) => {
  const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
  let angle = Math.abs((radians * 180.0) / Math.PI);
  return angle > 180.0 ? 360 - angle : angle;
};
const getDistance = (p1, p2) => Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));

let lastAngle = 0;
let lastVelocity = 0;
const getAcceleration = (currentAngle) => {
  const velocity = currentAngle - lastAngle; 
  const acceleration = velocity - lastVelocity; 
  lastAngle = currentAngle;
  lastVelocity = velocity;
  return Math.abs(acceleration);
};

const landmarkBuffer = {};
const getSmoothPoint = (index, point) => {
  if (!point) return { x: 0, y: 0 };
  if (!landmarkBuffer[index]) landmarkBuffer[index] = [];
  landmarkBuffer[index].push(point);
  if (landmarkBuffer[index].length > 5) landmarkBuffer[index].shift();
  const sum = landmarkBuffer[index].reduce((a, b) => ({ x: a.x + b.x, y: a.y + b.y }), { x: 0, y: 0 });
  return { x: sum.x / landmarkBuffer[index].length, y: sum.y / landmarkBuffer[index].length };
};

const processExerciseLogic = (lm) => {
  exerciseInfo.isWarning = false;

  const earL = getSmoothPoint(7, lm[7]), earR = getSmoothPoint(8, lm[8]);
  const shL = getSmoothPoint(11, lm[11]), shR = getSmoothPoint(12, lm[12]);
  const elL = getSmoothPoint(13, lm[13]);
  const wrL = getSmoothPoint(15, lm[15]), wrR = getSmoothPoint(16, lm[16]);
  const hipL = getSmoothPoint(23, lm[23]), hipR = getSmoothPoint(24, lm[24]);
  const knL = getSmoothPoint(25, lm[25]), knR = getSmoothPoint(26, lm[26]);
  const anL = getSmoothPoint(27, lm[27]);

  switch (selectedExerciseCode.value) {
    case 'SQUAT': {
      const valgusRatio = getDistance(knL, knR) / getDistance(hipL, hipR);
      if (valgusRatio < 0.7) triggerWarning('Knees Out!', 'Danger: Knee Valgus');

      const kneeAngle = calculateAngle(hipL, knL, anL);
      if (kneeAngle < 100 && getAcceleration(kneeAngle) > 8) {
        triggerWarning('Slow Down!', 'High Impact Detected');
      }

      if (kneeAngle < 95 && exerciseInfo.stage === 'UP') exerciseInfo.stage = 'DOWN';
      else if (kneeAngle > 160 && exerciseInfo.stage === 'DOWN') completeRep();
      break;
    }
    case 'BENCH_PRESS': {
      const flareAngle = calculateAngle(shL, elL, { x: shL.x, y: shL.y + 1 });
      if (flareAngle > 70) triggerWarning('Tuck Elbows!', 'Shoulder Impingement Risk');

      const gripRatio = getDistance(wrL, wrR) / getDistance(shL, shR);
      if (gripRatio > 1.5) triggerWarning('Narrow Grip!', 'AC Joint Stress');
      
      const pressAngle = calculateAngle(shL, elL, wrL);
      if (pressAngle < 80 && exerciseInfo.stage === 'UP') exerciseInfo.stage = 'DOWN';
      if (pressAngle > 150 && exerciseInfo.stage === 'DOWN') completeRep();
      break;
    }
    case 'DEADLIFT': {
      const spineAngle = calculateAngle(shL, hipL, anL);
      if (!exerciseInfo.baseSpineAngle) exerciseInfo.baseSpineAngle = spineAngle;
      if (Math.abs(spineAngle - exerciseInfo.baseSpineAngle) > 10) {
        triggerWarning('Straighten Back!', 'Spinal Creep Detected');
      }

      if (Math.abs(wrL.x - anL.x) > 0.15) triggerWarning('Bar Close!', 'Horizontal Shift');
      
      const liftAngle = calculateAngle(shL, hipL, knL);
      if (liftAngle < 60) exerciseInfo.stage = 'DOWN';
      if (liftAngle > 160 && exerciseInfo.stage === 'DOWN') completeRep();
      break;
    }
    case 'PUSH_UP': {
      const coreAngle = calculateAngle(shL, hipL, anL);
      if (coreAngle < 160) triggerWarning('Tighten Core!', 'Core Sagging');

      if (Math.abs(earL.x - shL.x) > 0.1) triggerWarning('Head Up!', 'Neck Compensation');
      
      const pushAngle = calculateAngle(shL, elL, wrL);
      if (pushAngle < 90) exerciseInfo.stage = 'DOWN';
      if (pushAngle > 160 && exerciseInfo.stage === 'DOWN') completeRep();
      break;
    }
    case 'BICEP_CURL': {
      const trunkAngle = calculateAngle(shL, hipL, { x: hipL.x, y: hipL.y - 1 });
      if (trunkAngle > 15) triggerWarning('No Swinging!', 'Trunk Swing');

      const shoulderFlex = calculateAngle(elL, shL, hipL);
      if (shoulderFlex > 20) triggerWarning('Elbows Back!', 'Deltoid Compensation');
      
      const curlAngle = calculateAngle(shL, elL, wrL);
      if (curlAngle < 40 && exerciseInfo.stage === 'DOWN') completeRep();
      else if (curlAngle > 150) exerciseInfo.stage = 'DOWN';
      break;
    }
  }
};

const triggerWarning = (speech, text) => {
  exerciseInfo.isWarning = true;
  exerciseInfo.feedback = text;
  detectedIssues.add(text); 
  speakFeedback(speech, true);
};

const completeRep = () => {
  exerciseInfo.counter++;
  exerciseInfo.stage = 'UP';
  exerciseInfo.feedback = 'Perfect!';
  speakFeedback(exerciseInfo.counter.toString());
};


// ==========================================
//          相机流控制与系统生命周期
// ==========================================

const onResults = (results) => {
  if (!canvasRef.value) return;
  const canvasCtx = canvasRef.value.getContext('2d');
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
  
  // 【关键修复点】：将摄像头画面绘制到 Canvas 基层
  canvasCtx.drawImage(videoRef.value, 0, 0, canvasRef.value.width, canvasRef.value.height);
  
  if (results.poseLandmarks) {
    drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, { color: '#00FF00', lineWidth: 4 });
    drawLandmarks(canvasCtx, results.poseLandmarks, { color: '#FF0000', lineWidth: 2 });
    
    // 骨骼点传递给物理损伤引擎
    processExerciseLogic(results.poseLandmarks);
  }
  canvasCtx.restore();
};

// 【修复点】：独立的模型预加载函数
const initAIModel = async () => {
  if (!Pose) return;
  poseModel = new Pose({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
  });
  poseModel.setOptions({
    modelComplexity: 1, smoothLandmarks: true, 
    minDetectionConfidence: 0.5, minTrackingConfidence: 0.5
  });
  poseModel.onResults(onResults);
  
  // 强制模型预下载核心文件 (.wasm)
  await poseModel.initialize(); 
  isModelLoaded.value = true; // 释放按钮的 Loading 状态
};

const startTraining = async () => {
  if (!poseModel || !Camera) {
    showFailToast('核心组件初始化失败，请检查网络');
    return;
  }
  isTraining.value = true;
  exerciseInfo.counter = 0;
  exerciseInfo.stage = selectedExerciseCode.value === 'BICEP_CURL' ? 'DOWN' : 'UP';
  exerciseInfo.feedback = 'Ready';
  detectedIssues.clear(); 

 if (videoRef.value) {
    camera = new Camera(videoRef.value, {
      onFrame: async () => {
        if (canvasRef.value && videoRef.value) {
          // 【关键优化点】：只有当尺寸不匹配时才设置宽高，防止 Canvas 每秒 30 次被强行清空
          if (canvasRef.value.width !== videoRef.value.videoWidth) {
            canvasRef.value.width = videoRef.value.videoWidth;
            canvasRef.value.height = videoRef.value.videoHeight;
          }
          await poseModel.send({ image: videoRef.value });
        }
      },
      width: 640, height: 480
    });
    camera.start();
  }
};

const stopTraining = async () => {
  isTraining.value = false;
  if (camera) { camera.stop(); camera = null; }
  
  const issueSummary = Array.from(detectedIssues).join(', ');
  
  try {
    showLoadingToast('正在生成生物力学分析报告...');
    // 【修复点】：路径确保包含 /api ，匹配后端的 RESTful 路由
    await axios.post('/api/records', {
      exercise_type: selectedExerciseCode.value,
      count: exerciseInfo.counter,
      issues: issueSummary 
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });
    showToast('数据已归档至云端');
    router.push('/history');
  } catch (error) {
    showFailToast('保存失败，请检查网络');
  }
};

const stopTrainingAndBack = () => {
  if (isTraining.value) { stopTraining(); }
  else { router.back(); }
};

const toggleFullScreen = () => {
  if (!document.fullscreenElement) { containerRef.value?.requestFullscreen(); } 
  else { document.exitFullscreen(); }
};

// 【修复点】：利用 Vue 挂载钩子，实现无感加载
onMounted(() => {
  // 唤醒浏览器底层语音合成队列，防止第一次播报卡顿
  synth.getVoices(); 
  
  // 异步预热视觉大模型
  initAIModel(); 
});

onUnmounted(() => {
  isTraining.value = false;
  if (camera) { camera.stop(); camera = null; }
  if (poseModel) { poseModel.close(); }
});

const handleLogout = () => {
  // 1. 调用刚刚在 auth.ts 中写好的 logout 函数
  if (typeof authStore.logout === 'function') {
    authStore.logout();
  }

  // 2. 终极物理保险：清空浏览器所有的本地存储，确保没有任何幽灵 Token 残留
  localStorage.clear();
  sessionStorage.clear();
  
  showSuccessToast('系统已断开');

  // 3. 强制跳转回登录页
  router.replace('/login');
};
</script>

<style scoped>
.workout-container { height: 100vh; display: flex; flex-direction: column; background-color: #000; width: 100%; max-width: 800px; margin: 0 auto; }
:deep(.van-nav-bar) { position: relative; z-index: 99; }
.video-box { flex: 1; position: relative; display: flex; align-items: center; justify-content: center; background: #111; overflow: hidden; }

/* 预警高亮层 */
.danger-flash-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  box-shadow: inset 0 0 80px rgba(238, 10, 36, 0.9);
  border: 4px solid #ee0a24;
  pointer-events: none; 
  z-index: 5;
  animation: alarm-pulse 0.6s infinite alternate;
}
@keyframes alarm-pulse {
  0% { opacity: 0.3; }
  100% { opacity: 1; }
}

.ai-canvas { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
.stats-overlay { position: absolute; top: 16px; right: 16px; background: rgba(0,0,0,0.6); backdrop-filter: blur(8px); padding: 16px; border-radius: 12px; color: #fff; border: 1px solid rgba(25, 137, 250, 0.3); min-width: 130px; z-index: 10;}
.stat-item { margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;}
.label { font-size: 12px; color: #ccc; }
.count { color: #1989fa; font-weight: 900; font-size: 24px; }
.status-tag { color: #07c160; font-weight: bold; }
.feedback-mini { border-top: 1px solid #333; padding-top: 8px; font-size: 12px; color: #ff976a; text-align: center; display: block;}
.control-panel { padding: 20px; background: #fff; border-radius: 24px 24px 0 0; position: relative; z-index: 99;}
.feedback-main { text-align: center; color: #1989fa; font-weight: 900; font-size: 20px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px;}
.button-group { display: flex; gap: 12px; }

.warning-text { color: #ee0a24 !important; animation: text-pulse 1s infinite; }
.warning-border { border-top-color: #ee0a24 !important; color: #ee0a24 !important; }
@keyframes text-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); text-shadow: 0 0 10px rgba(238, 10, 36, 0.5); }
  100% { transform: scale(1); }
}
</style>