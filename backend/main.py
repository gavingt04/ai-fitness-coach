from fastapi import FastAPI, WebSocket, Depends, HTTPException, status, WebSocketDisconnect
import mediapipe as mp
import cv2
import numpy as np
import base64
import io
import uvicorn
import json
import google.generativeai as genai
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# --- 全栈数据库与密码学模块 ---
from sqlalchemy.orm import Session  
from passlib.context import CryptContext 
import models
import schemas
import database

#导入本地Qwen模型接口
import requests
import re
from typing import List, Optional

# 编写登陆逻辑
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

# 安全，规定了Token的提取路径
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# 导入所有动作类
from exercises import Squat, BicepCurl, Deadlift, PushUp, BenchPress

# 加载环境变量
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ 环境变量 GEMINI_API_KEY 未设置！请检查 .env 文件")
genai.configure(api_key=api_key)

# 定义更新用户信息的 Pydantic 模型
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    weight: Optional[float] = None


class MetricsInput(BaseModel):
    age: int
    weight: float
    identity: Optional[str] = ""
    injury: Optional[str] = ""
    goal: str
    level: str
    days: int
    equipments: List[str]

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

# 动作映射表
EXERCISE_MAP = {
    "SQUAT": Squat,
    "BICEP_CURL": BicepCurl,
    "DEADLIFT": Deadlift,
    "PUSH_UP": PushUp,
    "BENCH_PRESS": BenchPress
}

app = FastAPI()

# --- 登录配置 ---
SECRET_KEY = "GESHUAI_SUPER_SECRET_KEY" 
ALGORITHM = "HS256"                     
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24   

# 系统启动时的数据库初始化
models.Base.metadata.create_all(bind=database.engine)

# 密码加密器配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================================
#           RESTful API 路由区 (HTTP协议)
# ==========================================

# 【修复点】：去掉了所有的 /api 前缀，迎接 Vite 代理转发过来的纯净路由
@app.post("/register", response_model=schemas.UserOut) 
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first() 
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    hashed_pwd = pwd_context.hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pwd, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user) 
    return new_user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="用户不存在")
    if not pwd_context.verify(form_data.password, db_user.hashed_password):
         raise HTTPException(status_code=400, detail="密码错误")
    
    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": db_user.username, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)

    return {"access_token": encoded_jwt, "token_type": "bearer"}

# 身份验证依赖 (TokenUrl 恢复为 login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") 

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") 
        if username is None:
            raise HTTPException(status_code=401, detail="无效凭证")
    except Exception:
        raise HTTPException(status_code=401, detail="登陆已过期") 
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在，请重新登录")
    return user

