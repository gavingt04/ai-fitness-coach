from fastapi import FastAPI, WebSocket, Depends, HTTPException, status, WebSocketDisconnect
import mediapipe as mp
import cv2
import numpy as np
import base64
import io
import uvicorn
import json

# --- 新增：全栈数据库与密码学模块 ---
from sqlalchemy.orm import Session  # 导入数据库
from passlib.context import CryptContext # 导入密码加密器，使用 bcrypt 算法进行安全哈希处理
import models
import schemas
import database

# 编写登陆逻辑
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

# 导入我们刚刚创建的动作类
from exercises import Squat

# 安全，规定了Token的提取路径
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# 导入所有动作类
from exercises import Squat, BicepCurl, Deadlift, PushUp, BenchPress

# 动作映射表：根据前端传来的动作类型字符串，动态实例化对应的动作类
EXERCISE_MAP = {
    "SQUAT": Squat,
    "BICEP_CURL": BicepCurl,
    "DEADLIFT": Deadlift,
    "PUSH_UP": PushUp,
    "BENCH_PRESS": BenchPress
}

app = FastAPI()

# --- 登录配置：这些是全局常量 ---
SECRET_KEY = "GESHUAI_SUPER_SECRET_KEY" # 你的“签名印章”
ALGORITHM = "HS256"                     # 签名算法
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24   # 令牌有效期：1天（1440分钟）

# --- 新增：系统启动时的数据库初始化 ---
# 这一行是全栈地基：启动时检查是否存在 aifitness.db，如果没有，按 models.py 自动建表
models.Base.metadata.create_all(bind=database.engine)

# --- 新增：密码加密器配置 ---
# 采用 bcrypt 强加密算法，弃用过时的加密方式
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================================
#           RESTful API 路由区 (HTTP协议)
# ==========================================

@app.post("/register", response_model=schemas.UserOut) # response_model=schemas.UserOut 极其关键，确保不泄露加密密码
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """
    用户注册接口：接收前端 JSON 表单，哈希加密密码后存入数据库
    """
    # 1. 查重：去数据库里找有没有同名的用户
    db_user = db.query(models.User).filter(models.User.username == user.username).first() 
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 2. 加密：把明文密码变成哈希乱码
    hashed_pwd = pwd_context.hash(user.password)
    
    # 3. 实例化：创建一个数据库 ORM 对象
    new_user = models.User(username=user.username, hashed_password=hashed_pwd)
    
    # 4. 提交：把对象塞进数据库并保存
    db.add(new_user)
    db.commit()
    db.refresh(new_user) 
    
    # 5. 返回：自动过滤掉密码发回前端
    return new_user


# ==========================================
#           AI 引擎核心区 (WebSocket协议)
# ==========================================

# 初始化 MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: str, 
    exercise: str,  # 要求前端在连 WebSocket 时，通过 URL 告诉后端要练什么动作
    db: Session = Depends(database.get_db)
):
    # 引入token（接受凭证能力），并连接数据库（验证用户身份）
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
            
    # --- 【新增】软件工程重构：动态工厂模式实例化动作对象 ---
    exercise_key = exercise.upper() 
    
    if exercise_key not in EXERCISE_MAP:
        print(f"不支持的动作类型: {exercise_key}")
        await websocket.close(code=1003) 
        return
        
    current_exercise = EXERCISE_MAP[exercise_key]()
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # --- 1. 解码原始画面 (frame_raw) ---
            image_bytes = base64.b64decode(data)
            image_stream = io.BytesIO(image_bytes)
            file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
            frame_raw = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            # --- 2. 三明治第一层：创建镜像工作空间 (frame_workspace) ---
            frame_workspace = cv2.flip(frame_raw, 1)

            # 【修正点 1】：AI 推理必须基于 workspace，否则坐标会错乱
            frame_rgb = cv2.cvtColor(frame_workspace, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)
            
            if results.pose_landmarks:
                # 【美化操作 A】：保留骨架绘制，这代表了 AI 的科技感
                mp_drawing.draw_landmarks(frame_workspace, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # 【美化操作 B】：核心重构！
                # 我们调用 process_frame 来计算计数和状态，但传入 frame_workspace.copy()
                # 这样 OpenCV 的 cv2.putText 产生的“绿字”只会画在副本上，不会污染我们要发回前端的 frame_workspace
                current_exercise.process_frame(results.pose_landmarks.landmark, frame_workspace.copy())

            # --- 3. 三明治最后一层：为了抵消前端翻转，这里再翻转回去 ---
            # 此时的 frame_workspace 只有骨架，没有 OSD 文字
            frame_final = cv2.flip(frame_workspace, 1)   
            
            # --- 4. 编码发回 ---
            _, buffer = cv2.imencode('.jpg', frame_final)
            b64_string = base64.b64encode(buffer).decode('utf-8')

            # 注意：这里的 feedback/counter/stage 依然正常发送，前端可以直接调用显示
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
            print(f"✅ 自动存盘：{user.username} 完成了 {current_exercise.counter} 个 {exercise_key}")


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


# 身份验证依赖
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
    return user

# 保存记录
@app.post("/records") 
def create_record(record: schemas.RecordCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    new_record = models.WorkoutRecord( 
        exercise_type = record.exercise_type,
        count = record.count,
        user_id = current_user.id
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return{"message": "记录保存成功", "record_id": new_record.id, "user": current_user.username}

# 获取当前用户的所有训练记录
@app.get("/records/my")
def get_my_records(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    获取当前登录用户的所有历史记录，并按时间倒序排列
    """
    records = db.query(models.WorkoutRecord)\
                .filter(models.WorkoutRecord.user_id == current_user.id)\
                .order_by(models.WorkoutRecord.timestamp.desc())\
                .all()
    return records

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)