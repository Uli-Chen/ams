from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update
from models import User, Course, Enrollment, RoleEnum
from schemas import UserCreate, UserResponse, CourseCreate, CourseResponse, CourseUpdate
from database import get_db
from security import require_role
from routers.auth import get_password_hash

router = APIRouter()

@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.admin]))):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_dict = user.model_dump()
    hashed_password = get_password_hash(hashed_dict.pop("password"))
    new_user = User(**hashed_dict, hashed_password=hashed_password)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.admin]))):
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.role == RoleEnum.admin:
        # Prevent deleting the last admin
        admin_count = await db.execute(select(User).where(User.role == RoleEnum.admin))
        if len(admin_count.scalars().all()) <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin")
            
    if user.role == RoleEnum.student:
        await db.execute(delete(Enrollment).where(Enrollment.student_id == user_id))
    elif user.role == RoleEnum.teacher:
        await db.execute(update(Course).where(Course.teacher_id == user_id).values(teacher_id=None))
        
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return {"message": "User deleted successfully"}

@router.post("/courses", response_model=CourseResponse)
async def create_course(course: CourseCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.admin]))):
    course_data = course.model_dump()
    teacher_id = course_data.get("teacher_id")
    if teacher_id:
        res_t = await db.execute(select(User).where(User.id == teacher_id, User.role == RoleEnum.teacher))
        if not res_t.scalars().first():
            raise HTTPException(status_code=400, detail="Invalid teacher")
            
    new_course = Course(**course_data)
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    return new_course

@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(course_id: int, course: CourseUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.admin]))):
    res = await db.execute(select(Course).where(Course.id == course_id))
    target_course = res.scalars().first()
    if not target_course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    update_data = course.model_dump(exclude_unset=True)
    
    if "teacher_id" in update_data and update_data["teacher_id"] is not None:
        res_t = await db.execute(select(User).where(User.id == update_data["teacher_id"], User.role == RoleEnum.teacher))
        if not res_t.scalars().first():
            raise HTTPException(status_code=400, detail="Invalid teacher")
            
    for key, value in update_data.items():
        setattr(target_course, key, value)
        
    await db.commit()
    await db.refresh(target_course)
    return target_course

@router.delete("/courses/{course_id}")
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.admin]))):
    res = await db.execute(select(Course).where(Course.id == course_id))
    course = res.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    await db.execute(delete(Enrollment).where(Enrollment.course_id == course_id))
    await db.execute(delete(Course).where(Course.id == course_id))
    await db.commit()
    return {"message": "Course deleted successfully"}

@router.get("/users", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.admin]))):
    result = await db.execute(select(User))
    return result.scalars().all()

@router.get("/courses", response_model=list[CourseResponse])
async def get_courses(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.admin, RoleEnum.student, RoleEnum.teacher]))):
    result = await db.execute(select(Course))
    courses = result.scalars().all()
    # attach teacher name
    for c in courses:
        if c.teacher_id:
            res_t = await db.execute(select(User).where(User.id == c.teacher_id))
            teacher = res_t.scalars().first()
            c.teacher_name = teacher.name if teacher else None
    return courses


