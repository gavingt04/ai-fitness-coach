import asyncio
import websockets
import cv2
import base64
import json
import requests
import numpy as np

# --- 客户端配置 ---
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"
USERNAME = "testuser"   # 替换为你刚才注册的账号
PASSWORD = "123456"     # 替换为你的密码
EXERCISE = "SQUAT"      # 试试换成 PUSHUP 或 DEADLIFT！

async def test_full_flow():
    # 1. 模拟前端登录拿 Token
    print(f"🔄 1. 正在尝试登录 {USERNAME}...")
    response = requests.post(f"{API_URL}/login", data={"username": USERNAME, "password": PASSWORD})
    
    if response.status_code != 200:
        print("❌ 登录失败，请检查账号密码！")
        return
        
    token = response.json().get("access_token")
    print(f"✅ 拿到合法通行证 (Token): {token[:15]}...\n")

    # 2. 拼接 WebSocket 地址 (触发后端的动态工厂模式)
    ws_endpoint = f"{WS_URL}?token={token}&exercise={EXERCISE}"
    print(f"🚀 2. 正在连接 AI 引擎，请求动作: {EXERCISE}...")

    # 3. 建立双向流连接
    async with websockets.connect(ws_endpoint) as websocket:
        print("✅ 连接成功！正在唤醒本地摄像头...\n")
        cap = cv2.VideoCapture(1) # 0 为默认笔记本摄像头

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

               # --- 发送端：将摄像头画面转成 Base64 发给后端 ---
                _, buffer = cv2.imencode('.jpg', frame)
                b64_str = base64.b64encode(buffer).decode('utf-8')
                await websocket.send(b64_str)  # ✅ 改为 send()

                # --- 接收端：接收后端 AI 处理完的画面和计分板 ---
                response_data = await websocket.recv() # ✅ 改为 recv()

                # 【关键补回】：将文本解析成 Python 字典，否则下面打印会找不到 result！
                result = json.loads(response_data)

                # 在控制台实时打印数据
                print(f"\r📊 动作: {EXERCISE} | 阶段: {result['stage']} | 战绩: {result['counter']} 次", end="")

                # 解码并显示 AI 渲染后的画面
                img_data = base64.b64decode(result['image'])
                nparr = np.frombuffer(img_data, np.uint8)
                img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                cv2.imshow("AI Fitness Test Client (Press 'q' to quit)", img_np)
                
                # 按 'q' 键退出测试
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("\n\n🔌 3. 模拟用户关闭网页，断开连接。请去后端终端查看是否触发 finally 存盘逻辑！")

if __name__ == "__main__":
    asyncio.run(test_full_flow())