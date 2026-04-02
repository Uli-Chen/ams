# 教务管理系统（AMS）项目报告（中文）

本系统是一个基于 FastAPI + MySQL + SQLAlchemy Async + 原生前端的角色化教务管理平台，覆盖管理员、教师、学生三类核心角色，并在近期完成了“操作驱动通知”的系统升级，使业务闭环更完整、信息同步更及时。

## 1. 项目重点与亮点（含代码定位）

### 1.1 配置解耦与环境管理（避免硬编码）
- 统一从 `.env` 读取数据库、JWT、服务启动参数，并提供默认值与类型转换。  
  代码定位：`settings.py` 第 **7-38** 行
- 数据库引擎直接消费配置层的 `DATABASE_URL`，业务代码不再写死账号密码。  
  代码定位：`database.py` 第 **1-17** 行
- 初始化数据库脚本同样接入配置，保持部署一致性。  
  代码定位：`init_db.py` 第 **1-22** 行
- 应用启动参数（host/port/reload）由配置驱动。  
  代码定位：`app.py` 第 **7-32** 行

### 1.2 认证与权限控制（安全基线）
- 登录时完成密码校验与 JWT 签发，Token 携带用户身份与角色。  
  代码定位：`routers/auth.py` 第 **21-51** 行
- 使用统一依赖完成 Token 解析与角色守卫，避免接口越权访问。  
  代码定位：`security.py` 第 **13-40** 行

### 1.3 领域模型清晰（用户-课程-选课-通知）
- 核心实体 `User / Course / Enrollment / Notification` 关系明确，支持后续扩展。  
  代码定位：`models.py` 第 **7-78** 行

### 1.4 选课业务具备约束能力（可用性与正确性）
- 学生选课时执行重复选课检查、时间冲突检查、容量检查。  
  代码定位：`routers/student.py` 第 **11-42** 行
- 学生可查看“我的课程”，聚合教师、时间、地点、成绩信息。  
  代码定位：`routers/student.py` 第 **88-115** 行

### 1.5 通知系统从“手动消息”升级为“业务事件驱动”
- 新增统一通知服务，支持单发/群发与接收人去重。  
  代码定位：`services/notification_service.py` 第 **8-62** 行
- 教师修改课程时间/地点后，自动通知该课程全部学生。  
  代码定位：`routers/teacher.py` 第 **26-73** 行
- 教师发布成绩与后续改分都会自动通知学生（不仅首次发布）。  
  代码定位：`routers/teacher.py` 第 **108-145** 行
- 学生选课/退选会自动通知任课教师。  
  代码定位：`routers/student.py` 第 **46-56** 行、**61-86** 行
- 管理员创建课程并分配教师时，自动通知对应教师。  
  代码定位：`routers/admin.py` 第 **51-80** 行
- 管理员更新课程（时间/地点/容量/教师等）时，自动通知已选学生及相关教师。  
  代码定位：`routers/admin.py` 第 **82-194** 行
- 管理员删除课程前，自动通知受影响学生与教师。  
  代码定位：`routers/admin.py` 第 **196-229** 行
- 管理员公告按“每个接收人一条通知”落库，支持读/未读追踪。  
  代码定位：`routers/admin.py` 第 **253-278** 行
- 通知中心支持查询、单条已读、全部已读；私信发送含教师/学生关系校验。  
  代码定位：`routers/notifications.py` 第 **15-78** 行、**81-172** 行

### 1.6 个人资料与文件上传控制
- 支持个人资料更新、密码修改，并做旧密码校验。  
  代码定位：`routers/profile.py` 第 **24-49** 行
- 头像上传包含类型白名单、体积上限、落盘路径规范。  
  代码定位：`routers/profile.py` 第 **52-77** 行

### 1.7 前端体验增强（容错与可用性）
- 图表渲染加入容错机制：`Chart.js` 或 Canvas 不可用时不阻断主流程。  
  代码定位：`static/app.js` 第 **29-42** 行
- 通知类型增加中文映射，提升消息可读性。  
  代码定位：`static/app.js` 第 **691-706** 行
- 学生端支持课表与成绩 CSV 导出。  
  代码定位：`static/app.js` 第 **868-908** 行

### 1.8 可复现测试数据与压测友好
- 一键生成约 100 名学生、5 门课程、随机选课和成绩，便于演示与联调。  
  代码定位：`seed.py` 第 **8-160** 行

---

## 2. 系统架构概览

- 后端：FastAPI（路由分层：`auth/admin/teacher/student/profile/notifications`）
- 数据层：SQLAlchemy Async + MySQL
- 前端：单页结构（`static/index.html` + `static/app.js` + `static/style.css`）
- 鉴权：JWT + 角色依赖守卫
- 通知：事件触发 + 通知中心读/未读机制

---

## 3. 快速运行（本地）

### 3.1 安装依赖

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 配置环境变量

复制配置模板：

```bat
copy .env.example .env
```

建议至少配置以下项：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=teaching_system
JWT_SECRET_KEY=change-me-in-production
APP_HOST=0.0.0.0
APP_PORT=8000
APP_RELOAD=true
```

### 3.3 初始化与启动

```bash
python init_db.py
python seed.py
python app.py
```

访问地址：

```text
http://127.0.0.1:<APP_PORT>
```

---

## 4. 项目价值总结

本系统的核心价值不只在“有功能”，而在于：
- 业务链路完整：从选课、授课、评分到通知闭环。
- 工程质量提升：配置集中、权限统一、通知服务抽象。
- 可演示可扩展：支持批量测试数据，便于后续继续迭代（如通知偏好、消息聚合、审计日志）。

