<template>
  <div class="bg-[#0f1115] text-white h-screen w-full flex flex-col overflow-hidden max-w-300 mx-auto antialiased relative font-sans">
    
    <main class="flex-1 relative w-full overflow-hidden bg-black">
      <video 
        ref="videoRef" 
        autoplay 
        playsinline 
        muted 
        class="absolute inset-0 w-full h-full object-cover opacity-60"
        :style="isTestingVideo ? '' : 'transform: scaleX(-1);'"
      ></video>
      <canvas 
        ref="canvasRef" 
        class="absolute inset-0 w-full h-full object-cover z-10"
        :style="isTestingVideo ? '' : 'transform: scaleX(-1);'"
      ></canvas>
      
      <div v-if="exerciseInfo.isWarning" class="absolute inset-0 border-[6px] border-red-600 bg-red-600/10 pointer-events-none z-20 animate-pulse"></div>

      <header class="absolute top-0 w-full px-4 py-4 flex justify-between items-center z-30">
        <button @click="stopTrainingAndBack" class="w-10 h-10 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center text-white hover:bg-white/20 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
        
        <div v-if="isTraining" class="px-4 py-1.5 rounded-full bg-black/40 backdrop-blur-md border flex items-center gap-2" :class="exerciseInfo.isWarning ? 'border-red-500' : 'border-white/10'">
          <span class="w-2 h-2 rounded-full animate-pulse" :class="exerciseInfo.isWarning ? 'bg-red-500' : 'bg-green-500'"></span>
          <span class="text-[10px] font-bold tracking-widest uppercase">{{ exerciseInfo.isWarning ? 'RISK DETECTED' : 'REC ACTIVE' }}</span>
        </div>

        <button @click="toggleFullScreen" class="w-10 h-10 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 3 6 6M9 21l-6-6M21 3l-6 6M3 21l6-6"/></svg>
        </button>
      </header>

      <div class="absolute top-20 right-4 z-30 flex flex-col items-end gap-2 pointer-events-none">
        <div class="px-4 py-2 rounded-2xl backdrop-blur-xl border-2 flex items-center gap-3 shadow-2xl transition-colors duration-300"
             :class="exerciseInfo.stage === 'UP' ? 'bg-blue-600/80 border-blue-400' : 'bg-orange-500/80 border-orange-300'">
          <div class="flex flex-col items-center justify-center">
            <svg v-if="exerciseInfo.stage === 'UP'" xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="text-white mb-1"><path d="m18 15-6-6-6 6"/></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="text-white mt-1"><path d="m6 9 6 6 6-6"/></svg>
          </div>
          <span class="text-2xl font-black text-white tracking-widest">{{ exerciseInfo.stage }}</span>
        </div>
      </div>

      <Transition name="bounce">
        <div v-if="exerciseInfo.isWarning" class="absolute top-1/4 left-1/2 -translate-x-1/2 w-[90%] max-w-sm z-40">
          <div class="bg-red-600/90 backdrop-blur-xl border-2 border-red-400 rounded-3xl px-6 py-5 flex flex-col items-center gap-3 shadow-[0_0_40px_rgba(220,38,38,0.6)] text-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-white"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
            <p class="text-lg font-black text-white tracking-wide">{{ exerciseInfo.feedback }}</p>
          </div>
        </div>
      </Transition>

      <div class="absolute bottom-6 left-4 right-4 z-30 flex justify-between items-end">
        <div class="flex flex-col gap-3">
          <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-600/80 backdrop-blur-md border border-blue-400/30 shadow-lg w-fit">
            <span class="text-[10px] font-bold text-white tracking-widest uppercase">AI 识别: {{ currentExerciseName.split(' ')[0] }}</span>
          </div>
          
          <div class="flex items-end gap-4">
            <div class="flex items-baseline drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]">
              <span class="text-7xl font-bold text-blue-500 leading-none tabular-nums">{{ exerciseInfo.counter }}</span>
              <span class="text-2xl font-bold text-white/90 ml-3 uppercase">次</span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <section class="bg-[#1a1c22] border-t border-white/5 rounded-t-4xl p-4 pt-2 shadow-2xl z-40">
      <div class="w-full flex justify-center py-3"><div class="w-12 h-1.5 bg-white/10 rounded-full"></div></div>

      <div class="w-full overflow-x-auto no-scrollbar pb-6 pt-2">
        <div class="flex gap-2 w-max px-2">
          <button
            v-for="ex in exerciseOptions"
            :key="ex.value"
            @click="onSelectExercise(ex)"
            :disabled="isTraining"
            :class="[
              'px-6 py-2.5 rounded-full font-bold text-xs transition-all active:scale-95 whitespace-nowrap',
              selectedExerciseCode === ex.value ? 'bg-blue-600 text-white shadow-lg' : 'bg-white/5 text-white/60'
            ]"
          >
            {{ ex.name }}
          </button>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3 pb-6">
        <input type="file" accept="video/*" class="hidden" ref="fileInputRef" @change="startVideoTest" />
        <button v-if="!isTraining" @click="$refs.fileInputRef.click()" :disabled="!isModelLoaded" class="flex flex-col items-center justify-center gap-1 w-16 h-16 rounded-2xl bg-white/5 text-blue-400 hover:bg-white/10">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          <span class="text-[9px] font-bold mt-1">视频测</span>
        </button>
        
        <button v-if="!isTraining" @click="startTraining" :disabled="!isModelLoaded" class="flex-1 h-16 bg-blue-600 disabled:bg-blue-900/50 text-white rounded-3xl font-bold text-lg flex items-center justify-center gap-2 shadow-xl shadow-blue-900/20">
          <span v-if="!isModelLoaded" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          {{ isModelLoaded ? '实时摄像头检测' : '引擎预热' }}
        </button>

        <button v-else @click="stopTraining" class="flex-1 h-16 bg-red-600 text-white rounded-3xl font-bold text-lg flex items-center justify-center shadow-xl shadow-red-900/20">
          停止并保存
        </button>

        <button @click="router.push('/history')" class="flex flex-col items-center justify-center gap-1 w-16 h-16 rounded-2xl bg-white/5 text-white/80 hover:bg-white/10">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>
          <span class="text-[9px] font-bold mt-1">历史</span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { showToast, showLoadingToast, showSuccessToast, showFailToast } from 'vant';
