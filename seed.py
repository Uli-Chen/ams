import asyncio
from database import engine, SessionLocal, Base
from models import User, Course, Enrollment, RoleEnum
from routers.auth import get_password_hash

async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def seed_data():
    await init_tables()
    async with SessionLocal() as session:
        # Admin
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role=RoleEnum.admin,
            name="System Admin"
        )
        
        # Teachers
        teacher1 = User(
            username="teacher1",
            hashed_password=get_password_hash("teacher123"),
            role=RoleEnum.teacher,
            name="Dr. Smith"
        )
        teacher2 = User(
            username="teacher2",
            hashed_password=get_password_hash("teacher123"),
            role=RoleEnum.teacher,
            name="Prof. Johnson"
        )

        # Students
        student1 = User(
            username="student1",
            hashed_password=get_password_hash("student123"),
            role=RoleEnum.student,
            name="Alice"
        )
        student2 = User(
            username="student2",
            hashed_password=get_password_hash("student123"),
            role=RoleEnum.student,
            name="Bob"
        )
        
        session.add_all([admin, teacher1, teacher2, student1, student2])
        await session.commit()

        # Due to autoincrement, we need to refresh to get IDs or just add courses
        # Since we added them, their IDs might not be immediately available until commit/flush
        
        # Courses
        course1 = Course(
            name="Database Systems",
            teacher_id=teacher1.id,
            credits=3,
            capacity=30,
            class_time="Mon 10:00-12:00",
            class_location="Room 201",
        )
        course2 = Course(
            name="Web Development",
            teacher_id=teacher2.id,
            credits=4,
            capacity=40,
            class_time="Wed 14:00-16:00",
            class_location="Lab 3",
        )
        
        session.add_all([course1, course2])
        await session.commit()

        print("Database seeded successfully with test data.")

if __name__ == "__main__":
    asyncio.run(seed_data())
