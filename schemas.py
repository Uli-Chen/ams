from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models import RoleEnum

class UserBase(BaseModel):
    username: str
    name: str
    role: RoleEnum

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    avatar_url: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    credits: int = Field(3, ge=1, le=10, description="Credits between 1 and 10")
    capacity: int = Field(50, ge=1, le=500, description="Capacity between 1 and 500")
    class_time: Optional[str] = Field(None, max_length=100, description="Class time / schedule")
    class_location: Optional[str] = Field(None, max_length=100, description="Class location / room")

class CourseCreate(CourseBase):
    teacher_id: Optional[int] = None

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    credits: Optional[int] = Field(None, ge=1, le=10)
    capacity: Optional[int] = Field(None, ge=1, le=500)
    teacher_id: Optional[int] = None
    class_time: Optional[str] = Field(None, max_length=100)
    class_location: Optional[str] = Field(None, max_length=100)


class TeacherCourseUpdate(BaseModel):
    class_time: Optional[str] = Field(None, max_length=100)
    class_location: Optional[str] = Field(None, max_length=100)

class CourseResponse(CourseBase):
    id: int
    teacher_id: Optional[int] = None
    teacher_name: Optional[str] = None
    enrolled_count: Optional[int] = None
    remaining_capacity: Optional[int] = None

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


class UserMeResponse(BaseModel):
    id: int
    username: str
    name: str
    role: RoleEnum
    avatar_url: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone_number: Optional[str] = Field(None, min_length=5, max_length=20)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=6, max_length=255)
    new_password: str = Field(..., min_length=6, max_length=255)


class NotificationResponse(BaseModel):
    id: int
    sender_name: Optional[str] = None
    notif_type: str
    title: Optional[str] = None
    content: str
    related_course_id: Optional[int] = None
    related_enrollment_id: Optional[int] = None
    is_read: bool
    created_at: datetime


class DirectMessageRequest(BaseModel):
    receiver_id: int
    content: str = Field(..., min_length=1, max_length=1000)
    related_course_id: Optional[int] = None


class AnnouncementCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    content: str = Field(..., min_length=1, max_length=1000)
