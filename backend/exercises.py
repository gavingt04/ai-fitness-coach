# exercises.py  ── v3.0  3D世界坐标版本
# ================================================================
# 核心架构升级：
#   1. 所有角度计算切换至 MediaPipe 3D 世界坐标 (pose_world_landmarks)
#      → 正面/侧面/45度视角均能正确测量真实关节弯曲角度
#   2. 稳定门控改为"最优单侧"策略
#      → 只要左/右 任意一侧 可见度达标即可通过，解决侧视图永远卡住的问题
#   3. 解剖合法性检查（3D坐标）
#      → 骨架被器械遮挡/定位错误时，自动丢弃异常帧
# ================================================================
import numpy as np
import cv2
import time


# ──────────────────────────────────────────────
#  角度计算工具函数
# ──────────────────────────────────────────────
def calculate_angle_3d(a, b, c):
    """
    【核心修复】使用3D世界坐标计算三点夹角。
    输入 a/b/c 均为 (x, y, z) 元组，单位：米。
    无论摄像头角度如何（正面、侧面、45°），
    返回值等于关节的真实解剖弯曲角度。
    """
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)
    ba = a - b
    bc = c - b
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return 180.0
    cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    return float(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0))))


def calculate_angle_2d(a, b, c):
    """2D投影角度计算（仅用于world_lm缺失时的回退）"""
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = (np.arctan2(c[1]-b[1], c[0]-b[0])
               - np.arctan2(a[1]-b[1], a[0]-b[0]))
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180.0 else angle


def wpt(lm, i):
    """从 world_landmarks 提取第 i 点的 (x, y, z) 坐标"""
    return (lm[i].x, lm[i].y, lm[i].z)


