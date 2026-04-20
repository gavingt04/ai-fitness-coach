from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # 【新增】引入 func 用来获取数据库当前时间
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)

    records = relationship("WorkoutRecord", back_populates="owner")

class WorkoutRecord(Base):
    __tablename__ = "workout_records"

    id = Column(Integer, primary_key=True, index=True)
    exercise_type = Column(String) 
    count = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    
   
    # server_default=func.now() 会让 SQLite 在存盘时自动帮你填上时间，不用你动写逻辑
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="records")