from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update
from models import User, Course, Enrollment, RoleEnum, Notification
from schemas import UserCreate, UserResponse, CourseCreate, CourseResponse, CourseUpdate, AnnouncementCreateRequest
from database import get_db
from security import require_role
from routers.auth import get_password_hash
from services.notification_service import queue_bulk_notifications, queue_notification

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
    await db.flush()

    if teacher_id:
        queue_notification(
            db,
            sender_id=current_user.id,
            recipient_id=teacher_id,
            notif_type="course_assignment",
            title="新课程分配 / New Course Assigned",
            content=(
                f"您被分配教授《{new_course.name}》，"
                f"时间：{new_course.class_time or '未设置'}，地点：{new_course.class_location or '未设置'}。"
            ),
            related_course_id=new_course.id,
        )

    await db.commit()
    await db.refresh(new_course)
    return new_course

@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(course_id: int, course: CourseUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.admin]))):
    res = await db.execute(select(Course).where(Course.id == course_id))
    target_course = res.scalars().first()
    if not target_course:
        raise HTTPException(status_code=404, detail="Course not found")

    old_name = target_course.name
    old_credits = target_course.credits
    old_capacity = target_course.capacity
    old_teacher_id = target_course.teacher_id
    old_time = target_course.class_time
    old_location = target_course.class_location

    update_data = course.model_dump(exclude_unset=True)

    new_teacher: User | None = None
    old_teacher: User | None = None
    if "teacher_id" in update_data and update_data["teacher_id"] is not None:
        res_t = await db.execute(select(User).where(User.id == update_data["teacher_id"], User.role == RoleEnum.teacher))
        new_teacher = res_t.scalars().first()
        if not new_teacher:
            raise HTTPException(status_code=400, detail="Invalid teacher")

    if old_teacher_id is not None:
        old_teacher_res = await db.execute(select(User).where(User.id == old_teacher_id, User.role == RoleEnum.teacher))
        old_teacher = old_teacher_res.scalars().first()

    for key, value in update_data.items():
        setattr(target_course, key, value)

    change_details: list[str] = []
    if "name" in update_data and old_name != target_course.name:
        change_details.append(f"课程名称：{old_name} -> {target_course.name}")
    if "credits" in update_data and old_credits != target_course.credits:
        change_details.append(f"学分：{old_credits} -> {target_course.credits}")
    if "capacity" in update_data and old_capacity != target_course.capacity:
        change_details.append(f"容量：{old_capacity} -> {target_course.capacity}")
    if "class_time" in update_data and old_time != target_course.class_time:
        change_details.append(f"上课时间：{old_time or '未设置'} -> {target_course.class_time or '未设置'}")
    if "class_location" in update_data and old_location != target_course.class_location:
        change_details.append(f"上课地点：{old_location or '未设置'} -> {target_course.class_location or '未设置'}")

    teacher_changed = "teacher_id" in update_data and old_teacher_id != target_course.teacher_id
    if teacher_changed:
        old_teacher_name = old_teacher.name if old_teacher else "未分配"
        if target_course.teacher_id is None:
            new_teacher_name = "未分配"
        else:
            new_teacher_name = new_teacher.name if new_teacher else f"教师#{target_course.teacher_id}"
        change_details.append(f"授课教师：{old_teacher_name} -> {new_teacher_name}")

    if change_details:
        res_students = await db.execute(select(Enrollment.student_id).where(Enrollment.course_id == target_course.id))
        student_ids = [row[0] for row in res_students.all()]
        queue_bulk_notifications(
            db,
            sender_id=current_user.id,
            recipient_ids=student_ids,
            notif_type="course_update",
            title="课程信息更新 / Course Updated",
            content=f"您选修的《{target_course.name}》信息已更新：" + "；".join(change_details),
            related_course_id=target_course.id,
        )

    if teacher_changed:
        if old_teacher_id is not None:
            if target_course.teacher_id is None:
                old_teacher_content = f"《{target_course.name}》已取消您的授课分配。"
            else:
                old_teacher_content = (
                    f"《{target_course.name}》已不再由您授课，"
                    f"现任教师为 {new_teacher.name if new_teacher else f'教师#{target_course.teacher_id}'}。"
                )
            queue_notification(
                db,
                sender_id=current_user.id,
                recipient_id=old_teacher_id,
                notif_type="course_assignment",
                title="课程分配变更 / Assignment Changed",
                content=old_teacher_content,
                related_course_id=target_course.id,
            )

        if target_course.teacher_id is not None:
            queue_notification(
                db,
                sender_id=current_user.id,
                recipient_id=target_course.teacher_id,
                notif_type="course_assignment",
                title="课程分配变更 / Assignment Changed",
                content=(
                    f"您被分配教授《{target_course.name}》，"
                    f"时间：{target_course.class_time or '未设置'}，"
                    f"地点：{target_course.class_location or '未设置'}。"
                ),
                related_course_id=target_course.id,
            )

    elif change_details and target_course.teacher_id is not None:
        queue_notification(
            db,
            sender_id=current_user.id,
            recipient_id=target_course.teacher_id,
            notif_type="course_update",
            title="课程信息更新 / Course Updated",
            content=f"您教授的《{target_course.name}》信息已更新：" + "；".join(change_details),
            related_course_id=target_course.id,
        )

    await db.commit()
    await db.refresh(target_course)
    return target_course

@router.delete("/courses/{course_id}")
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.admin]))):
    res = await db.execute(select(Course).where(Course.id == course_id))
    course = res.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    res_students = await db.execute(select(Enrollment.student_id).where(Enrollment.course_id == course_id))
    student_ids = [row[0] for row in res_students.all()]
    queue_bulk_notifications(
        db,
        sender_id=current_user.id,
        recipient_ids=student_ids,
        notif_type="course_cancelled",
        title="课程停开通知 / Course Cancelled",
        content=f"课程《{course.name}》已被教务删除/停开，请留意选课安排调整。",
        related_course_id=None,
    )

    if course.teacher_id is not None:
        queue_notification(
            db,
            sender_id=current_user.id,
            recipient_id=course.teacher_id,
            notif_type="course_cancelled",
            title="课程停开通知 / Course Cancelled",
            content=f"您负责的课程《{course.name}》已被删除/停开。",
            related_course_id=None,
        )

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
    # attach teacher name and enrollment summary for UI display
    for c in courses:
        if c.teacher_id:
            res_t = await db.execute(select(User).where(User.id == c.teacher_id))
            teacher = res_t.scalars().first()
            c.teacher_name = teacher.name if teacher else None
        res_e = await db.execute(select(Enrollment).where(Enrollment.course_id == c.id))
        enrolled_count = len(res_e.scalars().all())
        c.enrolled_count = enrolled_count
        c.remaining_capacity = max(c.capacity - enrolled_count, 0)
    return courses


@router.post("/announcements")
async def send_announcement(
    payload: AnnouncementCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.admin])),
):
    # Create one notification row per user so "read/unread" works for everyone.
    users_res = await db.execute(select(User))
    users = users_res.scalars().all()

    new_notifications: list[Notification] = []
    for u in users:
        new_notifications.append(
            Notification(
                sender_id=current_user.id,
                recipient_id=u.id,
                notif_type="announcement",
                title=payload.title,
                content=payload.content,
                is_read=False,
            )
        )

    db.add_all(new_notifications)
    await db.commit()
    return {"message": "Announcement sent"}

