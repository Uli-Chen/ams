# Academic Management System

Academic Management System is a role-based web application built with FastAPI, MySQL, SQLAlchemy, and vanilla HTML/CSS/JavaScript. It supports academic administration workflows for students, teachers, and administrators in a lightweight single-page interface.

![System Preview](https://github.com/user-attachments/assets/f393da59-4e21-4439-860f-9c2a409a4b55)

## Features

### Students
- Sign in and manage personal profile
- Update name, phone number, password, and avatar
- Browse available courses
- Enroll in and drop courses
- View enrolled courses, timetable, and grades
- Export timetable and grades as CSV
- Send messages to course teachers

### Teachers
- View assigned courses
- View enrolled students for each course
- Publish and update grades
- Adjust class time and class location for owned courses
- Receive enrollment notifications
- Send messages to enrolled students

### Administrators
- Create and delete users
- Create, update, assign, and delete courses
- Manage course capacity and schedule information
- Publish system-wide announcements

### Additional Capabilities
- Notification center
- Direct messaging between students and teachers
- Course time conflict detection during enrollment
- Remaining seat display for courses
- Grade publishing notifications
- CSV export for student records

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| Backend | FastAPI |
| ORM | SQLAlchemy Async |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript |
| Server | Uvicorn |

## Project Structure

```text
.
├── app.py
├── database.py
├── init_db.py
├── models.py
├── requirements.txt
├── routers/
│   ├── admin.py
│   ├── auth.py
│   ├── notifications.py
│   ├── profile.py
│   ├── student.py
│   └── teacher.py
├── schemas.py
├── security.py
├── seed.py
└── static/
    ├── app.js
    ├── index.html
    └── style.css
```

## Getting Started

### 1. Create a virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bat
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. Configure MySQL

The default database connection is defined in [`database.py`](/Users/Zhuanz/Desktop/ams-main%202/database.py):

```python
DATABASE_URL = "mysql+aiomysql://root:zhang.12@localhost:3306/teaching_system"
```

Make sure a local MySQL server is running and the configured user has access to create and use the `teaching_system` database.

### 3. Initialize the database

```bash
python3 init_db.py
python3 seed.py
```

### 4. Run the application

```bash
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Default Accounts

After running `seed.py`, the following demo accounts are available:

| Role | Username | Password |
| :--- | :--- | :--- |
| Admin | `admin` | `admin123` |
| Teacher | `teacher1` | `teacher123` |
| Teacher | `teacher2` | `teacher123` |
| Student | `student1` | `student123` |
| Student | `student2` | `student123` |

## Enrollment Conflict Detection

The system prevents students from enrolling in two courses with the same `class_time` value. If a student has already enrolled in a course and attempts to enroll in another course with an identical schedule string, the request is rejected.

Example:
- Course A: `Mon 10:00-12:00`
- Course B: `Mon 10:00-12:00`

If the student is already enrolled in Course A, enrolling in Course B will fail with a time conflict message.

## Notes

- The project uses async SQLAlchemy and requires `greenlet`
- Form-based login and avatar upload require `python-multipart`
- Local environment files, caches, and uploaded avatars are excluded through `.gitignore`

## License

This project is intended for educational and demonstration purposes.
