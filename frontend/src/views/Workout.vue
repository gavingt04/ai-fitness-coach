<template>
  <div class="workout-container" ref="containerRef">
    <van-nav-bar 
      title="AI 边缘计算版" 
      left-arrow 
      @click-left="stopTrainingAndBack" 
    >
      <template #right>
        <van-icon name="expand-o" size="20" @click="toggleFullScreen" />
      </template>
    </van-nav-bar>

    <div class="video-box">
      <video ref="videoRef" autoplay playsinline muted style="position: absolute; opacity: 0; pointer-events: none; z-index: -1;"></video>
      <canvas ref="canvasRef" class="ai-canvas"></canvas>

      <div class="stats-overlay" v-if="isTraining">
        <div class="stat-item">
          <span class="label">动作</span>
          <span class="value">{{ exerciseInfo.name }}</span>
        </div>
        <div class="stat-item">
          <span class="label">计数</span>
          <span class="count">{{ exerciseInfo.counter }}</span>
        </div>
        <div class="stat-item">
          <span class="label">状态</span>
          <span class="value status-tag">{{ exerciseInfo.stage }}</span>
        </div>
        <div class="stat-item feedback-mini">
          {{ exerciseInfo.feedback || '检测中...' }}
        </div>
      </div>
    </div>

    <div class="control-panel">
      <div class="feedback-main" v-if="isTraining">
        <van-icon name="volume-o" /> {{ exerciseInfo.feedback || '准备开始...' }}
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
        <van-button v-if="!isTraining" type="primary" block round icon="play" @click="startTraining">
          开始 {{ currentExerciseName }}
        </van-button>
        <van-button v-else type="danger" block round icon="stop" @click="stopTraining">
          结束并保存
        </van-button>

        <van-button v-if="!isTraining" type="default" round icon="clock-o" @click="$router.push('/history')">
          历史
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
import { ref, reactive, onUnmounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { showToast, showFailToast, showLoadingToast } from 'vant';
import axios from 'axios';

// --- 全局变量接管 ---
const Pose = window.Pose;
const POSE_CONNECTIONS = window.POSE_CONNECTIONS;
const Camera = window.Camera;
const drawConnectors = window.drawConnectors;
const drawLandmarks = window.drawLandmarks;

// --- 路由与状态 ---
const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// --- DOM 引用 ---
const containerRef = ref(null); 
const videoRef = ref(null);
const canvasRef = ref(null);

// --- 核心状态 ---
const isTraining = ref(false);
let poseModel = null;
let camera = null;
const showPicker = ref(false);
const selectedExerciseCode = ref(route.query.exercise || 'SQUAT'); 

// --- AI 语音引擎 ---
const synth = window.speechSynthesis;
let lastSpokenText = ''; 

const speakFeedback = (text) => {
  if (text === lastSpokenText || text === 'Ready' || !text) return;
  synth.cancel(); 
  const utterThis = new SpeechSynthesisUtterance(text);
  utterThis.lang = 'en-US'; 
  utterThis.rate = 1.1;     
  utterThis.pitch = 1.0;    
  synth.speak(utterThis);
  lastSpokenText = text;
};

// --- 动作配置 ---
const exerciseOptions = [
  { name: '深蹲 (Squat)', value: 'SQUAT' },
  { name: '二头弯举 (Bicep Curl)', value: 'BICEP_CURL' },
  { name: '硬拉 (Deadlift)', value: 'DEADLIFT' },
  { name: '俯卧撑 (Push Up)', value: 'PUSH_UP' },
  { name: '卧推 (Bench Press)', value: 'BENCH_PRESS' }
];

const currentExerciseName = computed(() => {
  const target = exerciseOptions.find(opt => opt.value === selectedExerciseCode.value);
  return target ? target.name : '深蹲';
});

const onSelectExercise = (action) => {
  selectedExerciseCode.value = action.value;
  exerciseInfo.name = action.value; 
};

const exerciseInfo = reactive({
  name: selectedExerciseCode.value,
  counter: 0,
  stage: 'UP', 
  feedback: 'Ready'
});

// --- 几何与平滑算法 ---
const calculateAngle = (a, b, c) => {
  const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
  let angle = Math.abs((radians * 180.0) / Math.PI);
  if (angle > 180.0) angle = 360 - angle;
  return angle;
};

const landmarkBuffer = {};
const getSmoothLandmark = (index, currentPoint) => {
  if (!landmarkBuffer[index]) landmarkBuffer[index] = [];
  landmarkBuffer[index].push(currentPoint);
  if (landmarkBuffer[index].length > 5) landmarkBuffer[index].shift();
  const avg = landmarkBuffer[index].reduce((acc, val) => {
    acc.x += val.x; acc.y += val.y;
    return acc;
  }, {x: 0, y: 0});
  return { x: avg.x / landmarkBuffer[index].length, y: avg.y / landmarkBuffer[index].length };
};

// --- AI 核心判定逻辑 ---
const processExerciseLogic = (landmarks) => {
  if (selectedExerciseCode.value === 'SQUAT') {
    const angle = calculateAngle(getSmoothLandmark(23, landmarks[23]), getSmoothLandmark(25, landmarks[25]), getSmoothLandmark(27, landmarks[27]));
    if (angle < 90 && exerciseInfo.stage === 'UP') { 
      exerciseInfo.stage = 'DOWN'; exerciseInfo.feedback = 'Push up!'; speakFeedback('Push up!');
    } else if (angle > 160 && exerciseInfo.stage === 'DOWN') { 
      exerciseInfo.stage = 'UP'; exerciseInfo.counter += 1; exerciseInfo.feedback = `Perfect!`; speakFeedback(exerciseInfo.counter.toString());
    }
  } else if (selectedExerciseCode.value === 'BICEP_CURL') {
    const angle = calculateAngle(getSmoothLandmark(12, landmarks[12]), getSmoothLandmark(14, landmarks[14]), getSmoothLandmark(16, landmarks[16]));
    if (angle < 40 && exerciseInfo.stage === 'DOWN') { 
      exerciseInfo.stage = 'UP'; exerciseInfo.counter += 1; exerciseInfo.feedback = `Good squeeze!`; speakFeedback(exerciseInfo.counter.toString());
    } else if (angle > 150 && exerciseInfo.stage === 'UP') { 
      exerciseInfo.stage = 'DOWN'; exerciseInfo.feedback = 'Slowly down...'; speakFeedback('Slowly down');
    }
  } else if (selectedExerciseCode.value === 'DEADLIFT') {
    const angle = calculateAngle(getSmoothLandmark(12, landmarks[12]), getSmoothLandmark(24, landmarks[24]), getSmoothLandmark(26, landmarks[26]));
    if (angle < 110 && exerciseInfo.stage === 'UP') { 
      exerciseInfo.stage = 'DOWN'; exerciseInfo.feedback = 'Push hips forward!'; speakFeedback('Push hips forward');
    } else if (angle > 160 && exerciseInfo.stage === 'DOWN') { 
      exerciseInfo.stage = 'UP'; exerciseInfo.counter += 1; exerciseInfo.feedback = `Perfect Pull!`; speakFeedback(exerciseInfo.counter.toString());
    }
  } else if (selectedExerciseCode.value === 'PUSH_UP') {
    const angle = calculateAngle(getSmoothLandmark(11, landmarks[11]), getSmoothLandmark(13, landmarks[13]), getSmoothLandmark(15, landmarks[15]));
    if (angle < 90 && exerciseInfo.stage === 'UP') { 
      exerciseInfo.stage = 'DOWN'; exerciseInfo.feedback = 'Push up!'; speakFeedback('Push up!');
    } else if (angle > 160 && exerciseInfo.stage === 'DOWN') { 
      exerciseInfo.stage = 'UP'; exerciseInfo.counter += 1; exerciseInfo.feedback = `Perfect!`; speakFeedback(exerciseInfo.counter.toString());
    }
  } else if (selectedExerciseCode.value === 'BENCH_PRESS') {
    const angle = calculateAngle(getSmoothLandmark(11, landmarks[11]), getSmoothLandmark(13, landmarks[13]), getSmoothLandmark(15, landmarks[15]));
    if (angle < 90 && exerciseInfo.stage === 'UP') { 
      exerciseInfo.stage = 'DOWN'; exerciseInfo.feedback = 'Drive!'; speakFeedback('Drive!');
    } else if (angle > 160 && exerciseInfo.stage === 'DOWN') { 
      exerciseInfo.stage = 'UP'; exerciseInfo.counter += 1; exerciseInfo.feedback = `Light weight!`; speakFeedback(exerciseInfo.counter.toString());
    }
  }
};

const toggleFullScreen = () => {
  const elem = containerRef.value;
  if (!document.fullscreenElement) {
    if (elem.requestFullscreen) elem.requestFullscreen();
    else if (elem.webkitRequestFullscreen) elem.webkitRequestFullscreen();
  } else {
    if (document.exitFullscreen) document.exitFullscreen();
  }
};

// --- 控制台动作 (热机与语音解锁) ---
const startTraining = async () => {
  // 语音解锁
  const unlockUtter = new SpeechSynthesisUtterance(' '); 
  synth.speak(unlockUtter);
  speakFeedback("Go"); 

  isTraining.value = true; 
  exerciseInfo.counter = 0;
  exerciseInfo.feedback = 'Ready';
  exerciseInfo.stage = selectedExerciseCode.value === 'BICEP_CURL' ? 'DOWN' : 'UP';

  const loading = showLoadingToast({ message: '引擎就绪中...', forbidClick: true, duration: 0 });
  
  try {
    if(!poseModel){
      poseModel = new Pose({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}` });
      poseModel.setOptions({ modelComplexity: 1, smoothLandmarks: true, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
      poseModel.onResults((results) => {
        if (!isTraining.value) return;
        const ctx = canvasRef.value.getContext('2d');
        canvasRef.value.width = videoRef.value.videoWidth;
        canvasRef.value.height = videoRef.value.videoHeight;
        ctx.save(); 
        ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
        ctx.drawImage(results.image, 0, 0, canvasRef.value.width, canvasRef.value.height);
        if (results.poseLandmarks) {
          processExerciseLogic(results.poseLandmarks);
          drawConnectors(ctx, results.poseLandmarks, POSE_CONNECTIONS, {color: '#1989fa', lineWidth: 4});
          drawLandmarks(ctx, results.poseLandmarks, {color: '#07c160', lineWidth: 2, radius: 3});
        }
        ctx.restore();
      });
    }

    if (!camera) { 
      camera = new Camera(videoRef.value, { 
        onFrame: async () => { 
          if (isTraining.value) await poseModel.send({image: videoRef.value}); 
        }, 
        width: 1280, height: 720 
      });
      await camera.start();
    }
    
    loading.close();
  } catch (err) { 
    loading.close(); 
    showFailToast('引擎启动失败'); 
    isTraining.value = false; 
  }
};

const stopTraining = async () => {
  if (!isTraining.value) return;
  isTraining.value = false;
  const finalCount = exerciseInfo.counter;
  
  if (finalCount > 0) {
    try {
      showLoadingToast({ message: '保存记录...', duration: 0 });
      await axios.post('/api/records', { exercise_type: selectedExerciseCode.value, count: finalCount }, { headers: { Authorization: `Bearer ${authStore.token}` } });
      showToast(`保存成功：完成了 ${finalCount} 个动作`);
    } catch (e) { showFailToast('保存失败'); }
  } else { showToast('未产生训练数据'); }
};

const stopTrainingAndBack = () => { 
  stopTraining(); 
  router.back(); 
};

onUnmounted(() => {
  isTraining.value = false;
  if (camera) { 
    camera.stop(); 
    camera = null; 
  }
});
</script>

<style scoped>
/* --- 极其重要的 CSS，控制整体布局不崩塌 --- */
.workout-container { 
  height: 100vh; 
  display: flex; 
  flex-direction: column; 
  background-color: #000; 
  width: 100%;
  /* 如果你在电脑宽屏上看，加上 max-width 可以让它像手机一样居中显示 */
  max-width: 800px;
  margin: 0 auto;
}

:deep(.van-nav-bar) { position: relative; z-index: 99; }

.video-box { 
  flex: 1; 
  position: relative; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  background: #111; 
  overflow: hidden; 
}

/* 让画布铺满容器，并保持比例剪裁 */
.ai-canvas { 
  width: 100%; 
  height: 100%; 
  object-fit: cover; 
  transform: scaleX(-1); 
}

/* 玻璃态数据悬浮窗 */
.stats-overlay { 
  position: absolute; 
  top: 16px; 
  right: 16px; 
  background: rgba(0,0,0,0.6); 
  backdrop-filter: blur(8px);
  padding: 16px; 
  border-radius: 12px; 
  color: #fff; 
  border: 1px solid rgba(25, 137, 250, 0.3); 
  min-width: 130px; 
  z-index: 10;
}

.stat-item { margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;}
.label { font-size: 12px; color: #ccc; }
.count { color: #1989fa; font-weight: 900; font-size: 24px; }
.status-tag { color: #07c160; font-weight: bold; }
.feedback-mini { border-top: 1px solid #333; padding-top: 8px; font-size: 12px; color: #ff976a; text-align: center; display: block;}

/* 底部控制台 */
.control-panel { 
  padding: 20px; 
  background: #fff; 
  border-radius: 24px 24px 0 0; 
  position: relative; 
  z-index: 99;
}

.feedback-main { 
  text-align: center; 
  color: #1989fa; 
  font-weight: 900; 
  font-size: 20px; 
  margin-bottom: 20px; 
  text-transform: uppercase; 
  letter-spacing: 1px;
}

.button-group { display: flex; gap: 12px; }
</style>