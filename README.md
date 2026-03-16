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
