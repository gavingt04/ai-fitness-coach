# exercises.py
import numpy as np
import cv2
import time

def calculate_angle(a, b, c): #计算三个点之间的夹角，例如膝盖：髋部A，膝盖B，踝部C
    # 通过函数计算出BA和BC向量之间相对于水平的绝对角度，再两者相减
    a = np.array(a)
    b = np.array(b)
    c = np.array(c) # 使得a,b,c成为numpy数组，也就是向量，方便计算
    
    # 【修正点】: 原代码中 actan2 应为 arctan2
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]- b[0])
    
    # 先算出BC向量和水平线的夹角，再算出BA向量和水平线的夹角，两者相减得到BA和BC之间的夹角
    # 其次，使用arctan2(y,x)函数，要先纵，后横
    # 使用arctan2相比于使用arctan的好处是，前者可以处理所有象限，后者只能处理第一和第四象限
    angle = np.abs(radians * 180.0 / np.pi) # 将弧度转换为角度
    
    if angle > 180.0:
        angle = 360 - angle # 如果角度大于180度，说明是钝角，需要用360减去它得到锐角
        
    # 【修正点】: return 应该在 if 之外，否则小于180度时函数会返回 None
    return angle

class Squat:
    """
    具体的深蹲动作类，继承自我们规划的动作逻辑
    """
    def __init__(self):#构造函数，在创建对象时自动调用  每一个对象都有自己的生命周期，不会导致数据串位
        # 动作状态与计数变量 (初始化记分板)
        self.counter = 0        # 记录完成的深蹲次数
        self.stage = "UP"       # 初始状态：站立
        self.feedback = "Ready" # 实时反馈语

        #增加计时场景，用户蹲下后长时间未站立
        self.last_progress_time = 0 #用户蹲下后的时间戳，初始为0
        self.highest_angle = 0 #用户蹲下过程中检测到的最高角度，初始为0
        self.timeout_threshold = 3.0 #用户蹲下后超过3秒未站立则触发超时反馈

        # 独立的减震器缓存 (每个动作类独立维护，防止干扰)
        self.landmark_buffer = {} 
        self.BUFFER_SIZE = 5    # 设置缓冲区大小，也就是要存储多少帧的坐标

    def get_smooth_landmark(self, index, current_x, current_y):
        # 这一步也在进行数据清洗，是紧跟在Mediapipe检测后的
        if index not in self.landmark_buffer:
            self.landmark_buffer[index] = []
            # 如果这个关节点还没有在字典里，就创建一个空列表来存储它的坐标
            
        self.landmark_buffer[index].append([current_x, current_y])
        
        if len(self.landmark_buffer[index]) > self.BUFFER_SIZE:
            self.landmark_buffer[index].pop(0) # 采用FIFO先进先出的方式确保实时性
            
        avg_coords = np.mean(self.landmark_buffer[index], axis=0) # 计算矩阵的算术平均值，将5行数据压缩成1行
        return avg_coords # 完成加权平滑处理

    def process_frame(self, landmarks, frame):
        """
        核心处理逻辑：输入骨骼点，返回处理后的画面和状态
        """
        h, w, _ = frame.shape # 获取画面尺寸，后续坐标转换需要用到
        
        # 1. 提取并平滑深蹲所需的左侧三点：髋(23), 膝(25), 踝(27)
        hip = self.get_smooth_landmark(23, landmarks[23].x * w, landmarks[23].y * h)#髋部
        #mediapipe给出像素的比例，再乘上获取的宽度和高度得到实际的像素坐标
        #在process_frame中调用了get_smooth_landmark方法
        knee = self.get_smooth_landmark(25, landmarks[25].x * w, landmarks[25].y * h)
        ankle = self.get_smooth_landmark(27, landmarks[27].x * w, landmarks[27].y * h)
        
        # 2. 调用量角器计算膝盖夹角
        angle = calculate_angle(hip, knee, ankle)
        
        # 3. 状态机判定逻辑 (FSM) 论文核心亮点，双阈值状态机

        #深蹲超过90度，认为进入蹲下状态，记录时间戳和初始底部角度
        ### 【逻辑改进】：增加了 self.stage == "UP" 的判定，防止在蹲下过程中反复刷新起始时间
        if angle < 90 and self.stage == "UP":
            self.stage = "DOWN"
            self.last_progress_time = time.time() # 用户进入蹲下状态，记录当前时间戳
            self.highest_angle = angle #记录初始底部角度
            self.feedback = "Push up! Fight it!"

        #蹲下后粘滞在底部，如果超过设定的时间阈值且用户没有站起来，给予超时反馈
        elif self.stage == "DOWN" and angle <= 160:
            current_time = time.time()

            if angle > self.highest_angle + 2:
                self.highest_angle = angle #更新最高角度，允许用户在底部有微小的调整
                self.last_progress_time = current_time #用户有进展，重置计时
                self.feedback = "Grinding! Keep pushing!"

            if current_time - self.last_progress_time > self.timeout_threshold:
                # 用户在底部停留过久，给予超时反馈
                self.stage = "FAIL"
                self.feedback = "Failed! Spotter needed!"


        if angle > 160 : # 站立状态的判定，角度大于160度才认为是完全站立，避免过早切换到UP状态
            if self.stage == "DOWN":
                self.stage = "UP"
                self.counter += 1
                self.feedback = f"Perfect! Count: {self.counter}"

            elif self.stage == "FAIL": #如果之前是FAIL状态，用户站起来了，认为是完成了一个失败的深蹲，重置状态机但不增加计数
                self.stage = "UP"
                self.feedback = "Reset. Take a breath."

        # 5.OSD( On-Screen Display ) 渲染逻辑
        cv2.putText(frame,str(int(angle)),
                    tuple(knee.astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        
        cv2.rectangle(frame,(0, 0), (500, 150), (0, 0, 0), -1)

        cv2.putText(frame, f"SQUATS: {self.counter}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
        
        stage_color = (0,255,0)
        if self.stage == "DOWN":
            stage_color = (0, 255, 255) 
        elif self.stage == "FAIL":
            stage_color = (0, 0, 255)

        cv2.putText(frame, f"STAGE: {self.stage}", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, stage_color, 2, cv2.LINE_AA)
        
        cv2.putText(frame, self.feedback, (20, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        return frame

# --- 修正点：以下类必须与 class Squat 顶格对齐，解决嵌套类导致的语法错误 ---

class BicepCurl:
    """
    哑铃弯举动作类
    """
    def __init__(self):
        self.counter = 0
        # 【核心差异1】弯举的初始状态是手臂自然下垂，即 DOWN
        self.stage = "DOWN"       
        self.feedback = "Ready for Curls"
        self.landmark_buffer = {} 
        self.BUFFER_SIZE = 5 

    def get_smooth_landmark(self, index, current_x, current_y):
        if index not in self.landmark_buffer:
            self.landmark_buffer[index] = []
        self.landmark_buffer[index].append([current_x, current_y])
        if len(self.landmark_buffer[index]) > self.BUFFER_SIZE:
            self.landmark_buffer[index].pop(0) 
        return np.mean(self.landmark_buffer[index], axis=0) 

    def process_frame(self, landmarks, frame):
        h, w, _ = frame.shape 
        shoulder = self.get_smooth_landmark(12, landmarks[12].x * w, landmarks[12].y * h)
        elbow = self.get_smooth_landmark(14, landmarks[14].x * w, landmarks[14].y * h)
        wrist = self.get_smooth_landmark(16, landmarks[16].x * w, landmarks[16].y * h)
        angle = calculate_angle(shoulder, elbow, wrist)
        
        if angle < 40 and self.stage == "DOWN":
            self.stage = "UP"
            self.counter += 1
            self.feedback = f"Good squeeze! Count: {self.counter}"
        elif angle > 150 and self.stage == "UP":
            self.stage = "DOWN"
            self.feedback = "Slowly down..."

        cv2.putText(frame,str(int(angle)), tuple(elbow.astype(int)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.rectangle(frame,(0, 0), (500, 150), (0, 0, 0), -1)
        cv2.putText(frame, f"CURLS: {self.counter}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
        stage_color = (0,255,0) if self.stage == "UP" else (0, 255, 255)
        cv2.putText(frame, f"STAGE: {self.stage}", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, stage_color, 2, cv2.LINE_AA)
        cv2.putText(frame, self.feedback, (20, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        return frame

class Deadlift:
    """
    硬拉动作类 (以罗马尼亚硬拉 RDL 为例)
    """
    def __init__(self):
        self.counter = 0
        self.stage = "UP" 
        self.feedback = "Ready for Deadlift"
        self.landmark_buffer = {} 
        self.BUFFER_SIZE = 5 

    def get_smooth_landmark(self, index, current_x, current_y):
        if index not in self.landmark_buffer:
            self.landmark_buffer[index] = []
        self.landmark_buffer[index].append([current_x, current_y])
        if len(self.landmark_buffer[index]) > self.BUFFER_SIZE:
            self.landmark_buffer[index].pop(0) 
        return np.mean(self.landmark_buffer[index], axis=0) 

    def process_frame(self, landmarks, frame):
        h, w, _ = frame.shape 
        shoulder = self.get_smooth_landmark(12, landmarks[12].x * w, landmarks[12].y * h)
        hip = self.get_smooth_landmark(24, landmarks[24].x * w, landmarks[24].y * h)
        knee = self.get_smooth_landmark(26, landmarks[26].x * w, landmarks[26].y * h)
        angle = calculate_angle(shoulder, hip, knee)
        
        if angle < 110 and self.stage == "UP":
            self.stage = "DOWN"
            self.feedback = "Push hips forward!"
        elif angle > 160 and self.stage == "DOWN":
            self.stage = "UP"
            self.counter += 1
            self.feedback = f"Perfect Pull! Count: {self.counter}"

        cv2.putText(frame,str(int(angle)), tuple(hip.astype(int)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.rectangle(frame,(0, 0), (500, 150), (0, 0, 0), -1)
        cv2.putText(frame, f"DEADLIFT: {self.counter}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
        stage_color = (0,255,0) if self.stage == "UP" else (0, 255, 255)
        cv2.putText(frame, f"STAGE: {self.stage}", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, stage_color, 2, cv2.LINE_AA)
        cv2.putText(frame, self.feedback, (20, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        return frame

class PushUp:
    """
    俯卧撑动作类
    """
    def __init__(self):
        self.counter = 0
        self.stage = "UP"       
        self.feedback = "Ready for Push-ups" 
        self.last_progress_time = 0 
        self.highest_angle = 0 
        self.timeout_threshold = 3.0 
        self.landmark_buffer = {} 
        self.BUFFER_SIZE = 5 

    def get_smooth_landmark(self, index, current_x, current_y):
        if index not in self.landmark_buffer:
            self.landmark_buffer[index] = []
        self.landmark_buffer[index].append([current_x, current_y])
        if len(self.landmark_buffer[index]) > self.BUFFER_SIZE:
            self.landmark_buffer[index].pop(0) 
        return np.mean(self.landmark_buffer[index], axis=0) 

    def process_frame(self, landmarks, frame):
        h, w, _ = frame.shape 
        shoulder = self.get_smooth_landmark(11, landmarks[11].x * w, landmarks[11].y * h)
        elbow = self.get_smooth_landmark(13, landmarks[13].x * w, landmarks[13].y * h)
        wrist = self.get_smooth_landmark(15, landmarks[15].x * w, landmarks[15].y * h)
        angle = calculate_angle(shoulder, elbow, wrist)
        
        if angle < 90 and self.stage == "UP":
            self.stage = "DOWN"
            self.last_progress_time = time.time()
            self.highest_angle = angle 
            self.feedback = "Push up! Fight it!"
        elif self.stage == "DOWN" and angle <= 160:
            current_time = time.time()
            if angle > self.highest_angle + 2:
                self.highest_angle = angle 
                self.last_progress_time = current_time 
                self.feedback = "Grinding! Keep pushing!"
            if current_time - self.last_progress_time > self.timeout_threshold:
                self.stage = "FAIL"
                self.feedback = "Failed! Rest needed!"

        if angle > 160 : 
            if self.stage == "DOWN":
                self.stage = "UP"
                self.counter += 1
                self.feedback = f"Perfect! Count: {self.counter}"
            elif self.stage == "FAIL": 
                self.stage = "UP"
                self.feedback = "Reset. Take a breath."

        cv2.putText(frame,str(int(angle)), tuple(elbow.astype(int)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.rectangle(frame,(0, 0), (500, 150), (0, 0, 0), -1)
        cv2.putText(frame, f"PUSH-UPS: {self.counter}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
        stage_color = (0,255,0) if self.stage == "UP" else ((0, 255, 255) if self.stage == "DOWN" else (0, 0, 255))
        cv2.putText(frame, f"STAGE: {self.stage}", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, stage_color, 2, cv2.LINE_AA)
        cv2.putText(frame, self.feedback, (20, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        return frame

class BenchPress:
    """
    卧推动作类
    """
    def __init__(self):
        self.counter = 0
        self.stage = "UP"       
        self.feedback = "Ready for Bench Press" 
        self.last_progress_time = 0 
        self.highest_angle = 0 
        self.timeout_threshold = 3.0 
        self.landmark_buffer = {} 
        self.BUFFER_SIZE = 5 

    def get_smooth_landmark(self, index, current_x, current_y):
        if index not in self.landmark_buffer:
            self.landmark_buffer[index] = []
        self.landmark_buffer[index].append([current_x, current_y])
        if len(self.landmark_buffer[index]) > self.BUFFER_SIZE:
            self.landmark_buffer[index].pop(0) 
        return np.mean(self.landmark_buffer[index], axis=0) 

    def process_frame(self, landmarks, frame):
        h, w, _ = frame.shape 
        shoulder = self.get_smooth_landmark(11, landmarks[11].x * w, landmarks[11].y * h)
        elbow = self.get_smooth_landmark(13, landmarks[13].x * w, landmarks[13].y * h)
        wrist = self.get_smooth_landmark(15, landmarks[15].x * w, landmarks[15].y * h)
        angle = calculate_angle(shoulder, elbow, wrist)
        
        if angle < 90 and self.stage == "UP":
            self.stage = "DOWN"
            self.last_progress_time = time.time()
            self.highest_angle = angle 
            self.feedback = "Press it! Drive!"
        elif self.stage == "DOWN" and angle <= 160:
            current_time = time.time()
            if angle > self.highest_angle + 2:
                self.highest_angle = angle 
                self.last_progress_time = current_time 
                self.feedback = "Grinding! Push through!"
            if current_time - self.last_progress_time > self.timeout_threshold:
                self.stage = "FAIL"
                self.feedback = "Failed! Spotter take the bar!" 

        if angle > 160 : 
            if self.stage == "DOWN":
                self.stage = "UP"
                self.counter += 1
                self.feedback = f"Light weight! Count: {self.counter}"
            elif self.stage == "FAIL": 
                self.stage = "UP"
                self.feedback = "Reset. Rack the bar."

        cv2.putText(frame,str(int(angle)), tuple(elbow.astype(int)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        cv2.rectangle(frame,(0, 0), (500, 150), (0, 0, 0), -1)
        cv2.putText(frame, f"BENCH PRESS: {self.counter}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
        stage_color = (0,255,0) if self.stage == "UP" else ((0, 255, 255) if self.stage == "DOWN" else (0, 0, 255))
        cv2.putText(frame, f"STAGE: {self.stage}", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, stage_color, 2, cv2.LINE_AA)
        cv2.putText(frame, self.feedback, (20, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        return frame