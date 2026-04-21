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

class MetricsInput(BaseModel):
    height: float
    weight: float
    goal: str
    level: str
    days: int

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
    new_user = models.User(username=user.username, hashed_password=hashed_pwd)
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
def generate_workout_plan(metrics: MetricsInput, current_user: models.User = Depends(get_current_user)):
    try:
        generation_config = {
            "temperature": 0.7,
            "response_mime_type": "application/json", 
        }
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )
        prompt = f"""
        你现在是一位顶级的健身教练。
        用户数据：身高 {metrics.height}cm, 体重 {metrics.weight}kg。
        用户目标：{metrics.goal}。经验水平：{metrics.level}。每周训练天数：{metrics.days}天。
        
        请为他制定一个训练计划。
        注意：你【只能】从以下 5 个动作中选择：SQUAT (深蹲), BICEP_CURL (弯举), DEADLIFT (硬拉), PUSH_UP (俯卧撑), BENCH_PRESS (卧推)。
        
        必须严格返回一个 JSON 数组，格式如下：
        [
          {{
            "day": 1,
            "exercise_code": "SQUAT",
            "exercise_name": "深蹲",
            "sets": 4,
            "reps": 12,
            "advice": "注意保持背部挺直"
          }}
        ]
        """
        response = model.generate_content(prompt)
        plan_data = json.loads(response.text)
        return {"message": "计划生成成功", "plan": plan_data}
        
    except Exception as e:
        print(f"Gemini API 调用失败: {e}")
        raise HTTPException(status_code=500, detail="AI 计划生成失败，请稍后再试")

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)