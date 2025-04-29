from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, UserDB, get_password_hash

# 数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./merchants.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建管理员用户
def create_admin_user():
    db = SessionLocal()
    try:
        # 检查是否已存在管理员用户
        admin = db.query(UserDB).filter(UserDB.username == "admin").first()
        if not admin:
            admin_user = UserDB(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print("管理员用户创建成功！")
            print("用户名: admin")
            print("密码: admin123")
        else:
            print("管理员用户已存在")
    except Exception as e:
        print(f"创建管理员用户失败: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user() 