import axios from 'axios';

// 全局变量接管
const Pose = window.Pose || null;
const POSE_CONNECTIONS = window.POSE_CONNECTIONS || null;
const Camera = window.Camera || null;
const drawConnectors = window.drawConnectors || null;
const drawLandmarks = window.drawLandmarks || null;

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const videoRef = ref(null);
const canvasRef = ref(null);
const fileInputRef = ref(null);

const isTraining = ref(false);
const isTestingVideo = ref(false);
const isModelLoaded = ref(false);
let poseModel = null;
let camera = null;
let animationFrameId = null;

const selectedExerciseCode = ref(route.query.exercise || 'SQUAT'); 

const exerciseOptions = [
  { name: '深蹲 Squat', value: 'SQUAT' },
  { name: '二头弯举 Curl', value: 'BICEP_CURL' },
  { name: '硬拉 Deadlift', value: 'DEADLIFT' },
  { name: '俯卧撑 PushUp', value: 'PUSH_UP' },
  { name: '卧推 Bench', value: 'BENCH_PRESS' }
];

const currentExerciseName = computed(() => {
  const target = exerciseOptions.find(opt => opt.value === selectedExerciseCode.value);
  return target ? target.name : '未知动作';
});

// 新增：系统动态特征库 (用于 1.5 sigma 疲劳与基准线检测)
const userBaselines = reactive({
  squatDepthHistory: [],
  spineBaseAngle: null,
  stageHoldFrames: 0 // 用于时间序列状态机防抖
});

const onSelectExercise = (action) => {
  selectedExerciseCode.value = action.value;
  exerciseInfo.name = action.value; 
  exerciseInfo.counter = 0; 
  resetBaselines();
};

const resetBaselines = () => {
  userBaselines.squatDepthHistory = [];
  userBaselines.spineBaseAngle = null;
  userBaselines.stageHoldFrames = 0;
};

