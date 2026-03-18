from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Dict

from src.auth.security import get_password_hash, verify_password, create_access_token
from src.auth.dependencies import get_current_user

# 创建路由器 - 这是这个文件唯一应该创建和导出的对象
router = APIRouter(prefix="/auth", tags=["认证"])

# 模拟用户数据库
fake_users_db: Dict[str, dict] = {}

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    email: EmailStr
    id: int

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    if user.email in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    user_id = len(fake_users_db) + 1
    hashed_password = get_password_hash(user.password)
    fake_users_db[user.email] = {
        "id": user_id,
        "email": user.email,
        "hashed_password": hashed_password,
    }
    return {"msg": "用户创建成功", "user_id": user_id}

@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db_user = fake_users_db.get(user.email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(db_user["id"])})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user_id: str = Depends(get_current_user)):
    for user_data in fake_users_db.values():
        if str(user_data["id"]) == current_user_id:
            return UserOut(email=user_data["email"], id=user_data["id"])
    raise HTTPException(status_code=404, detail="用户不存在")
