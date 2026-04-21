# backend/schemas.py
from pydantic import BaseModel
from typing import Optional

# 注册时，前端发送过来的数据格式
class UserCreate(BaseModel):
    username: str
    password: str

# 返回给前端的用户信息格式（过滤掉密码）
class UserOut(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True # 允许从 SQLAlchemy 模型转换


class RecordCreate(BaseModel): #记录前端传回数据的格式
    exercise_type: str
    count: int
    issues: Optional[str] = ""  # 【新增】允许前端上传本次的错误总结