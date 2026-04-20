<template>
  <div class="workout-container" ref="containerRef">
    <van-nav-bar 
      title="AI 实时训练" 
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
          停止训练
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
      teleport=".workout-container"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { showToast, showFailToast, showLoadingToast } from 'vant';

const router = useRouter();
const authStore = useAuthStore();

const containerRef = ref(null); 
const videoRef = ref(null);
const canvasRef = ref(null);
const isTraining = ref(false);
let ws = null;
let timer = null;

const showPicker = ref(false);
const selectedExerciseCode = ref('SQUAT'); 

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
  stage: 'WAITING',
  feedback: ''
});

// --- 全屏控制逻辑 ---
const toggleFullScreen = () => {
  if (!document.fullscreenElement) {
    if (containerRef.value.requestFullscreen) {
      containerRef.value.requestFullscreen();
    } else if (containerRef.value.webkitRequestFullscreen) { 
      containerRef.value.webkitRequestFullscreen();
    }
    showToast('已进入全屏');
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    }
  }
};

const startTraining = async () => {
  const loading = showLoadingToast({ message: '引擎点火...', forbidClick: true });

  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const videoDevices = devices.filter(device => device.kind === 'videoinput');
    const realCamera = videoDevices.find(d => !d.label.includes('DroidCam')) || videoDevices[0];

    const constraints = { 
      video: { 
        deviceId: realCamera?.deviceId ? { exact: realCamera.deviceId } : undefined,
        width: { ideal: 1280 },
        height: { ideal: 720 }
      } 
    };

    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    
    if (videoRef.value) {
      videoRef.value.srcObject = stream;
      await videoRef.value.play(); 
      
      isTraining.value = true;
      initWebSocket();
      loading.close();
    }
  } catch (err) {
    loading.close();
    showFailToast('摄像头开启失败');
  }
};

const initWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws?token=${authStore.token}&exercise=${selectedExerciseCode.value}`;
  
  ws = new WebSocket(wsUrl);
  ws.onopen = () => showToast(`正在进行 ${currentExerciseName.value} 训练`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    exerciseInfo.counter = data.counter;
    exerciseInfo.stage = data.stage;
    exerciseInfo.feedback = data.feedback;

    if (data.image && canvasRef.value) {
      const ctx = canvasRef.value.getContext('2d');
      const img = new Image();
      img.onload = () => {
        canvasRef.value.width = img.width;
        canvasRef.value.height = img.height;
        ctx.drawImage(img, 0, 0);
      };
      img.src = data.image.startsWith('data:image') ? data.image : 'data:image/jpeg;base64,' + data.image;
    }
  };
  
  sendFrames();
};

const sendFrames = () => {
  const offCanvas = document.createElement('canvas');
  const ctx = offCanvas.getContext('2d');
  
  timer = setInterval(() => {
    if (isTraining.value && videoRef.value && ws?.readyState === WebSocket.OPEN) {
      const vw = videoRef.value.videoWidth;
      const vh = videoRef.value.videoHeight;
      
      if (vw > 0 && vh > 0) {
        const maxSide = 640;
        const scale = Math.min(maxSide / vw, maxSide / vh);
        
        offCanvas.width = vw * scale;
        offCanvas.height = vh * scale;

        ctx.drawImage(videoRef.value, 0, 0, offCanvas.width, offCanvas.height);
        
        const rawData = offCanvas.toDataURL('image/jpeg', 0.3).split(',')[1];
        ws.send(rawData);
      }
    }
  }, 150);
};

// --- 【关键恢复】：被误删的 stopTraining 函数 ---
const stopTraining = () => {
  isTraining.value = false;
  if (timer) clearInterval(timer);
  if (ws) ws.close();
  if (videoRef.value?.srcObject) {
    videoRef.value.srcObject.getTracks().forEach(track => track.stop());
  }
};

// --- 【新增】：处理导航栏返回按钮的逻辑 ---
const stopTrainingAndBack = () => {
  stopTraining();
  router.back();
};

onUnmounted(() => stopTraining());
</script>

<style scoped>
/* 全屏时的背景处理 */
.workout-container { 
  height: 100vh; 
  display: flex; 
  flex-direction: column; 
  background-color: #000; 
  width: 100%;
}

/* --- 【关键 CSS 修复】：确保导航栏在最上层 --- */
:deep(.van-nav-bar) {
  position: relative;
  z-index: 99; 
}

.video-box { 
  flex: 1; 
  position: relative; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  background: #000; 
  overflow: hidden; 
}

.ai-canvas { 
  width: 100%; 
  height: 100%; 
  object-fit: cover; 
  transform: scaleX(-1); 
}

.stats-overlay { 
  position: absolute; 
  top: 16px; 
  right: 16px; 
  background: rgba(0,0,0,0.75); 
  padding: 16px; 
  border-radius: 12px; 
  color: #fff; 
  border: 1px solid #1989fa;
  min-width: 130px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  z-index: 10;
}
.stat-item { margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;}
.label { font-size: 12px; color: #bbb; }
.count { color: #1989fa; font-weight: 900; font-size: 24px; }
.status-tag { color: #07c160; font-weight: bold; }
.feedback-mini { border-top: 1px solid #333; padding-top: 8px; font-size: 12px; color: #ff976a; text-align: center; display: block;}

/* --- 【关键 CSS 修复】：确保控制台在最上层 --- */
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