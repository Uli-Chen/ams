import asyncio
import random

from database import Base, SessionLocal, engine
from models import Course, Enrollment, RoleEnum, User
from routers.auth import get_password_hash

TOTAL_STUDENTS = 100
RANDOM_SEED = 20260402


async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


def build_students(total_students: int, student_password_hash: str) -> list[User]:
    students = [
        User(
            username="student1",
            hashed_password=student_password_hash,
            role=RoleEnum.student,
            name="Alice",
        ),
        User(
            username="student2",
            hashed_password=student_password_hash,
            role=RoleEnum.student,
            name="Bob",
        ),
    ]

    auto_count = max(total_students - len(students), 0)
    for i in range(3, 3 + auto_count):
        students.append(
            User(
                username=f"student{i}",
                hashed_password=student_password_hash,
                role=RoleEnum.student,
                name=f"Student {i}",
            )
        )

    return students


async def seed_data():
    await init_tables()
    rng = random.Random(RANDOM_SEED)

    async with SessionLocal() as session:
        admin_password_hash = get_password_hash("admin123")
        teacher_password_hash = get_password_hash("teacher123")
        student_password_hash = get_password_hash("student123")

        admin = User(
            username="admin",
            hashed_password=admin_password_hash,
            role=RoleEnum.admin,
            name="System Admin",
        )

        teachers = [
            User(
                username="teacher1",
                hashed_password=teacher_password_hash,
                role=RoleEnum.teacher,
                name="Dr. Smith",
            ),
            User(
                username="teacher2",
                hashed_password=teacher_password_hash,
                role=RoleEnum.teacher,
                name="Prof. Johnson",
            ),
            User(
                username="teacher3",
                hashed_password=teacher_password_hash,
                role=RoleEnum.teacher,
                name="Dr. Williams",
            ),
        ]

        students = build_students(TOTAL_STUDENTS, student_password_hash)
        session.add_all([admin, *teachers, *students])
        await session.flush()

        courses = [
            Course(
                name="Database Systems",
                teacher_id=teachers[0].id,
                credits=3,
                capacity=120,
                class_time="Mon 10:00-12:00",
                class_location="Room 201",
            ),
            Course(
                name="Web Development",
                teacher_id=teachers[1].id,
                credits=4,
                capacity=120,
                class_time="Tue 14:00-16:00",
                class_location="Lab 3",
            ),
            Course(
                name="Data Structures",
                teacher_id=teachers[2].id,
                credits=3,
                capacity=120,
                class_time="Wed 08:30-10:30",
                class_location="Room 305",
            ),
            Course(
                name="Operating Systems",
                teacher_id=teachers[0].id,
                credits=4,
                capacity=120,
                class_time="Thu 15:00-17:00",
                class_location="Room 402",
            ),
            Course(
                name="Computer Networks",
                teacher_id=teachers[1].id,
                credits=3,
                capacity=120,
                class_time="Fri 09:00-11:00",
                class_location="Room 108",
            ),
        ]
        session.add_all(courses)
        await session.flush()

        enrollments: list[Enrollment] = []
        for student in students:
            selected_count = rng.randint(2, 4)
            selected_courses = rng.sample(courses, k=selected_count)
            for course in selected_courses:
                grade = round(rng.uniform(55.0, 99.5), 1)
                enrollments.append(
                    Enrollment(
                        student_id=student.id,
                        course_id=course.id,
                        grade=grade,
                    )
                )

        session.add_all(enrollments)
        await session.commit()

        print("Database seeded successfully.")
        print(f"Admin users: 1")
        print(f"Teacher users: {len(teachers)}")
        print(f"Student users: {len(students)}")
        print(f"Courses: {len(courses)}")
        print(f"Enrollments: {len(enrollments)}")


if __name__ == "__main__":
    asyncio.run(seed_data())
