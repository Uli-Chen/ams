# Academic Management System

一个基于 FastAPI + MySQL + 原生 HTML/CSS/JS 实现的简易教学管理系统，面向课程实验中的 SQL 语言应用设计题目。

系统包含三类角色：
- 学生
- 教师
- 管理员

在不改动既有美术风格的前提下，项目补充并完善了课程冲突检测、真实余量显示、个人资料维护、通知消息、系统公告等功能。

![System Preview](https://github.com/user-attachments/assets/f393da59-4e21-4439-860f-9c2a409a4b55)

## Experiment Requirement Mapping

本项目对应实验要求中的四项内容：

1. 学生可以管理自己的信息、选课
2. 教师可以管理自己的信息、自己所教课程、成绩管理
3. 管理员对课程信息进行管理
4. 根据教学管理系统需要，自行设计相应功能

当前实现情况：
- 学生：查看和修改个人信息、上传头像、修改密码、选课、退课、查看成绩、导出课表和成绩
- 教师：查看自己课程、查看选课学生、录入成绩、调整自己课程时间和地点、向学生发送消息
- 管理员：用户管理、课程增删改查、课程分配教师、发布系统公告
- 自定义功能：通知中心、师生私信、课程冲突检测、课程剩余容量显示、CSV 导出

## Tech Stack

| Category | Technology | Description |
| :--- | :--- | :--- |
| Frontend | HTML / CSS / JavaScript | 原生前端实现，保留既有界面风格 |
| Backend | FastAPI | 提供认证、角色权限和业务接口 |
| ORM | SQLAlchemy Async | 负责异步数据库访问 |
| Database | MySQL | 存储用户、课程、选课、成绩、通知数据 |
| Server | Uvicorn | 运行 ASGI 服务 |

## Main Features

### Student
- 登录系统
- 查看个人资料
- 修改姓名、手机号、密码
- 上传头像
- 查看可选课程
- 选课与退课
- 查看已选课程、课表和成绩
- 导出课表 CSV
- 导出成绩 CSV
- 向任课教师发送消息

### Teacher
- 登录系统
- 查看个人资料
- 查看自己教授的课程
- 查看课程学生名单
- 录入与修改成绩
- 调整自己课程的上课时间和地点
- 接收学生选课通知
- 向已选课学生发送消息

### Admin
- 登录系统
- 新建用户
- 删除用户
- 新建课程
- 修改课程
- 删除课程
- 为课程分配教师
- 发布系统公告

### Extended Functions
- 通知中心
- 全体公告
- 师生私信
- 课程冲突检测
- 课程剩余容量显示
- 头像上传
- 成绩发布通知

## Course Conflict Detection

为体现教学管理系统的业务完整性，项目新增了课程时间冲突检测功能。

规则说明：
- 学生选课时，如果待选课程的 `class_time` 与学生已选课程中的某门课时间完全相同，系统将拒绝本次选课。

示例：
- 课程 A：`Mon 10:00-12:00`
- 课程 B：`Mon 10:00-12:00`
- 学生已选 A 后，再选 B，系统会提示课程时间冲突。

这一功能适合直接写入实验报告中的“自行设计功能”部分。

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

## Local Setup

### 1. Create virtual environment

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

### 2. Prepare MySQL

项目默认数据库配置位于 `database.py`：

```python
DATABASE_URL = "mysql+aiomysql://root:zhang.12@localhost:3306/teaching_system"
```

请确保本地 MySQL 已启动，并且存在对应账号密码。

### 3. Initialize database

```bash
python3 init_db.py
python3 seed.py
```

### 4. Start the application

```bash
uvicorn app:app --reload
```

默认访问地址：

```text
http://127.0.0.1:8000
```

## Default Test Accounts

执行 `seed.py` 后，系统会写入以下测试账号：

| Role | Username | Password |
| :--- | :--- | :--- |
| Admin | `admin` | `admin123` |
| Teacher | `teacher1` | `teacher123` |
| Teacher | `teacher2` | `teacher123` |
| Student | `student1` | `student123` |
| Student | `student2` | `student123` |

## Suggested Demo Flow

如果需要课堂演示或实验验收，可以按下面顺序测试：

1. 使用 `admin` 登录，查看用户管理和课程管理
2. 新建两门相同上课时间的课程
3. 使用 `student1` 登录，先选择第一门课程
4. 再选择第二门相同时间课程，验证系统拦截冲突选课
5. 使用 `teacher1` 登录，查看课程学生名单并录入成绩
6. 返回学生端，查看成绩变化和通知消息

## Notes

- 本项目使用异步 SQLAlchemy，因此依赖 `greenlet`
- 登录表单和头像上传依赖 `python-multipart`
- 仓库中已通过 `.gitignore` 排除本地虚拟环境、缓存和上传头像文件

## License

This project is intended for educational and experimental use.
