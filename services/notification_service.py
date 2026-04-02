from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from models import Notification


def queue_notification(
    db: AsyncSession,
    *,
    sender_id: int | None,
    recipient_id: int | None,
    notif_type: str,
    title: str | None,
    content: str,
    related_course_id: int | None = None,
    related_enrollment_id: int | None = None,
) -> None:
    if recipient_id is None:
        return
    db.add(
        Notification(
            sender_id=sender_id,
            recipient_id=recipient_id,
            notif_type=notif_type,
            title=title,
            content=content,
            related_course_id=related_course_id,
            related_enrollment_id=related_enrollment_id,
            is_read=False,
        )
    )


def queue_bulk_notifications(
    db: AsyncSession,
    *,
    sender_id: int | None,
    recipient_ids: Iterable[int | None],
    notif_type: str,
    title: str | None,
    content: str,
    related_course_id: int | None = None,
    related_enrollment_id: int | None = None,
    exclude_recipient_ids: Iterable[int | None] | None = None,
) -> None:
    excluded = {rid for rid in (exclude_recipient_ids or []) if rid is not None}
    seen: set[int] = set()
    for recipient_id in recipient_ids:
        if recipient_id is None or recipient_id in excluded or recipient_id in seen:
            continue
        seen.add(recipient_id)
        queue_notification(
            db,
            sender_id=sender_id,
            recipient_id=recipient_id,
            notif_type=notif_type,
            title=title,
            content=content,
            related_course_id=related_course_id,
            related_enrollment_id=related_enrollment_id,
        )
