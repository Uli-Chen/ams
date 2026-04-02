from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from database import get_db
from security import get_current_user, require_role
from models import User, RoleEnum, Notification, Course, Enrollment
from schemas import NotificationResponse, DirectMessageRequest
from services.notification_service import queue_notification

router = APIRouter()


@router.get("/my", response_model=list[NotificationResponse])
async def my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification, User)
        .join(User, Notification.sender_id == User.id, isouter=True)
        .where(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )

    items: list[NotificationResponse] = []
    for notif, sender in result.all():
        items.append(
            NotificationResponse(
                id=notif.id,
                sender_name=sender.name if sender else None,
                notif_type=notif.notif_type,
                title=notif.title,
                content=notif.content,
                related_course_id=notif.related_course_id,
                related_enrollment_id=notif.related_enrollment_id,
                is_read=notif.is_read,
                created_at=notif.created_at,
            )
        )
    return items


@router.put("/read-all")
async def read_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(Notification).where(
            Notification.recipient_id == current_user.id,
            Notification.is_read == False,  # noqa: E712
        ).values(is_read=True)
    )
    await db.commit()
    return {"message": "All notifications marked as read"}


@router.put("/{notification_id}/read")
async def read_one(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == current_user.id,
        )
    )
    notif = res.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    await db.commit()
    return {"message": "Notification marked as read"}


@router.post("/direct")
async def send_direct(
    payload: DirectMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    receiver_id = payload.receiver_id
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    if receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    receiver_res = await db.execute(select(User).where(User.id == receiver_id))
    receiver = receiver_res.scalars().first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    related_course_id = payload.related_course_id

    # Validate relationship based on sender/receiver roles
    if current_user.role == RoleEnum.teacher:
        if receiver.role != RoleEnum.student:
            raise HTTPException(status_code=400, detail="Teacher can only message students")

        if related_course_id is not None:
            # Must be a course taught by the teacher
            course_res = await db.execute(select(Course).where(Course.id == related_course_id, Course.teacher_id == current_user.id))
            course = course_res.scalars().first()
            if not course:
                raise HTTPException(status_code=400, detail="Invalid course for this teacher")

            enrollment_res = await db.execute(
                select(Enrollment).where(Enrollment.course_id == related_course_id, Enrollment.student_id == receiver_id)
            )
            if not enrollment_res.scalars().first():
                raise HTTPException(status_code=400, detail="Student is not enrolled in this course")
        else:
            enrollment_res = await db.execute(
                select(Enrollment)
                .join(Course, Enrollment.course_id == Course.id)
                .where(Enrollment.student_id == receiver_id, Course.teacher_id == current_user.id)
            )
            if not enrollment_res.scalars().first():
                raise HTTPException(status_code=400, detail="Student does not belong to your courses")

        notif_type = "direct"
    elif current_user.role == RoleEnum.student:
        if receiver.role != RoleEnum.teacher:
            raise HTTPException(status_code=400, detail="Student can only message teachers")

        if related_course_id is not None:
            course_res = await db.execute(
                select(Course).where(Course.id == related_course_id, Course.teacher_id == receiver_id)
            )
            course = course_res.scalars().first()
            if not course:
                raise HTTPException(status_code=400, detail="Invalid course for the receiver")

            enrollment_res = await db.execute(
                select(Enrollment).where(
                    Enrollment.course_id == related_course_id,
                    Enrollment.student_id == current_user.id,
                )
            )
            if not enrollment_res.scalars().first():
                raise HTTPException(status_code=400, detail="You are not enrolled in this course")
        else:
            enrollment_res = await db.execute(
                select(Enrollment)
                .join(Course, Enrollment.course_id == Course.id)
                .where(Enrollment.student_id == current_user.id, Course.teacher_id == receiver_id)
            )
            if not enrollment_res.scalars().first():
                raise HTTPException(status_code=400, detail="You are not enrolled in any course taught by this teacher")

        notif_type = "direct"
    else:
        raise HTTPException(status_code=403, detail="Only teacher/student can send direct messages")

    queue_notification(
        db,
        sender_id=current_user.id,
        recipient_id=receiver_id,
        notif_type=notif_type,
        title=f"来自 {current_user.name}",
        content=content,
        related_course_id=related_course_id,
    )
    await db.commit()
    return {"message": "Message sent"}

