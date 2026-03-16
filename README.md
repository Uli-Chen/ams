Welcome to the Academic Management System
A modern, lightweight platform designed to streamline administration and enhance the academic experience for both students and teachers.

<img width="2560" height="1270" alt="image" src="https://github.com/user-attachments/assets/f393da59-4e21-4439-860f-9c2a409a4b55" />

# To Run and Debug Locally
1. Setup the Environment
``` cmd
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
```

2. Initialize DB and Seed Data:
``` cmd
python init_db.py
python seed.py
```
> Note that:
> (This will create your MySQL database "teaching_system" and populate it with sample users: admin, teacher1, teacher2, student1, student2. All log-in passwords are <username>123, e.g., admin123 or student123)

3. Start the Application
``` cmd
uvicorn app:app --reload
```

4. Test the UI: Open http://localhost:8000 in your web browser. 

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | HTML / CSS / JS | Native web technologies featuring a modern **Glassmorphism** UI. |
| **Backend** | Python & FastAPI | High-performance API framework handling core business logic. |
| **Database** | MySQL | Relational database for storing user, course, and academic data. |
| **Server** | Uvicorn | Lightning-fast ASGI server for running the backend application. |