@app.post("/records") 
def create_record(record: schemas.RecordCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    new_record = models.WorkoutRecord( 
        exercise_type = record.exercise_type,
        count = record.count,
        issues = record.issues, 
        user_id = current_user.id
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return {"message": "记录保存成功", "record_id": new_record.id, "user": current_user.username}

@app.get("/records/my")
def get_my_records(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    records = db.query(models.WorkoutRecord)\
                .filter(models.WorkoutRecord.user_id == current_user.id)\
                .order_by(models.WorkoutRecord.timestamp.desc())\
                .all()
    return records

@app.post("/plan/generate")
def generate_workout_plan(
    metrics: MetricsInput, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    try:
        equipments_str = "、".join(metrics.equipments) if metrics.equipments else "自重"
        injury_str = metrics.injury if metrics.injury else "无"
        
        # 将前端传来的精准数据组装进 Prompt
        prompt = f"""
        你是一位专业的 AI 健身教练。请为以下用户制定【{metrics.days}天完整训练计划】：
        - 用户画像：年龄 {metrics.age}, 日常身份 {metrics.identity}。
        - 身体指标：体重 {metrics.weight}kg。
        - 当前水平：{metrics.level}。
        - 伤病情况：{injury_str}。
        - 可用器械：{equipments_str}。
        - 核心目标：{metrics.goal}。
        
        【严格要求】：
        1. 必须生成 {metrics.days} 天的计划。如果包含休息日，用 REST 表示。
        2. 避开受伤部位。
        3. 只能使用以下动作代码：SQUAT, BICEP_CURL, DEADLIFT, PUSH_UP, BENCH_PRESS, REST。
        
        必须严格返回 JSON 数组格式，不要包含多余的文字：
        [
          {{"day": 1, "exercise_code": "SQUAT", "exercise_name": "深蹲", "sets": 4, "reps": 12, "advice": "动作放慢"}}
        ]
        """
        
        # 请求本地大模型 Qwen2.5:7b
        response = requests.post("http://localhost:11434/api/generate", 
                               json={"model": "qwen2.5:7b", "prompt": prompt, "stream": False, "format": "json"})
        response.raise_for_status()
        result_text = response.json().get("response", "")
        
        match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if match:
            clean_text = match.group()
            plan_data = json.loads(clean_text)
            
            plan_json_str = json.dumps(plan_data, ensure_ascii=False)
            db.query(models.User).filter(models.User.id == current_user.id).update(
                {"workout_plan": plan_json_str}
            )
            db.commit() 
            return {"message": "计划生成并保存成功", "plan": plan_data}
        else:
            raise ValueError("AI 未能返回有效的 JSON 数组")
            
    except Exception as e:
        db.rollback()
        print(f"生成报错: {e}")
        raise HTTPException(status_code=500, detail="生成失败，请检查服务")
    
# 1. 增强获取接口：加入终端打印，方便你直观看到数据库里有没有东西
@app.get("/plan/my")
def get_my_plan(current_user: models.User = Depends(get_current_user)):
    # 在后端终端打印当前用户的存储状态
    print(f"====== 数据库检索 ======\n用户: {current_user.username}\n数据库中的计划: {current_user.workout_plan}\n======================")
    
    if not current_user.workout_plan:
        return {"plan": []}
    return {"plan": json.loads(current_user.workout_plan)}
# ==========================================
#           AI 引擎核心区 (WebSocket协议)
# ==========================================
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: str, 
    exercise: str,  
    db: Session = Depends(database.get_db)
):
    await websocket.accept()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) 
        username: str = payload.get("sub")
        if username is None: 
            await websocket.close(code=1008)
            return
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            await websocket.close(code=1008)
            return
    except Exception:
        await websocket.close(code=1008) 
        return
            
    exercise_key = exercise.upper() 
    if exercise_key not in EXERCISE_MAP:
        await websocket.close(code=1003) 
        return
        
    current_exercise = EXERCISE_MAP[exercise_key]()
    
    try:
        while True:
            data = await websocket.receive_text()
            image_bytes = base64.b64decode(data)
            image_stream = io.BytesIO(image_bytes)
            file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
            frame_raw = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            frame_workspace = cv2.flip(frame_raw, 1)
            frame_rgb = cv2.cvtColor(frame_workspace, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)
            
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(frame_workspace, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                current_exercise.process_frame(results.pose_landmarks.landmark, frame_workspace.copy())

            frame_final = cv2.flip(frame_workspace, 1)   
            _, buffer = cv2.imencode('.jpg', frame_final)
            b64_string = base64.b64encode(buffer).decode('utf-8')

            payload = {
                "image": b64_string,
                "feedback": current_exercise.feedback,
                "counter": current_exercise.counter,
                "stage": current_exercise.stage
            }
            await websocket.send_text(json.dumps(payload))
                
    except WebSocketDisconnect: 
        print(f"用户 {user.username} 正常离开")
    except Exception as e:
        print(f"视频流处理发生异常: {e}")
    finally:
        if current_exercise.counter > 0:
            new_record = models.WorkoutRecord(
                exercise_type=exercise_key,
                count=current_exercise.counter,
                user_id=user.id
            )
            db.add(new_record) 
            db.commit()


# 3. 添加获取个人信息的 GET 接口
@app.get("/users/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id, # 增加真实 ID
        "username": current_user.username,
        "email": current_user.email or "",
        "weight": current_user.weight or 70.0,
    }

# 4. 添加更新个人信息的 PUT 接口
@app.put("/users/me")
def update_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 如果修改了用户名，需要检查是否重复
    if user_update.username and user_update.username != current_user.username:
        existing = db.query(models.User).filter(models.User.username == user_update.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="该昵称/用户名已被占用")
        current_user.username = user_update.username

    if user_update.email is not None:
        current_user.email = user_update.email
        
    if user_update.weight is not None:
        current_user.weight = user_update.weight
        
    db.commit()
    return {"message": "个人信息更新成功"}

# 3. 修改密码接口 (为 ChangePassword.vue 准备)
class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

@app.put("/users/password")
def update_password(
    pwd_data: PasswordUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not pwd_context.verify(pwd_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    current_user.hashed_password = pwd_context.hash(pwd_data.new_password)
    db.commit()
    return {"message": "密码修改成功"}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)