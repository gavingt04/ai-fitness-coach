# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 定义数据库文件的存储路径（SQLite 会在本地生成一个文件）
SQLALCHEMY_DATABASE_URL = "sqlite:///./aifitness.db"

# 2. 创建数据库引擎
# connect_args={"check_same_thread": False} 是 SQLite 特有的，允许 FastAPI 的多线程访问
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. 创建会话工厂，用于后续生产数据库连接
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 创建所有数据库模型的基类，models.py 里的 User 类会继承它
Base = declarative_base()

# 5. 定义一个依赖项函数，用于在 FastAPI 接口中获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # 请求结束后自动关闭连接，防止内存泄漏