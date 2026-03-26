from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
import enum
import datetime as dt
from database import Base

class RoleEnum(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    name = Column(String(50), nullable=False)

    # Profile fields
    avatar_url = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)

    # Relationships
    teaching_courses = relationship("Course", back_populates="teacher")
    enrollments = relationship("Enrollment", back_populates="student")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    credits = Column(Integer, nullable=False, default=3)
    capacity = Column(Integer, nullable=False, default=50)

    # Schedule fields (single class session info)
    class_time = Column(String(100), nullable=True)
    class_location = Column(String(100), nullable=True)

    # Relationships
    teacher = relationship("User", back_populates="teaching_courses")
    enrollments = relationship("Enrollment", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float, nullable=True)

    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    notif_type = Column(String(50), nullable=False)  # announcement/direct/grade/enrollment...
    title = Column(String(150), nullable=True)
    content = Column(String(1000), nullable=False)

    related_course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    related_enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=True)

    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
