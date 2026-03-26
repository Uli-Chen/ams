from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import User, Course, Enrollment, RoleEnum, Notification
from schemas import CourseResponse, EnrollmentResponse, TeacherCourseUpdate
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


@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_teacher_course(
    course_id: int,
    payload: TeacherCourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.teacher])),
):
    result = await db.execute(select(Course).where(Course.id == course_id, Course.teacher_id == current_user.id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No changes provided")

    for key, value in update_data.items():
        setattr(course, key, value)

    course.teacher_name = current_user.name
    await db.commit()
    await db.refresh(course)
    course.teacher_name = current_user.name
    return course

@router.get("/courses/{course_id}/students")
async def get_course_students(course_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.teacher]))):
    # Verify teacher owns this course
    res_c = await db.execute(select(Course).where(Course.id == course_id, Course.teacher_id == current_user.id))
    course = res_c.scalars().first()
    if not course:
        raise HTTPException(status_code=403, detail="Not your course")
        
    res = await db.execute(
        select(Enrollment, User)
        .join(User, Enrollment.student_id == User.id)
        .where(Enrollment.course_id == course_id)
    )
    students = []
    for enrollment, student in res.all():
        students.append({
            "enrollment_id": enrollment.id,
            "student_id": student.id,
            "student_name": student.name,
            "grade": enrollment.grade
        })

    # Return course schedule together, so UI can display timetable info
    return {
        "course": {
            "course_id": course.id,
            "course_name": course.name,
            "class_time": course.class_time,
            "class_location": course.class_location,
        },
        "students": students,
    }

@router.put("/enrollments/{enrollment_id}/grade")
async def update_grade(enrollment_id: int, payload: GradeUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.teacher]))):
    res_e = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id).options(selectinload(Enrollment.course)))
    enrollment = res_e.scalars().first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
        
    if enrollment.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your course")
    
    old_grade = enrollment.grade
    enrollment.grade = payload.grade

    # Notify the student only when grade is first published (old was null)
    if old_grade is None:
        new_notif = Notification(
            sender_id=current_user.id,
            recipient_id=enrollment.student_id,
            notif_type="grade",
            title="成绩已公布 / Grade Posted",
            content=f"课程 {enrollment.course.name} 成绩：{payload.grade}",
            related_course_id=enrollment.course_id,
            related_enrollment_id=enrollment.id,
            is_read=False,
        )
        db.add(new_notif)

    await db.commit()
    return {"message": "Grade updated"}