# ──────────────────────────────────────────────
#  公共基类
# ──────────────────────────────────────────────
class BaseExercise:
    """
    所有动作类基类。
    核心机制：
      - 最优单侧稳定门控：只要左/右任一侧骨骼点可见度达标就允许进入识别
      - 解剖异常帧计数：连续多帧骨架定位错误时给出提示并跳过计算
    """
    BUFFER_SIZE = 5
    STABLE_FRAMES_NEEDED = 10
    MIN_VISIBILITY = 0.50
    MAX_INVALID_STREAK = 5   # 连续N帧解剖异常则显示警告

    def __init__(self):
        self.counter = 0
        self.stage = "UP"
        self.feedback = "Ready"
        # ---- 新增：警告驻留机制 ----
        self.warning_text = ""
        self.warning_expire_time = 0.0
        self.WARNING_DURATION = 2.0  # 警告强制显示 2 秒

    def set_warning(self, text):
        """触发一个强制驻留的警告"""
        self.warning_text = text
        self.warning_expire_time = time.time() + self.WARNING_DURATION

    def get_current_feedback(self, default_feedback):
        """获取当前应显示的反馈文本（优先显示未过期的警告）"""
        if time.time() < self.warning_expire_time:
            return f"⚠ {self.warning_text}"
        return default_feedback

    # ── 2D平滑缓冲（仅用于OSD显示坐标，不参与角度计算）
    def smooth2d(self, index, x, y):
        buf = self.landmark_buffer.setdefault(index, [])
        buf.append([x, y])
        if len(buf) > self.BUFFER_SIZE:
            buf.pop(0)
        return np.mean(buf, axis=0)

    # ── 最优单侧可见度检查
    def _best_side_vis(self, landmarks, left_idx, right_idx):
        l = min(landmarks[i].visibility for i in left_idx)
        r = min(landmarks[i].visibility for i in right_idx)
        return max(l, r)

    # ── 稳定门控更新（快降慢升）
    def update_gate(self, landmarks, left_idx, right_idx):
        vis = self._best_side_vis(landmarks, left_idx, right_idx)
        if vis >= self.MIN_VISIBILITY:
            self.stable_frames = min(self.stable_frames + 1,
                                     self.STABLE_FRAMES_NEEDED)
        else:
            self.stable_frames = max(self.stable_frames - 1, 0)
        self.is_ready = (self.stable_frames >= self.STABLE_FRAMES_NEEDED)
        return self.is_ready

    # ── OSD渲染
    def draw_osd(self, frame, title, stage_color=(0, 255, 0)):
        cv2.rectangle(frame, (0, 0), (540, 165), (0, 0, 0), -1)
        cv2.putText(frame, f"{title}: {self.counter}", (20, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, f"STAGE: {self.stage}", (20, 93),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, stage_color, 2, cv2.LINE_AA)
        cv2.putText(frame, self.feedback, (20, 138),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2, cv2.LINE_AA)

    def draw_calibrating(self, frame, title):
        h, w, _ = frame.shape
        bar_w = int(w * 0.6 * self.stable_frames / self.STABLE_FRAMES_NEEDED)
        cv2.rectangle(frame, (0, 0), (540, 165), (0, 0, 0), -1)
        cv2.putText(frame, f"{title}: {self.counter}", (20, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, "CALIBRATING...", (20, 93),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2, cv2.LINE_AA)
        cv2.rectangle(frame, (20, 110), (20 + int(w * 0.6), 132), (50, 50, 50), -1)
        cv2.rectangle(frame, (20, 110), (20 + bar_w, 132), (0, 200, 255), -1)
        cv2.putText(frame, f"骨骼点校准中 {self.stable_frames}/{self.STABLE_FRAMES_NEEDED}",
                    (20, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (200, 200, 200), 1, cv2.LINE_AA)


# ──────────────────────────────────────────────
#  深蹲
# ──────────────────────────────────────────────
class Squat(BaseExercise):
    """
    修复清单：
      ✅ Bug1  启动乱跳  → 最优单侧稳定门控
      ✅ Bug2  膝盖内扣  → 3D世界坐标膝踝横向比较，消除2D投影误差
      ✅ Bug3  正面不计数 → 3D角度彻底无视相机朝向
      ✅ Bug4  有杠铃骨架偏移  → 解剖合法性检查丢弃异常帧
      ✅ Bug5  45度/背面不计数 → 同Bug3
    """
    # MediaPipe世界坐标：x轴向右(正)，以髋部中心为原点，单位：米
    VALGUS_THRESHOLD = 0.05   # 膝盖相对踝关节向内偏移 5cm 触发内扣警告

    def __init__(self):
        super().__init__()
        self.stage = "UP"
        self.feedback = "Ready for Squat"
        self.last_progress_time = 0
        self.highest_angle = 0
        self.timeout_threshold = 3.0
        self.valgus_active = False
        self.last_count_time = 0
        self.COOLDOWN_PERIOD = 1.0 # 强制 1 秒冷却

    # 修改 exercises.py 中的 Squat._get_angle_3d
def _get_angle_3d(self, wlm, landmarks): # 传入原始 landmarks 获取可见度
    def side(h, k, a):
        if not (wlm[h].y > wlm[k].y > wlm[a].y):
            return None
        return calculate_angle_3d(wpt(wlm, h), wpt(wlm, k), wpt(wlm, a))

    l_angle = side(23, 25, 27)
    r_angle = side(24, 26, 28)

    # 获取左右膝盖的可见度分数
    l_vis = landmarks[25].visibility
    r_vis = landmarks[26].visibility

    if l_angle is None and r_angle is None:
        return None

    # 如果一侧可见度明显高于另一侧（侧拍场景），直接采信清晰的一侧
    if l_angle is not None and r_angle is not None:
        if l_vis > r_vis + 0.1: # 阈值可调，0.1表示明显更清晰
            return l_angle
        elif r_vis > l_vis + 0.1:
            return r_angle
        return (l_angle + r_angle) / 2.0 # 只有双腿都清晰时才平均
    
    return l_angle if l_angle is not None else r_angle

    def _check_valgus_3d(self, wlm):
        """
        3D世界坐标内扣检测。
        正常姿势：膝盖在踝关节外侧（左膝x < 左踝x，右膝x > 右踝x）。
        内扣时：膝盖越过踝关节向内侧移动。
        """
        # Left knee caves right (inward toward midline)
        l_valgus = (wlm[25].x - wlm[27].x) > self.VALGUS_THRESHOLD
        # Right knee caves left (inward toward midline)
        r_valgus = (wlm[28].x - wlm[26].x) > self.VALGUS_THRESHOLD
        return l_valgus or r_valgus

    def process_frame(self, landmarks, world_lm, frame):
        h, w, _ = frame.shape

        # ① 最优单侧稳定门控
        if not self.update_gate(landmarks, [23, 25, 27], [24, 26, 28]):
            self.draw_calibrating(frame, "SQUATS")
            return frame

        # ② 3D角度（world_lm缺失时回退2D）
        if world_lm is not None:
            angle = self._get_angle_3d(world_lm)
        else:
            hip  = self.smooth2d(23, landmarks[23].x * w, landmarks[23].y * h)
            knee = self.smooth2d(25, landmarks[25].x * w, landmarks[25].y * h)
            ankle= self.smooth2d(27, landmarks[27].x * w, landmarks[27].y * h)
            angle = calculate_angle_2d(hip, knee, ankle)

        # ③ 解剖异常帧处理
        if angle is None:
            self.invalid_streak += 1
            if self.invalid_streak > self.MAX_INVALID_STREAK:
                self.feedback = "⚠ 请调整站位 / 器械遮挡"
            self.draw_osd(frame, "SQUATS", (0, 165, 255))
            return frame
        self.invalid_streak = 0

        # ④ 膝盖内扣检测（3D）
        if world_lm is not None:
            self.valgus_active = self._check_valgus_3d(world_lm)

        # ⑤ 状态机 — 阈值略宽松避免边界抖动
        if angle < 100 and self.stage == "UP":
            self.stage = "DOWN"
            self.last_progress_time = time.time()
            self.highest_angle = angle
            self.feedback = "Push up! Fight it!"

        elif self.stage == "DOWN" and angle <= 160:
            cur = time.time()
            if angle > self.highest_angle + 2:
                self.highest_angle = angle
                self.last_progress_time = cur
                if not self.valgus_active:
                    self.feedback = "Grinding! Keep pushing!"
            if cur - self.last_progress_time > self.timeout_threshold:
                self.stage = "FAIL"
                self.feedback = "Failed! Spotter needed!"

        if angle > 160:
            if self.stage == "DOWN":
                now = time.time()
                # 👇👇👇 核心拦截逻辑：只有间隔大于 1 秒才计次 👇👇👇
                if now - self.last_count_time > self.COOLDOWN_PERIOD:
                    self.stage = "UP"
                    self.counter += 1
                    self.last_count_time = now
                    self.feedback = f"Perfect! Count: {self.counter}"
                    self.valgus_active = False
                else:
                    # 如果时间太短，说明是侧拍时的噪点抖动导致的假起身，过滤掉不计次
                    self.stage = "UP" 
                    self.valgus_active = False
                # 👆👆👆 ======================================= 👆👆👆
                
            elif self.stage == "FAIL":
                self.stage = "UP"
                self.feedback = "Reset. Take a breath."
                self.valgus_active = False

        if self.valgus_active and self.stage == "DOWN":
            self.feedback = "⚠ 膝盖内扣！脚尖膝盖对齐！"

        # ⑥ OSD渲染
        knee_pt = self.smooth2d(25, landmarks[25].x * w, landmarks[25].y * h)
        cv2.putText(frame, str(int(angle)), tuple(knee_pt.astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        sc = (0, 255, 0)
        if self.stage == "DOWN":  sc = (0, 255, 255)
        elif self.stage == "FAIL": sc = (0, 0, 255)
        self.draw_osd(frame, "SQUATS", sc)

        # ⑦ 膝盖内扣横幅警告
        if self.valgus_active and self.stage == "DOWN":
            by = h // 2
            cv2.rectangle(frame, (0, by - 55), (w, by + 55), (0, 0, 170), -1)
            cv2.putText(frame, "⚠  KNEE VALGUS  /  膝盖内扣",
                        (w // 2 - 260, by + 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3, cv2.LINE_AA)
        return frame


# ──────────────────────────────────────────────
#  哑铃弯举
# ──────────────────────────────────────────────
class BicepCurl(BaseExercise):
    """
    修复：最优单侧门控 + 3D肘关节角度（解决侧视图误判）
    """
    def __init__(self):
        super().__init__()
        self.stage = "DOWN"
        self.feedback = "Ready for Curls"

    def _get_angle_3d(self, wlm):
        def side(s, e, wr):
            return calculate_angle_3d(wpt(wlm, s), wpt(wlm, e), wpt(wlm, wr))
        l = side(11, 13, 15)
        r = side(12, 14, 16)
        # 取肘关节弯曲更大的一侧（正在做动作的手臂）
        return min(l, r)   # 弯曲更多 = 角度更小

    def process_frame(self, landmarks, world_lm, frame):
        h, w, _ = frame.shape

        if not self.update_gate(landmarks, [11, 13, 15], [12, 14, 16]):
            self.draw_calibrating(frame, "CURLS")
            return frame

        if world_lm is not None:
            angle = self._get_angle_3d(world_lm)
            # OSD点：取可见度较高的肘关节
            l_vis = landmarks[13].visibility
            r_vis = landmarks[14].visibility
            e_idx = 13 if l_vis >= r_vis else 14
        else:
            sh = self.smooth2d(12, landmarks[12].x * w, landmarks[12].y * h)
            el = self.smooth2d(14, landmarks[14].x * w, landmarks[14].y * h)
            wr = self.smooth2d(16, landmarks[16].x * w, landmarks[16].y * h)
            angle = calculate_angle_2d(sh, el, wr)
            e_idx = 14

        if angle < 40 and self.stage == "DOWN":
            self.stage = "UP"
            self.counter += 1
            self.feedback = f"Good squeeze! Count: {self.counter}"
        elif angle > 150 and self.stage == "UP":
            self.stage = "DOWN"
            self.feedback = "Slowly down..."

        elbow_pt = self.smooth2d(e_idx, landmarks[e_idx].x * w, landmarks[e_idx].y * h)
        cv2.putText(frame, str(int(angle)), tuple(elbow_pt.astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        sc = (0, 255, 0) if self.stage == "UP" else (0, 255, 255)
        self.draw_osd(frame, "CURLS", sc)
        return frame


# ──────────────────────────────────────────────
#  硬拉
# ──────────────────────────────────────────────
class Deadlift(BaseExercise):
    """
    修复：最优单侧门控 + 3D躯干折叠角度
    """
    def __init__(self):
        super().__init__()
        self.stage = "UP"
        self.feedback = "Ready for Deadlift"

    def _get_angle_3d(self, wlm):
        """肩-髋-膝角，反映躯干前倾程度"""
        def side(s, hp, k):
            # 合法性：肩膀在髋部上方
            if not (wlm[s].y > wlm[hp].y):
                return None
            return calculate_angle_3d(wpt(wlm, s), wpt(wlm, hp), wpt(wlm, k))
        l = side(11, 23, 25)
        r = side(12, 24, 26)
        if l is None and r is None: return None
        if l and r: return (l + r) / 2.0
        return l if l else r

    def process_frame(self, landmarks, world_lm, frame):
        h, w, _ = frame.shape

        if not self.update_gate(landmarks, [11, 23, 25], [12, 24, 26]):
            self.draw_calibrating(frame, "DEADLIFT")
            return frame

        if world_lm is not None:
            angle = self._get_angle_3d(world_lm)
        else:
            sh  = self.smooth2d(12, landmarks[12].x * w, landmarks[12].y * h)
            hip = self.smooth2d(24, landmarks[24].x * w, landmarks[24].y * h)
            kn  = self.smooth2d(26, landmarks[26].x * w, landmarks[26].y * h)
            angle = calculate_angle_2d(sh, hip, kn)

        if angle is None:
            self.feedback = "⚠ 请确保躯干入镜"
            self.draw_osd(frame, "DEADLIFT", (0, 165, 255))
            return frame

        if angle < 110 and self.stage == "UP":
            self.stage = "DOWN"
            self.feedback = "Push hips forward!"
        elif angle > 160 and self.stage == "DOWN":
            self.stage = "UP"
            self.counter += 1
            self.feedback = f"Perfect Pull! Count: {self.counter}"

        hip_pt = self.smooth2d(24, landmarks[24].x * w, landmarks[24].y * h)
        cv2.putText(frame, str(int(angle)), tuple(hip_pt.astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        sc = (0, 255, 0) if self.stage == "UP" else (0, 255, 255)
        self.draw_osd(frame, "DEADLIFT", sc)
        return frame


# ──────────────────────────────────────────────
#  俯卧撑
# ──────────────────────────────────────────────
class PushUp(BaseExercise):
    """
    修复：
      ✅ 侧视图门控卡死  → 最优单侧门控
      ✅ 侧视图角度误差  → 3D肘关节角度
      ✅ 超时检测保留
    """
    def __init__(self):
        super().__init__()
        self.stage = "UP"
        self.feedback = "Ready for Push-ups"
        self.last_progress_time = 0
        self.highest_angle = 0
        self.timeout_threshold = 3.0
        self.last_rep_time = 0      
        self.REP_COOLDOWN = 1.2  # 卧推不可能在 1.2 秒内完成一次起

    def _get_angle_3d(self, wlm, landmarks):
        """【手术 1】抛弃 min(l, r)，改为可见度(Visibility)赢家通吃"""
        # 计算左右臂 3D 角度
        l = calculate_angle_3d(wpt(wlm, 11), wpt(wlm, 13), wpt(wlm, 15))
        r = calculate_angle_3d(wpt(wlm, 12), wpt(wlm, 14), wpt(wlm, 16))
        
        # 获取肘部置信度
        l_vis = landmarks[13].visibility
        r_vis = landmarks[14].visibility
        
        # 谁的可见度高，完全采信谁的数据（差值阈值设为 0.15 避免频繁切换）
        if l_vis > r_vis + 0.15:
            return l
        elif r_vis > l_vis + 0.15:
            return r
        else:
            return (l + r) / 2.0

    def process_frame(self, landmarks, world_lm, frame):
        h, w, _ = frame.shape
        current_feedback = "Ready for Bench Press" # 默认状态文本

        if not self.update_gate(landmarks, [11, 13, 15], [12, 14, 16]):
            self.draw_calibrating(frame, "BENCH PRESS")
            return frame

        # 【重点】调用传参增加 landmarks
        if world_lm is not None:
            angle = self._get_angle_3d(world_lm, landmarks)
            e_idx = 13 if landmarks[13].visibility >= landmarks[14].visibility else 14
        else:
            # ... 你的 2D 回退逻辑保持不变 ...
            pass

        # ---- 状态机逻辑 ----
        if angle < 90 and self.stage == "UP":
            self.stage = "DOWN"
            self.last_progress_time = time.time()
            self.highest_angle = angle
            current_feedback = "Press it! Drive!"
            
        elif self.stage == "DOWN" and angle <= 160:
            cur = time.time()
            if angle > self.highest_angle + 2:
                self.highest_angle = angle
                self.last_progress_time = cur
                current_feedback = "Grinding! Push through!"
                
            if cur - self.last_progress_time > self.timeout_threshold:
                self.stage = "FAIL"
                self.set_warning("Failed! Spotter take the bar!") # 使用驻留警告

        if angle > 160:
            if self.stage == "DOWN":
                current_time = time.time()
                # 【手术 2】动作时间冷却锁 (Debounce)
                if current_time - self.last_rep_time > self.REP_COOLDOWN:
                    self.stage = "UP"
                    self.counter += 1
                    self.last_rep_time = current_time # 刷新 CD
                    current_feedback = f"Light weight! Count: {self.counter}"
                else:
                    # 如果间隔太短，说明是噪点引起的抖动，拒绝计数
                    self.stage = "UP"
                    current_feedback = "Too fast! Control the eccentric!"
                    
            elif self.stage == "FAIL":
                self.stage = "UP"
                current_feedback = "Reset. Rack the bar."

        # 【手术 3】输出最终的反馈文本（通过基类的过滤器）
        self.feedback = self.get_current_feedback(current_feedback)

        # ---- OSD 渲染 ----
        elbow_pt = self.smooth2d(e_idx, landmarks[e_idx].x * w, landmarks[e_idx].y * h)
        cv2.putText(frame, str(int(angle)), tuple(elbow_pt.astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        sc = (0, 0, 255) if self.stage == "FAIL" else (
             (0, 255, 255) if self.stage == "DOWN" else (0, 255, 0))
        
        self.draw_osd(frame, "BENCH PRESS", sc)
        return frame


# ──────────────────────────────────────────────
#  卧推
# ──────────────────────────────────────────────
class BenchPress(BaseExercise):
    """
    修复：最优单侧门控 + 3D肘关节角度 + 超时检测
    """
    def __init__(self):
        super().__init__()
        self.stage = "UP"
        self.feedback = "Ready for Bench Press"
        self.last_progress_time = 0
        self.highest_angle = 0
        self.timeout_threshold = 3.0

    def _get_angle_3d(self, wlm):
        l = calculate_angle_3d(wpt(wlm, 11), wpt(wlm, 13), wpt(wlm, 15))
        r = calculate_angle_3d(wpt(wlm, 12), wpt(wlm, 14), wpt(wlm, 16))
        return min(l, r)

    def process_frame(self, landmarks, world_lm, frame):
        h, w, _ = frame.shape

        if not self.update_gate(landmarks, [11, 13, 15], [12, 14, 16]):
            self.draw_calibrating(frame, "BENCH PRESS")
            return frame

        if world_lm is not None:
            angle = self._get_angle_3d(world_lm)
            e_idx = 13 if landmarks[13].visibility >= landmarks[14].visibility else 14
        else:
            sh = self.smooth2d(11, landmarks[11].x * w, landmarks[11].y * h)
            el = self.smooth2d(13, landmarks[13].x * w, landmarks[13].y * h)
            wr = self.smooth2d(15, landmarks[15].x * w, landmarks[15].y * h)
            angle = calculate_angle_2d(sh, el, wr)
            e_idx = 13

        if angle < 90 and self.stage == "UP":
            self.stage = "DOWN"
            self.last_progress_time = time.time()
            self.highest_angle = angle
            self.feedback = "Press it! Drive!"
        elif self.stage == "DOWN" and angle <= 160:
            cur = time.time()
            if angle > self.highest_angle + 2:
                self.highest_angle = angle
                self.last_progress_time = cur
                self.feedback = "Grinding! Push through!"
            if cur - self.last_progress_time > self.timeout_threshold:
                self.stage = "FAIL"
                self.feedback = "Failed! Spotter take the bar!"

        if angle > 160:
            if self.stage == "DOWN":
                self.stage = "UP"
                self.counter += 1
                self.feedback = f"Light weight! Count: {self.counter}"
            elif self.stage == "FAIL":
                self.stage = "UP"
                self.feedback = "Reset. Rack the bar."

        elbow_pt = self.smooth2d(e_idx, landmarks[e_idx].x * w, landmarks[e_idx].y * h)
        cv2.putText(frame, str(int(angle)), tuple(elbow_pt.astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        sc = (0, 0, 255) if self.stage == "FAIL" else (
             (0, 255, 255) if self.stage == "DOWN" else (0, 255, 0))
        self.draw_osd(frame, "BENCH PRESS", sc)
        return frame