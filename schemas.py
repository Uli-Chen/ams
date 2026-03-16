from pydantic import BaseModel, Field
from typing import Optional, List
from models import RoleEnum

class UserBase(BaseModel):
    username: str
    name: str
    role: RoleEnum

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    credits: int = Field(3, ge=1, le=10, description="Credits between 1 and 10")
    capacity: int = Field(50, ge=1, le=500, description="Capacity between 1 and 500")

class CourseCreate(CourseBase):
    teacher_id: Optional[int] = None

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    credits: Optional[int] = Field(None, ge=1, le=10)
    capacity: Optional[int] = Field(None, ge=1, le=500)
    teacher_id: Optional[int] = None

class CourseResponse(CourseBase):
    id: int
    teacher_id: Optional[int] = None
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True

class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    grade: Optional[float] = None
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
