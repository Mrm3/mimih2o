from typing import List, Optional
import os
import re
import math
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 安全配置
SECRET_KEY = "your-secret-key"  # 在生产环境中应该使用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 数据库连接
def get_db():
    db = sqlite3.connect("merchants.db")
    db.row_factory = sqlite3.Row
    return db

# 用户模型
class User(BaseModel):
    username: str
    password: str

# 创建用户表
def init_db():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
    """)
    # 添加默认用户
    hashed_password = pwd_context.hash("admin")
    db.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
              ("admin", hashed_password))
    db.commit()
    db.close()

# 初始化数据库
init_db()

# 验证用户
def verify_user(username: str, password: str):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    db.close()
    if user and pwd_context.verify(password, user["password"]):
        return True
    return False

# 创建访问令牌
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 获取当前用户
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    return username

# 登录接口
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if verify_user(form_data.username, form_data.password):
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误",
        headers={"WWW-Authenticate": "Bearer"},
    )

# 上传文件接口
@app.post("/api/upload/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    try:
        # 保存上传的文件
        file_path = "merchant_data.xlsx"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 连接到SQLite数据库
        db = get_db()
        
        # 创建merchants表（如果不存在）
        db.execute("""
        CREATE TABLE IF NOT EXISTS merchants (
            merchant_id TEXT PRIMARY KEY,
            merchant_name TEXT,
            institution TEXT,
            institution_id TEXT,
            transaction_count INTEGER
        )
        """)
        
        # 清空现有数据
        db.execute("DELETE FROM merchants")
        
        # 插入新数据
        for _, row in df.iterrows():
            db.execute("""
            INSERT INTO merchants (merchant_id, merchant_name, institution, institution_id, transaction_count)
            VALUES (?, ?, ?, ?, ?)
            """, (
                str(row['商户号']),
                str(row['商户名称']),
                str(row['机构']),
                str(row['机构号']),
                int(row['有效交易笔数'])
            ))
        
        db.commit()
        db.close()
        
        return {"message": "文件上传成功，数据已更新"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"上传失败: {str(e)}"}
        )

# 商户模型
class Merchant(BaseModel):
    merchant_id: str
    merchant_name: str
    institution: str
    institution_id: str
    transaction_count: int

class MerchantResponse(BaseModel):
    items: List[Merchant]
    total: int
    page: int
    page_size: int
    total_pages: int
    data_date: str = ""  # 添加数据日期字段

@app.get("/api/merchants/", response_model=MerchantResponse)
async def get_merchants(
    institution_id: Optional[str] = None,
    institution: Optional[str] = None,
    merchant_id: Optional[str] = None,
    merchant_name: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
):
    # 从文件名中提取数据日期
    data_date = ""
    if os.path.exists("merchant_data.xlsx"):
        filename = "merchant_data.xlsx"
        # 尝试从文件名中提取日期
        match = re.search(r'(\d{2})(\d{2})', filename)
        if match:
            month, day = match.groups()
            data_date = f"{month}月{day}日"

    # 构建查询条件
    db = get_db()
    query = "SELECT * FROM merchants WHERE 1=1"
    params = []
    
    if institution_id:
        query += " AND (institution_id LIKE ? OR institution LIKE ?)"
        params.extend([f"%{institution_id}%", f"%{institution_id}%"])
    if institution:
        query += " AND (institution_id LIKE ? OR institution LIKE ?)"
        params.extend([f"%{institution}%", f"%{institution}%"])
    if merchant_id:
        query += " AND (merchant_id LIKE ? OR merchant_name LIKE ?)"
        params.extend([f"%{merchant_id}%", f"%{merchant_id}%"])
    if merchant_name:
        query += " AND (merchant_id LIKE ? OR merchant_name LIKE ?)"
        params.extend([f"%{merchant_name}%", f"%{merchant_name}%"])

    # 获取总记录数
    count_query = f"SELECT COUNT(*) FROM ({query})"
    total = db.execute(count_query, params).fetchone()[0]

    # 添加分页
    query += " LIMIT ? OFFSET ?"
    params.extend([page_size, (page - 1) * page_size])

    # 执行查询
    cursor = db.execute(query, params)
    merchants = [dict(row) for row in cursor.fetchall()]
    db.close()

    return MerchantResponse(
        items=merchants,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
        data_date=data_date
    ) 