const exerciseInfo = reactive({
  name: selectedExerciseCode.value,
  counter: 0,
  stage: 'UP', 
  feedback: '准备就绪',
  isWarning: false
});

const detectedIssues = new Set();
const synth = window.speechSynthesis;
let lastSpokenText = ''; 

const speakFeedback = (text, isWarning = false) => {
  if (text === lastSpokenText || !text) return;
  synth.cancel(); 
  const utterThis = new SpeechSynthesisUtterance(text);
  utterThis.lang = 'zh-CN'; 
  utterThis.rate = isWarning ? 1.4 : 1.1; 
  utterThis.pitch = isWarning ? 1.2 : 1.0;
  synth.speak(utterThis);
  lastSpokenText = text;
};

// --- 基础数学与几何计算 ---
const calculateAngle = (a, b, c) => {
  const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
  let angle = Math.abs((radians * 180.0) / Math.PI);
  return angle > 180.0 ? 360 - angle : angle;
};

const calculateRelativeAngle = (axis1Start, axis1End, axis2Start, axis2End) => {
  const v1 = { x: axis1End.x - axis1Start.x, y: axis1End.y - axis1Start.y };
  const v2 = { x: axis2End.x - axis2Start.x, y: axis2End.y - axis2Start.y };
  const dot = v1.x * v2.x + v1.y * v2.y;
  const mag1 = Math.sqrt(v1.x * v1.x + v1.y * v1.y);
  const mag2 = Math.sqrt(v2.x * v2.x + v2.y * v2.y);
  return Math.acos(dot / (mag1 * mag2)) * (180.0 / Math.PI);
};

const getDistance = (p1, p2) => Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));

// 统计学：标准差计算
const calculateStdDev = (arr) => {
  if(arr.length < 2) return 0;
  const mean = arr.reduce((a, b) => a + b) / arr.length;
  return Math.sqrt(arr.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / (arr.length - 1));
};

let lastAngle = 0; let lastVelocity = 0; let lastTime = 0;
const getRealtimeAcceleration = (currentAngle) => {
  const now = performance.now();
  if (lastTime === 0) { lastTime = now; return 0; }
  const dt = (now - lastTime) / 1000;
  if (dt === 0) return 0;
  const velocity = (currentAngle - lastAngle) / dt;
  const acceleration = Math.abs(velocity - lastVelocity) / dt;
  lastAngle = currentAngle; lastVelocity = velocity; lastTime = now;
  return acceleration;
};

const landmarkBuffer = {};
const getSmoothPoint = (index, point) => {
  if (!point) return { x: 0, y: 0, z: 0, visibility: 0 };
  if (!landmarkBuffer[index]) landmarkBuffer[index] = [];
  landmarkBuffer[index].push(point);
  if (landmarkBuffer[index].length > 5) landmarkBuffer[index].shift();
  const sum = landmarkBuffer[index].reduce((a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + (b.z||0), visibility: a.visibility + (b.visibility||0) }), { x: 0, y: 0, z: 0, visibility: 0 });
  const len = landmarkBuffer[index].length;
  return { x: sum.x / len, y: sum.y / len, z: sum.z / len, visibility: sum.visibility / len };
};

