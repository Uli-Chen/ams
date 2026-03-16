from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User, Course, Enrollment, RoleEnum
from database import get_db
from security import require_role

router = APIRouter()

@router.post("/courses/{course_id}/enroll")
async def enroll_course(course_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.student]))):
    res_c = await db.execute(select(Course).where(Course.id == course_id))
    course = res_c.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    res_e = await db.execute(select(Enrollment).where(Enrollment.course_id == course_id, Enrollment.student_id == current_user.id))
    if res_e.scalars().first():
        raise HTTPException(status_code=400, detail="Already enrolled")
        
    # check capacity
    res_count = await db.execute(select(Enrollment).where(Enrollment.course_id == course_id))
    current_count = len(res_count.scalars().all())
    if current_count >= course.capacity:
        raise HTTPException(status_code=400, detail="Course is full")
        
    new_enrollment = Enrollment(student_id=current_user.id, course_id=course_id)
    db.add(new_enrollment)
    await db.commit()
    return {"message": "Enrolled successfully"}

@router.delete("/courses/{course_id}/unenroll")
async def unenroll_course(course_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.student]))):
    res_e = await db.execute(select(Enrollment).where(Enrollment.course_id == course_id, Enrollment.student_id == current_user.id))
    enrollment = res_e.scalars().first()
    if not enrollment:
        raise HTTPException(status_code=400, detail="Not enrolled in this course")
        
    await db.delete(enrollment)
    await db.commit()
    return {"message": "Unenrolled successfully"}

@router.get("/my-courses")
async def get_my_courses(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.student]))):
    res = await db.execute(
        select(Enrollment, Course)
        .join(Course, Enrollment.course_id == Course.id)
        .where(Enrollment.student_id == current_user.id)
    )
    data = []
    for enrollment, course in res.all():
        # Get teacher's name
        teacher_name = None
        if course.teacher_id:
            res_t = await db.execute(select(User).where(User.id == course.teacher_id))
            teacher = res_t.scalars().first()
            if teacher:
                teacher_name = teacher.name
                
        data.append({
            "course_id": course.id,
            "course_name": course.name,
            "credits": course.credits,
            "teacher_name": teacher_name,
            "grade": enrollment.grade
        })
    return data
