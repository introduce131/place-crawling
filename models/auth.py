from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List

# 회원가입 요청 바디 모델
class SignupRequest(BaseModel):
    guest_id: Optional[str] = Field(None, description="게스트 ID (게스트에서 회원으로 전환할 때만 필요)")
    email: EmailStr = Field(..., description="사용자 이메일 (고유)")
    password: str = Field(..., description="로그인용 비밀번호")
    nickname: str = Field(..., description="사용자 닉네임")
    birth: str = Field(..., description="출생일 (YYYYMMDD)")

# 회원가입 응답 모델
class SignupResponse(BaseModel):
    user_id: str
    email: EmailStr
    nickname: str
    birth: str
    is_guest: bool

# 로그인 요청 모델
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# 로그인 응답 모델
class LoginResponse(BaseModel):
    user_id: str
    email: EmailStr
    nickname: str
    birth: str
    is_guest: bool