// --- 高级生物力学核心处理 ---
const processExerciseLogic = (lm) => {
  exerciseInfo.isWarning = false;
  
  // 提取全身关键点
  const earL = getSmoothPoint(7, lm[7]), earR = getSmoothPoint(8, lm[8]); // 头部用于颈部代偿
  const shL = getSmoothPoint(11, lm[11]), shR = getSmoothPoint(12, lm[12]);
  const elL = getSmoothPoint(13, lm[13]), elR = getSmoothPoint(14, lm[14]);
  const wrL = getSmoothPoint(15, lm[15]), wrR = getSmoothPoint(16, lm[16]);
  const hipL = getSmoothPoint(23, lm[23]), hipR = getSmoothPoint(24, lm[24]);
  const knL = getSmoothPoint(25, lm[25]), knR = getSmoothPoint(26, lm[26]);
  const anL = getSmoothPoint(27, lm[27]), anR = getSmoothPoint(28, lm[28]);
  const toeL = getSmoothPoint(31, lm[31]), toeR = getSmoothPoint(32, lm[32]); // 脚趾用于支撑面

  const midHip = { x: (hipL.x + hipR.x) / 2, y: (hipL.y + hipR.y) / 2 };
  const midSh = { x: (shL.x + shR.x) / 2, y: (shL.y + shR.y) / 2 };

  // 智能侧位选择：取置信度更高的一侧
  const isLeftVisible = (lm[13]?.visibility || 0) > (lm[14]?.visibility || 0);
  const activeEar = isLeftVisible ? earL : earR;
  const activeSh = isLeftVisible ? shL : shR;
  const activeEl = isLeftVisible ? elL : elR;
  const activeWr = isLeftVisible ? wrL : wrR;
  const activeHip = isLeftVisible ? hipL : hipR;
  const activeKn = isLeftVisible ? knL : knR;
  const activeAn = isLeftVisible ? anL : anR;
  const activeToe = isLeftVisible ? toeL : toeR;

  switch (selectedExerciseCode.value) {
    case 'SQUAT': {
      // 1. 膝关节内扣检测
      const valgusRatio = getDistance(knL, knR) / getDistance(hipL, hipR);
      if (valgusRatio < 0.7) triggerWarning('膝盖打开', '警告：膝关节严重内扣');
      
      // 2. 底部反弹预警
      const kneeAngle = calculateAngle(activeHip, activeKn, activeAn);
      if (kneeAngle < 100 && getRealtimeAcceleration(kneeAngle) > 800) triggerWarning('放慢速度', '警告：底部反弹冲击过大');

      // 3. 补全：3D 重心失稳检测 (COM/COP)
      // 计算二维投影重心 (近似)，若重心X坐标超出脚跟到脚尖的范围 (BOS)，判定失衡
      const comX = (activeSh.x * 0.4 + activeHip.x * 0.4 + activeKn.x * 0.2);
      const bosMin = Math.min(activeAn.x, activeToe.x) - 0.05; // 预留5%缓冲
      const bosMax = Math.max(activeAn.x, activeToe.x) + 0.05;
      if (comX < bosMin || comX > bosMax) triggerWarning('控制重心', '警告：身体重心偏移，失去平衡');
      
      // 4. 补全：动态误差容忍度 (1.5 Sigma 深度衰减)
      if (kneeAngle < 100) {
        if (!userBaselines.squatDepthHistory.includes(kneeAngle)) {
           userBaselines.squatDepthHistory.push(kneeAngle);
           if(userBaselines.squatDepthHistory.length > 10) userBaselines.squatDepthHistory.shift();
        }
      }
      
      if (userBaselines.squatDepthHistory.length > 3) {
        const avgDepth = userBaselines.squatDepthHistory.reduce((a,b)=>a+b)/userBaselines.squatDepthHistory.length;
        const stdDev = calculateStdDev(userBaselines.squatDepthHistory);
        // 如果当前最低点比历史平均最低点浅了 1.5个标准差以上，说明出现代偿变浅
        if (kneeAngle > 100 && kneeAngle < 120 && exerciseInfo.stage === 'DOWN' && (kneeAngle - avgDepth) > (1.5 * stdDev + 10)) {
           triggerWarning('蹲深一点', '警告：疲劳导致动作幅度(ROM)衰减');
        }
      }

      // 时间序列对齐 (S-DTW 轻量替代：状态防抖)
      if (kneeAngle < 90) {
        userBaselines.stageHoldFrames++;
        if(userBaselines.stageHoldFrames > 3 && exerciseInfo.stage === 'UP') { exerciseInfo.stage = 'DOWN'; userBaselines.stageHoldFrames = 0;}
      } else if (kneeAngle > 150) {
        userBaselines.stageHoldFrames++;
        if(userBaselines.stageHoldFrames > 3 && exerciseInfo.stage === 'DOWN') { completeRep(); userBaselines.stageHoldFrames = 0; }
      } else {
        userBaselines.stageHoldFrames = 0;
      }
      break;
    }
    
    case 'BENCH_PRESS': {
      const flareAngle = calculateRelativeAngle(midHip, midSh, shL, elL);
      if (flareAngle > 70) triggerWarning('收紧手肘', '警告：手肘外展过度 (肩峰撞击)');
      
      const gripRatio = getDistance(wrL, wrR) / getDistance(shL, shR);
      if (gripRatio > 1.5) triggerWarning('缩窄握距', '警告：握距过宽');
      
      const pressAngle = calculateAngle(shL, elL, wrL);
      if (pressAngle < 80 && exerciseInfo.stage === 'UP') exerciseInfo.stage = 'DOWN';
      else if (pressAngle > 150 && exerciseInfo.stage === 'DOWN') completeRep();
      break;
    }

    case 'DEADLIFT': {
      const spineAngle = calculateAngle(activeSh, activeHip, activeAn);
      if (!userBaselines.spineBaseAngle && spineAngle > 0) userBaselines.spineBaseAngle = spineAngle;
      if (userBaselines.spineBaseAngle && Math.abs(spineAngle - userBaselines.spineBaseAngle) > 10) {
        triggerWarning('背部挺直', '警告：组内脊柱发生疲劳弯曲 (韧带拉伸)');
      }
      
      const shinLength = getDistance(activeKn, activeAn);
      if (Math.abs(activeWr.x - activeAn.x) > shinLength * 0.2) triggerWarning('杠铃贴紧小腿', '警告：杠铃偏离力学中心');
      
      const liftAngle = calculateAngle(activeSh, activeHip, activeKn);
      if (liftAngle < 70 && exerciseInfo.stage === 'UP') exerciseInfo.stage = 'DOWN';
      else if (liftAngle > 150 && exerciseInfo.stage === 'DOWN') completeRep();
      break;
    }

    case 'PUSH_UP': {
      // 1. 核心塌陷
      const coreAngle = calculateAngle(activeSh, activeHip, activeAn);
      if (coreAngle < 160) triggerWarning('收紧核心', '警告：核心塌陷 (腰椎受压)');
      
      // 2. 补全：颈部前伸代偿 (Neck Compensation)
      const trunkLength = getDistance(activeSh, activeHip);
      // 计算耳屏点相对于肩峰的水平前移量 (归一化到躯干长度)
      const neckProtrusion = Math.abs(activeEar.x - activeSh.x) / trunkLength;
      if (neckProtrusion > 0.25) triggerWarning('头部收回', '警告：颈部前伸虚假触底');
      
      const pushAngle = calculateAngle(activeSh, activeEl, activeWr);
      if (pushAngle < 90 && exerciseInfo.stage === 'UP') exerciseInfo.stage = 'DOWN';
      else if (pushAngle > 150 && exerciseInfo.stage === 'DOWN') completeRep();
      break;
    }

    case 'BICEP_CURL': {
      // 1. 躯干摇摆
      const trunkAngle = calculateAngle(activeSh, activeHip, { x: activeHip.x, y: activeHip.y - 1 });
      if (trunkAngle > 15) triggerWarning('身体不要晃', '警告：躯干后仰借力');
      
      // 2. 补全：前三角肌代偿 (Anterior Deltoid Compensation)
      // 计算大臂(肩到肘)与躯干(肩到髋)的夹角。正常孤立弯举大臂应贴紧躯干。
      const shoulderFlexionAngle = calculateAngle(activeHip, activeSh, activeEl);
      if (shoulderFlexionAngle > 35 && exerciseInfo.stage === 'DOWN') {
        triggerWarning('大臂贴紧身体', '警告：大臂前抬 (前三角肌代偿发力)');
      }

      const curlAngle = calculateAngle(activeSh, activeEl, activeWr);
      if (curlAngle < 40 && exerciseInfo.stage === 'DOWN') exerciseInfo.stage = 'UP';
      else if (curlAngle > 140 && exerciseInfo.stage === 'UP') {
        exerciseInfo.stage = 'DOWN';
        completeRep(); 
      }
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
  exerciseInfo.feedback = '动作标准';
  speakFeedback(exerciseInfo.counter.toString());
};

const onResults = (results) => {
  if (!canvasRef.value) return;
  const canvasCtx = canvasRef.value.getContext('2d');
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
  if (results.poseLandmarks) {
    drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, { color: '#3b82f6', lineWidth: 4 });
    drawLandmarks(canvasCtx, results.poseLandmarks, { color: '#ffffff', lineWidth: 1, radius: 3 });
    processExerciseLogic(results.poseLandmarks);
  }
  canvasCtx.restore();
};

const initAIModel = async () => {
  if (!Pose) return;
  poseModel = new Pose({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}` });
  poseModel.setOptions({ modelComplexity: 1, smoothLandmarks: true, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
  poseModel.onResults(onResults);
  await poseModel.initialize();
  isModelLoaded.value = true;
};

const startVideoTest = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  isTestingVideo.value = true;
  isTraining.value = true;
  exerciseInfo.counter = 0;
  exerciseInfo.stage = selectedExerciseCode.value === 'BICEP_CURL' ? 'DOWN' : 'UP';
  detectedIssues.clear();
  resetBaselines();
  lastTime = 0;

  const url = URL.createObjectURL(file);
  videoRef.value.src = url;
  videoRef.value.loop = true; 
  videoRef.value.play();

  const processFrame = async () => {
    if (!isTraining.value || !isTestingVideo.value) return;
    if (videoRef.value.readyState >= 2 && poseModel) {
      if (canvasRef.value.width !== videoRef.value.videoWidth) {
        canvasRef.value.width = videoRef.value.videoWidth;
        canvasRef.value.height = videoRef.value.videoHeight;
      }
      await poseModel.send({ image: videoRef.value });
    }
    animationFrameId = requestAnimationFrame(processFrame);
  };
  processFrame();
};

const startTraining = async () => {
  if (!poseModel || !Camera) return;
  isTestingVideo.value = false;
  isTraining.value = true;
  exerciseInfo.counter = 0;
  exerciseInfo.stage = selectedExerciseCode.value === 'BICEP_CURL' ? 'DOWN' : 'UP';
  detectedIssues.clear(); 
  resetBaselines();
  lastTime = 0; 

  if (videoRef.value) {
    camera = new Camera(videoRef.value, {
      onFrame: async () => {
        if (!isTestingVideo.value && canvasRef.value && videoRef.value) {
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
  if (animationFrameId) { cancelAnimationFrame(animationFrameId); animationFrameId = null; }
  if (videoRef.value) { videoRef.value.pause(); videoRef.value.src = ''; }
  
  const issueSummary = Array.from(detectedIssues).join(' | ');
  try {
    showLoadingToast('分析中...');
    await axios.post('/api/records', {
      exercise_type: selectedExerciseCode.value,
      count: exerciseInfo.counter,
      issues: issueSummary 
    }, { headers: { Authorization: `Bearer ${authStore.token}` } });
    showSuccessToast('记录已保存');
    router.push('/history');
  } catch (error) {
    showFailToast('保存失败，请检查网络');
  }
};

const stopTrainingAndBack = () => {
  if (isTraining.value) stopTraining();
  else router.back();
};

const toggleFullScreen = () => {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen();
  else document.exitFullscreen();
};

onMounted(() => {
  synth.getVoices(); 
  initAIModel(); 
});

onUnmounted(() => {
  if (camera) camera.stop();
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  if (poseModel) poseModel.close();
});
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

.bounce-enter-active { animation: bounce-in 0.4s; }
.bounce-leave-active { animation: bounce-in 0.3s reverse; }
@keyframes bounce-in {
  0% { transform: translate(-50%, -20px) scale(0.9); opacity: 0; }
  50% { transform: translate(-50%, 5px) scale(1.05); opacity: 1; }
  100% { transform: translate(-50%, 0) scale(1); opacity: 1; }
}

@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700;900&display=swap');
.font-sans { font-family: 'Lexend', system-ui, -apple-system, sans-serif; }
</style>