from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import os
import logging
import sqlite3
from sqlalchemy import text
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from io import BytesIO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# JWT配置
SECRET_KEY = "your-secret-key"  # 在生产环境中应该使用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./merchants.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy 模型
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(String, unique=True, index=True)
    merchant_name = Column(String)
    institution = Column(String)
    institution_id = Column(String)
    transaction_count = Column(Integer)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 检查数据库连接
def check_db_connection():
    try:
        conn = sqlite3.connect('merchants.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='merchants'")
        table_exists = cursor.fetchone() is not None
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM merchants")
            count = cursor.fetchone()[0]
            logger.info(f"数据库连接成功，merchants表存在，当前记录数: {count}")
        else:
            logger.warning("数据库连接成功，但merchants表不存在")
        conn.close()
    except Exception as e:
        logger.error(f"数据库连接检查失败: {str(e)}")

# 在应用启动时检查数据库
check_db_connection()

# Pydantic 模型
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    is_admin: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class MerchantBase(BaseModel):
    merchant_id: str
    merchant_name: str
    institution: str
    institution_id: str
    transaction_count: int

class MerchantResponse(MerchantBase):
    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    items: List[MerchantResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    data_date: str

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 密码验证
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# 用户认证
def authenticate_user(db: SessionLocal, username: str, password: str):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: SessionLocal = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(UserDB).filter(UserDB.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserDB = Depends(get_current_user)):
    return current_user

# 路由
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"message": "Welcome to Merchant Query System"}

@app.get("/api/merchants/", response_model=PaginatedResponse)
def get_merchants(
    institution_id: Optional[str] = None,
    institution: Optional[str] = None,
    merchant_id: Optional[str] = None,
    merchant_name: Optional[str] = None,
    min_transactions: Optional[int] = None,
    max_transactions: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
    db: SessionLocal = Depends(get_db)
):
    # 记录查询参数
    logger.info(f"开始查询 - 参数: institution_id={institution_id}, institution={institution}, merchant_id={merchant_id}, merchant_name={merchant_name}, page={page}, page_size={page_size}")
    
    # 构建查询
    query = db.query(Merchant)
    
    # 记录SQL查询
    conditions = []
    
    # 机构查询
    if institution_id:
        # 使用精确匹配机构号
        conditions.append(Merchant.institution_id == institution_id)
        logger.info(f"添加条件: institution_id = {institution_id}")
    
    if institution:
        # 使用精确匹配机构名称
        conditions.append(Merchant.institution == institution)
        logger.info(f"添加条件: institution = {institution}")
    
    # 商户查询
    if merchant_id:
        # 使用精确匹配商户号
        conditions.append(Merchant.merchant_id == merchant_id)
        logger.info(f"添加条件: merchant_id = {merchant_id}")
    
    if merchant_name:
        # 使用模糊匹配商户名称
        conditions.append(Merchant.merchant_name.like(f"%{merchant_name}%"))
        logger.info(f"添加条件: merchant_name like %{merchant_name}%")
    
    # 应用所有条件（使用OR连接）
    if conditions:
        from sqlalchemy import or_
        query = query.filter(or_(*conditions))
        logger.info("使用OR条件连接所有查询条件")
    
    if min_transactions is not None:
        query = query.filter(Merchant.transaction_count >= min_transactions)
        logger.info(f"添加条件: transaction_count >= {min_transactions}")
    if max_transactions is not None:
        query = query.filter(Merchant.transaction_count <= max_transactions)
        logger.info(f"添加条件: transaction_count <= {max_transactions}")
    
    # 计算总记录数
    total_count = query.count()
    logger.info(f"查询结果总记录数: {total_count}")
    
    # 应用分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    logger.info(f"应用分页: offset={offset}, limit={page_size}")
    
    # 执行查询
    try:
        # 记录当前数据库中的一些示例数据
        sample_data = db.query(Merchant).limit(5).all()
        logger.info("数据库中的示例数据:")
        for data in sample_data:
            logger.info(f"机构: {data.institution}, 机构号: {data.institution_id}, 商户名: {data.merchant_name}, 商户号: {data.merchant_id}")

        results = query.all()
        logger.info(f"查询执行成功，找到 {len(results)} 条记录")
        
        # 记录一些示例数据
        if results:
            logger.info(f"查询结果示例: {results[0].__dict__}")
            
            # 记录数据统计信息
            transaction_counts = [r.transaction_count for r in results]
            if transaction_counts:
                logger.info(f"交易笔数统计 - 最小: {min(transaction_counts)}, 最大: {max(transaction_counts)}, 平均: {sum(transaction_counts)/len(transaction_counts):.2f}")
        else:
            # 如果没有结果，尝试查询所有数据
            all_results = db.query(Merchant).all()
            logger.info(f"当前数据库总记录数: {len(all_results)}")
            if all_results:
                logger.info(f"数据库示例数据: {all_results[0].__dict__}")
        
        # 设置数据日期
        data_date = "4月27日"  # 这里可以根据实际情况设置
        
        # 返回结果和分页信息
        return {
            "items": results,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "data_date": data_date
        }
    except Exception as e:
        logger.error(f"查询执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.get("/api/merchants/{merchant_id}", response_model=MerchantResponse)
def get_merchant(merchant_id: str, db: SessionLocal = Depends(get_db)):
    logger.info(f"开始查询商户详情 - 商户号: {merchant_id}")
    try:
        merchant = db.query(Merchant).filter(Merchant.merchant_id == merchant_id).first()
        if merchant is None:
            logger.warning(f"未找到商户号: {merchant_id}")
            raise HTTPException(status_code=404, detail="Merchant not found")
        logger.info(f"找到商户: {merchant.__dict__}")
        return merchant
    except Exception as e:
        logger.error(f"查询商户详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.post("/api/upload/")
async def upload_file(file: UploadFile = File(...), current_user: UserDB = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # 检查文件格式
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="Only Excel files are allowed")
        
        # 尝试从文件名中提取日期（如果文件名符合格式）
        formatted_date = None
        filename = file.filename
        logger.info(f"上传文件名: {filename}")
        
        if filename.startswith("未月活-") and filename.endswith(".xlsx"):
            try:
                # 修复日期提取逻辑
                date_str = filename[3:-5]  # 提取 MMDD 部分
                logger.info(f"提取的日期字符串: {date_str}")
                
                # 处理可能的负号
                if date_str.startswith('-'):
                    date_str = date_str[1:]  # 去掉负号
                    logger.info(f"去掉负号后的日期字符串: {date_str}")
                
                # 确保日期字符串长度正确
                if len(date_str) == 4:
                    month = int(date_str[:2])
                    day = int(date_str[2:])
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        formatted_date = f"{month}月{day}日"
                        logger.info(f"从文件名解析出日期: {formatted_date}")
                    else:
                        logger.warning(f"解析出的月份或日期无效: 月={month}, 日={day}")
                else:
                    logger.warning(f"日期字符串长度不正确: {date_str}, 长度: {len(date_str)}")
            except (ValueError, IndexError) as e:
                logger.error(f"解析文件名日期失败: {str(e)}")
                pass  # 如果解析失败，继续使用原有功能
        else:
            logger.info(f"文件名不符合格式要求，不解析日期")
        
        # 读取Excel文件
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # 记录上传的数据信息
        logger.info(f"上传文件: {file.filename}")
        logger.info(f"数据形状: {df.shape}")
        logger.info(f"列名: {df.columns.tolist()}")
        
        # 重命名列（如果需要）
        column_mapping = {
            'counts': '有效交易笔数'
        }
        df = df.rename(columns=column_mapping)
        
        # 验证必要的列
        required_columns = ['商户号', '商户名称', '机构', '机构号', '有效交易笔数']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [col for col in required_columns if col not in df.columns]
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # 清空现有数据
        db = SessionLocal()
        db.query(Merchant).delete()
        logger.info("已清空现有数据")
        
        # 插入新数据
        success_count = 0
        for _, row in df.iterrows():
            try:
                merchant = Merchant(
                    merchant_id=str(row['商户号']),
                    merchant_name=str(row['商户名称']),
                    institution=str(row['机构']),
                    institution_id=str(row['机构号']),
                    transaction_count=int(row['有效交易笔数'])
                )
                db.add(merchant)
                success_count += 1
                if success_count % 100 == 0:  # 每100条记录记录一次
                    logger.info(f"已处理 {success_count} 条记录")
            except Exception as e:
                logger.error(f"处理行数据失败: {row}, 错误: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing row: {str(e)}"
                )
        
        # 如果成功解析了日期，则更新数据日期
        if formatted_date:
            try:
                logger.info(f"准备更新数据日期为: {formatted_date}")
                # 检查data_date表是否存在，如果不存在则创建
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS data_date (
                        id INTEGER PRIMARY KEY,
                        date TEXT
                    )
                """))
                logger.info("确保data_date表存在")
                
                # 更新或插入数据日期
                db.execute(text("""
                    INSERT OR REPLACE INTO data_date (id, date)
                    VALUES (1, :date)
                """), {"date": formatted_date})
                logger.info("执行更新数据日期SQL")
                
                db.commit()
                logger.info("提交事务")
                
                # 验证数据日期是否更新成功
                result = db.execute(text("SELECT date FROM data_date WHERE id = 1")).fetchone()
                logger.info(f"验证数据日期更新结果: {result}")
                
                if result and result[0] == formatted_date:
                    logger.info(f"数据日期更新成功: {formatted_date}")
                else:
                    logger.warning(f"数据日期更新可能失败，当前值: {result[0] if result else 'None'}")
            except Exception as e:
                logger.error(f"更新数据日期失败: {str(e)}")
                # 继续执行，不影响上传功能
        else:
            logger.info("没有解析出日期，不更新数据日期")
        
        logger.info(f"成功上传 {success_count} 条记录")
        
        # 验证数据是否成功写入
        check_db_connection()
        
        return {
            "message": f"Data uploaded successfully, {success_count} records processed",
            "data_date": formatted_date if formatted_date else "未更新"
        }
    except Exception as e:
        logger.error(f"上传错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data-date")
async def get_data_date(db: SessionLocal = Depends(get_db)):
    try:
        logger.info("开始获取数据日期")
        # 检查data_date表是否存在，如果不存在则创建
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS data_date (
                id INTEGER PRIMARY KEY,
                date TEXT
            )
        """))
        logger.info("确保data_date表存在")
        
        # 查询数据日期
        result = db.execute(text("SELECT date FROM data_date WHERE id = 1")).fetchone()
        logger.info(f"查询数据日期结果: {result}")
        
        if result and result[0]:
            logger.info(f"返回数据日期: {result[0]}")
            return {"date": result[0]}
        
        # 如果没有设置日期，设置默认值并返回
        default_date = "4月27日"  # 设置默认日期
        logger.info(f"没有找到数据日期，设置默认值: {default_date}")
        db.execute(text("""
            INSERT OR REPLACE INTO data_date (id, date)
            VALUES (1, :date)
        """), {"date": default_date})
        db.commit()
        logger.info("已更新默认数据日期")
        
        return {"date": default_date}
    except Exception as e:
        logger.error(f"获取数据日期失败: {str(e)}")
        return {"date": "4月27日"}  # 即使出错也返回默认日期

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 