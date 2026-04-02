from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import auth, admin, teacher, student, profile, notifications
import uvicorn
import os
from settings import APP_HOST, APP_PORT, APP_RELOAD

app = FastAPI(title="Teaching Management System")

# Ensure static folder exists
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(teacher.router, prefix="/api/teacher", tags=["Teacher"])
app.include_router(student.router, prefix="/api/student", tags=["Student"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])

@app.get("/")
async def root():
    if not os.path.exists("static/index.html"):
        return {"message": "index.html not found"}
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run("app:app", host=APP_HOST, port=APP_PORT, reload=APP_RELOAD)
