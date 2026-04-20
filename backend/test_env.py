import sys
import time

# 强制刷新输出缓冲区
print("1. 脚本启动成功...", flush=True)

try:
    print("2. 正在尝试导入 cv2...", flush=True)
    import cv2
    print(f"✅ OpenCV 加载成功，版本: {cv2.__version__}", flush=True)
    
    print("3. 正在尝试导入 mediapipe...", flush=True)
    import mediapipe as mp
    print("✅ MediaPipe 加载成功", flush=True)
    
    print("4. 正在初始化 Pose 引擎 (这一步最耗时)...", flush=True)
    # 检查MediaPipe版本和API
    if hasattr(mp, 'solutions'):
        # 旧API (MediaPipe < 0.10)
        mp_pose = mp.solutions.pose
        with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
            print("🚀 MediaPipe 姿态引擎完全就绪！(使用旧API)", flush=True)
    else:
        # 新API (MediaPipe >= 0.10)
        print("⚠️  MediaPipe >= 0.10 detected, solutions module moved to tasks. 需要下载模型文件才能使用姿势检测。", flush=True)
        print("🚀 MediaPipe 导入成功，但姿势功能需要额外配置。", flush=True)

except ImportError as e:
    print(f"❌ 模块缺失错误: {e}", flush=True)
except Exception as e:
    print(f"❌ 运行异常: {e}", flush=True)

print("5. 测试结束。", flush=True)