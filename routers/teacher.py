from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import User, Course, Enrollment, RoleEnum
from schemas import CourseResponse, EnrollmentResponse
from database import get_db
from security import require_role
from pydantic import BaseModel, Field

router = APIRouter()

class GradeUpdate(BaseModel):
    grade: float = Field(..., ge=0, le=100, description="Grade must be between 0 and 100")

@router.get("/my-courses", response_model=list[CourseResponse])
async def get_teacher_courses(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.teacher]))):
    result = await db.execute(select(Course).where(Course.teacher_id == current_user.id))
    courses = result.scalars().all()
    for c in courses:
        c.teacher_name = current_user.name
    return courses

@router.get("/courses/{course_id}/students", response_model=list[dict])
async def get_course_students(course_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.teacher]))):
    # Verify teacher owns this course
    res_c = await db.execute(select(Course).where(Course.id == course_id, Course.teacher_id == current_user.id))
    if not res_c.scalars().first():
        raise HTTPException(status_code=403, detail="Not your course")
        
    res = await db.execute(
        select(Enrollment, User)
        .join(User, Enrollment.student_id == User.id)
        .where(Enrollment.course_id == course_id)
    )
    data = []
    for enrollment, student in res.all():
        data.append({
            "enrollment_id": enrollment.id,
            "student_id": student.id,
            "student_name": student.name,
            "grade": enrollment.grade
        })
    return data

@router.put("/enrollments/{enrollment_id}/grade")
async def update_grade(enrollment_id: int, payload: GradeUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.teacher]))):
    res_e = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id).options(selectinload(Enrollment.course)))
    enrollment = res_e.scalars().first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
        
    if enrollment.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your course")
        
    enrollment.grade = payload.grade
    await db.commit()
    return {"message": "Grade updated"}
