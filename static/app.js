const API_BASE = '/api';

// State
let state = {
    token: localStorage.getItem('token') || null,
    role: null,
    userId: null,
    username: null,
    avatarUrl: null,
    phoneNumber: null
};

// Charts refs
let adminChartInst = null;
let teacherChartInst = null;
let studentChartInst = null;
let chartWarningShown = false;

// Cache for student exports / timetable
let myCoursesData = [];

// Elements
const viewLogin = document.getElementById('login-view');
const viewDashboard = document.getElementById('dashboard-layout');
const loginForm = document.getElementById('login-form');
const toastEl = document.getElementById('toast');
const toastMsg = document.getElementById('toast-msg');

function getChartContext(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof canvas.getContext !== 'function') {
        return null;
    }
    return canvas.getContext('2d');
}

function notifyChartUnavailable(detail) {
    console.warn(detail);
    if (chartWarningShown) return;
    chartWarningShown = true;
    showToast('Chart.js 未加载或图表节点缺失，已跳过图表渲染。', true);
}

function updateDateDisplay() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('date-display').textContent = new Date().toLocaleDateString('zh-CN', options);
}

function init() {
    updateDateDisplay();
    if (state.token) {
        parseToken();
        showDashboard();
    } else {
        showLogin();
    }
}

function parseToken() {
    try {
        const payload = JSON.parse(atob(state.token.split('.')[1]));
        state.role = payload.role;
        state.userId = payload.id;
        state.username = payload.sub;
    } catch(e) { logout(); }
}

function showToast(msg, isError = false) {
    toastMsg.textContent = msg;
    if (isError) toastEl.classList.add('error');
    else toastEl.classList.remove('error');
    toastEl.classList.add('show');
    setTimeout(() => toastEl.classList.remove('show'), 3000);
}

async function apiCall(endpoint, options = {}) {
    const headers = { ...options.headers };
    if (state.token) headers['Authorization'] = `Bearer ${state.token}`;
    if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }
    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'API request failed');
    return data;
}

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('username', document.getElementById('username').value);
    formData.append('password', document.getElementById('password').value);
    const btn = loginForm.querySelector('button');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 登录中...';
    btn.disabled = true;
    try {
        const data = await apiCall('/auth/login', { method: 'POST', body: formData });
        state.token = data.access_token;
        localStorage.setItem('token', state.token);
        parseToken();
        showDashboard();
    } catch(err) {
        document.getElementById('login-error').textContent = err.message;
    } finally {
        btn.innerHTML = '进入系统';
        btn.disabled = false;
    }
});

document.getElementById('logout-btn').addEventListener('click', logout);

function logout() {
    state.token = null;
    state.role = null;
    localStorage.removeItem('token');
    showLogin();
}

function showLogin() {
    viewDashboard.classList.remove('active');
    viewDashboard.classList.add('hidden');
    viewLogin.classList.remove('hidden');
    viewLogin.classList.add('active');
    document.getElementById('login-error').textContent = '';
}

async function showDashboard() {
    viewLogin.classList.remove('active');
    viewLogin.classList.add('hidden');
    viewDashboard.classList.remove('hidden');
    viewDashboard.classList.add('active');
    
    document.getElementById('nav-user-name').textContent = state.username;
    document.getElementById('nav-user-role').textContent = state.role === 'admin' ? '系统管理员' : (state.role === 'teacher' ? '教师' : '学生');
    
    document.querySelectorAll('.role-dashboard').forEach(d => {
        d.classList.remove('active');
        d.classList.add('hidden');
    });
    
    const activeDash = document.getElementById(`${state.role}-dashboard`);
    activeDash.classList.remove('hidden');
    activeDash.classList.add('active');
    
    if (state.role === 'admin') loadAdminData();
    if (state.role === 'teacher') loadTeacherData();
    if (state.role === 'student') loadStudentData();

    // Common modules
    loadMeAndFillUI();
    loadNotifications();
}

// ==== Admin ====
let adminUsersData = [];

window.renderAdminUsers = () => {
    const filter = document.getElementById('user-role-filter').value;
    const filteredUsers = filter === 'all' ? adminUsersData : adminUsersData.filter(u => u.role === filter);
    
    const userTbody = document.querySelector('#admin-users-table tbody');
    if (filteredUsers.length === 0) {
        userTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">暂无记录 / No records found</td></tr>`;
        return;
    }
    userTbody.innerHTML = filteredUsers.map(u => `
        <tr>
            <td>#${u.id}</td>
            <td><strong>${u.username}</strong></td>
            <td>${u.name}</td>
            <td><span class="badge ${u.role}">${u.role}</span></td>
            <td>
                ${u.role !== 'admin' || adminUsersData.filter(a => a.role === 'admin').length > 1 
                    ? `<button class="btn danger-btn sm-btn" onclick="deleteUser(${u.id}, '${u.username}')"><i class="fa-solid fa-trash"></i> 删除</button>`
                    : '<span class="text-muted">不可删除</span>'
                }
            </td>
        </tr>
    `).join('');
};

async function loadAdminData() {
    try {
        const [courses, users] = await Promise.all([
            apiCall('/admin/courses'),
            apiCall('/admin/users')
        ]);
        
        document.getElementById('admin-total-courses').textContent = courses.length;
        document.getElementById('admin-total-users').textContent = users.length;
        adminUsersData = users;
        
        // Populate User Table
        renderAdminUsers();
        
        const teachers = users.filter(u => u.role === 'teacher');
        const teacherSelect = document.getElementById('new-course-teacher');
        teacherSelect.innerHTML = '<option value="">暂不分配 (None)</option>' + teachers.map(t => `<option value="${t.id}">${t.name} (@${t.username})</option>`).join('');
        
        const tbody = document.querySelector('#admin-courses-table tbody');
        tbody.innerHTML = courses.map(c => `
            <tr>
                <td>#${c.id}</td>
                <td><strong>${c.name}</strong></td>
                <td>${c.credits}</td>
                <td>${c.capacity}</td>
                <td>${c.class_time || '-'}</td>
                <td>${c.class_location || '-'}</td>
                <td>${c.teacher_name ? `<span class="badge" style="color:var(--primary)"><i class="fa-solid fa-chalkboard-user"></i> ${c.teacher_name}</span>` : `<span style="color:var(--text-muted)">未分配</span>`}</td>
                <td>
                    <button class="btn default-btn sm-btn" onclick="openEditCourseModal(${c.id}, '${c.name.replace(/'/g, "\\'")}', ${c.credits}, ${c.capacity}, ${c.teacher_id || 'null'}, '${(c.class_time || '').replace(/'/g, "\\'")}', '${(c.class_location || '').replace(/'/g, "\\'")}')"><i class="fa-solid fa-pen"></i></button>
                    <button class="btn danger-btn sm-btn" onclick="deleteCourse(${c.id}, '${c.name.replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash"></i></button>
                </td>
            </tr>
        `).join('');

        // Admin Visualization: User role distribution
        const roleCounts = { admin: 0, teacher: 0, student: 0 };
        users.forEach(u => { if(roleCounts[u.role] !== undefined) roleCounts[u.role]++; });
        
        if (typeof window.Chart === 'function') {
            const ctx = getChartContext('adminStatsChart');
            if (ctx) {
                if (adminChartInst) adminChartInst.destroy();
                adminChartInst = new window.Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['管理员 (Admin)', '教师 (Teacher)', '学生 (Student)'],
                        datasets: [{
                            data: [roleCounts.admin, roleCounts.teacher, roleCounts.student],
                            backgroundColor: ['#2c3e50', '#2b5797', '#e2e8f0'],
                            borderWidth: 0
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, cutout: '70%' }
                });
            } else {
                notifyChartUnavailable('adminStatsChart canvas not found.');
            }
        } else {
            notifyChartUnavailable('Chart.js is not loaded for admin chart.');
        }
    } catch(err) { showToast(err.message, true); }
}

document.getElementById('create-course-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const tId = document.getElementById('new-course-teacher').value;
        await apiCall('/admin/courses', {
            method: 'POST',
            body: {
                name: document.getElementById('new-course-name').value,
                credits: parseInt(document.getElementById('new-credits').value),
                capacity: parseInt(document.getElementById('new-capacity').value),
                teacher_id: tId ? parseInt(tId) : null,
                class_time: document.getElementById('new-course-time').value,
                class_location: document.getElementById('new-course-location').value,
            }
        });
        showToast('新课程添加成功 / Course Created');
        e.target.reset();
        loadAdminData();
    } catch(err) { showToast(err.message, true); }
});

document.getElementById('create-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        await apiCall('/admin/users', {
            method: 'POST',
            body: {
                username: document.getElementById('new-user-username').value,
                name: document.getElementById('new-user-name').value,
                role: document.getElementById('new-user-role').value,
                password: document.getElementById('new-user-password').value
            }
        });
        showToast('新用户添加成功 / User Created');
        e.target.reset();
        loadAdminData();
    } catch(err) { showToast(err.message, true); }
});

window.deleteUser = async (id, username) => {
    if(!confirm(`确定要删除用户 @${username} 吗？\n如果该用户是学生，其所有选课记录将被清除；如果是教师，其教授的课程将不再绑定该名教师。`)) return;
    try {
        await apiCall(`/admin/users/${id}`, { method: 'DELETE' });
        showToast('用户已删除 / User Deleted');
        loadAdminData();
    } catch (err) { showToast(err.message, true); }
};

window.openEditCourseModal = (id, name, credits, capacity, teacherId, classTime, classLocation) => {
    document.getElementById('edit-course-id').value = id;
    document.getElementById('edit-course-name-field').value = name;
    document.getElementById('edit-course-credits-field').value = credits;
    document.getElementById('edit-course-capacity-field').value = capacity;
    document.getElementById('edit-course-time-field').value = classTime || '';
    document.getElementById('edit-course-location-field').value = classLocation || '';
    
    // Copy options from "new-course-teacher" select
    const teacherSelect = document.getElementById('edit-course-teacher-field');
    teacherSelect.innerHTML = document.getElementById('new-course-teacher').innerHTML;
    teacherSelect.value = teacherId || '';
    
    document.getElementById('edit-course-modal').classList.remove('hidden');
};

document.getElementById('edit-course-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const id = document.getElementById('edit-course-id').value;
        const tId = document.getElementById('edit-course-teacher-field').value;
        await apiCall(`/admin/courses/${id}`, {
            method: 'PUT',
            body: {
                name: document.getElementById('edit-course-name-field').value,
                credits: parseInt(document.getElementById('edit-course-credits-field').value),
                capacity: parseInt(document.getElementById('edit-course-capacity-field').value),
                teacher_id: tId ? parseInt(tId) : null,
                class_time: document.getElementById('edit-course-time-field').value,
                class_location: document.getElementById('edit-course-location-field').value,
            }
        });
        showToast('课程修改成功 / Course Updated');
        document.getElementById('edit-course-modal').classList.add('hidden');
        loadAdminData();
    } catch(err) { showToast(err.message, true); }
});

window.deleteCourse = async (id, name) => {
    if(!confirm(`确定要删除课程 [${name}] 吗？\n此举将级联删除所有学生的选课与成绩记录！`)) return;
    try {
        await apiCall(`/admin/courses/${id}`, { method: 'DELETE' });
        showToast('课程已删除 / Course Deleted');
        loadAdminData();
    } catch (err) { showToast(err.message, true); }
};



// ==== Teacher ====
async function loadTeacherData() {
    try {
        const courses = await apiCall('/teacher/my-courses');
        document.getElementById('teacher-total-courses').textContent = courses.length;
        const grid = document.getElementById('teacher-courses-grid');
        
        if (courses.length === 0) {
            grid.innerHTML = '<p class="text-muted">暂无课程安排。 / No assigned courses yet.</p>';
            return;
        }

        grid.innerHTML = courses.map(c => `
            <div class="course-card">
                <h4><i class="fa-solid fa-book"></i> ${c.name}</h4>
                <p>学分: ${c.credits} | ${c.class_time || '-'} | ${c.class_location || '-'}</p>
                <div class="flex-between" style="gap:0.5rem; flex-wrap:wrap; margin-top:0.75rem;">
                    <button class="btn default-btn sm-btn" onclick="openTeacherEditCourseModal(${c.id}, '${c.name.replace(/'/g, "\\'")}', '${(c.class_time || '').replace(/'/g, "\\'")}', '${(c.class_location || '').replace(/'/g, "\\'")}')">
                        调整安排
                    </button>
                    <button class="btn primary-btn sm-btn" onclick="viewCourseDetails(${c.id}, '${c.name.replace(/'/g, "\\'")}')">
                        查看详情 <i class="fa-solid fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        `).join('');
    } catch(err) { showToast(err.message, true); }
}

window.openTeacherEditCourseModal = (courseId, courseName, classTime, classLocation) => {
    document.getElementById('teacher-edit-course-id').value = courseId;
    document.getElementById('teacher-edit-course-name').value = courseName;
    document.getElementById('teacher-edit-course-time').value = classTime || '';
    document.getElementById('teacher-edit-course-location').value = classLocation || '';
    document.getElementById('teacher-edit-course-modal').classList.remove('hidden');
};

document.getElementById('teacher-edit-course-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const id = document.getElementById('teacher-edit-course-id').value;
        await apiCall(`/teacher/courses/${id}`, {
            method: 'PUT',
            body: {
                class_time: document.getElementById('teacher-edit-course-time').value,
                class_location: document.getElementById('teacher-edit-course-location').value,
            }
        });
        document.getElementById('teacher-edit-course-modal').classList.add('hidden');
        showToast('课程安排已更新');
        await loadTeacherData();
    } catch (err) {
        showToast(err.message, true);
    }
});

window.viewCourseDetails = async (courseId, courseName) => {
    try {
        const data = await apiCall(`/teacher/courses/${courseId}/students`);
        const students = data.students || [];
        const course = data.course || {};

        document.getElementById('teacher-detail-title').textContent = courseName || course.course_name || '-';
        document.getElementById('teacher-detail-schedule').textContent =
            `${course.class_time || '-'} / ${course.class_location || '-'}`;
        document.getElementById('teacher-course-detail').classList.remove('hidden');
        
        const tbody = document.querySelector('#teacher-students-table tbody');
        if(students.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#7f8c8d;">暂无学生选修 / No students enrolled</td></tr>`;
        } else {
            tbody.innerHTML = students.map(s => `
                <tr>
                    <td>#${s.student_id}</td>
                    <td><strong>${s.student_name}</strong></td>
                    <td>
                        <input type="number" step="0.1" min="0" max="100" value="${s.grade !== null ? s.grade : ''}" id="grade-${s.enrollment_id}" 
                               style="width: 70px; padding: 0.3rem 0.5rem; border: 1px solid #e2e8f0; border-radius: 4px; font-family: Inter;">
                    </td>
                    <td>
                        <button class="btn default-btn sm-btn" onclick="updateGrade(${s.enrollment_id}, this)">保存</button>
                        <button class="btn primary-btn sm-btn" onclick="openMessageModal(${s.student_id}, '${(s.student_name || '').replace(/'/g, "\\'")}', ${courseId})" style="margin-left:0.5rem;">
                            发消息
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        // Draw Grade Chart
        const grades = { '优秀(A)':0, '良好(B)':0, '及格(C)':0, '不及格(F)':0, '未录入(Null)':0 };
        students.forEach(s => {
            if(s.grade === null) grades['未录入(Null)']++;
            else if(s.grade >= 90) grades['优秀(A)']++;
            else if(s.grade >= 75) grades['良好(B)']++;
            else if(s.grade >= 60) grades['及格(C)']++;
            else grades['不及格(F)']++;
        });

        if (typeof window.Chart === 'function') {
            const ctx = getChartContext('teacherGradeChart');
            if (ctx) {
                if (teacherChartInst) teacherChartInst.destroy();
                teacherChartInst = new window.Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(grades),
                        datasets: [{
                            label: '学生数量',
                            data: Object.values(grades),
                            backgroundColor: ['#27ae60', '#2b5797', '#f39c12', '#e74c3c', '#95a5a6']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
                        plugins: { legend: { display: false } }
                    }
                });
            } else {
                notifyChartUnavailable('teacherGradeChart canvas not found.');
            }
        } else {
            notifyChartUnavailable('Chart.js is not loaded for teacher chart.');
        }

    } catch(err) { showToast(err.message, true); }
};

document.getElementById('close-detail-btn').addEventListener('click', () => {
    document.getElementById('teacher-course-detail').classList.add('hidden');
});

window.updateGrade = async (enrollmentId, btn) => {
    const val = document.getElementById(`grade-${enrollmentId}`).value;
    if (val === '') return showToast('成绩不能为空 / Grade cannot be empty', true);
    const grade = parseFloat(val);
    if (grade < 0 || grade > 100) return showToast('成绩必须在 0 到 100 之间 / Grade must be 0-100', true);
    
    try {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        await apiCall(`/teacher/enrollments/${enrollmentId}/grade`, {
            method: 'PUT',
            body: { grade }
        });
        showToast('成绩已保存 / Grade saved');
        btn.innerHTML = '<i class="fa-solid fa-check" style="color:var(--success)"></i>';
        setTimeout(() => { btn.innerHTML = '保存'; }, 2000);
        // We could rerender chart here by fetching again, but kept simple
    } catch(err) { 
        showToast(err.message, true); 
        btn.innerHTML = '保存';
    }
};

// ==== Student ====
async function loadStudentData() {
    try {
        const [allCourses, myCourses] = await Promise.all([
            apiCall('/admin/courses'),
            apiCall('/student/my-courses')
        ]);
        
        const myCourseIds = new Set(myCourses.map(c => c.course_id));
        
        let earn = 0; let totalGradePoints = 0; let gradedCount = 0;
        const labels = []; const datagrades = [];

        const tbodyMy = document.querySelector('#student-my-courses-table tbody');
        if(myCourses.length === 0) {
            tbodyMy.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#7f8c8d;">你还未选修任何课程 / No enrollments yet.</td></tr>`;
        } else {
            tbodyMy.innerHTML = myCourses.map(c => {
                if (c.grade !== null) {
                    earn += c.credits;
                    totalGradePoints += c.grade;
                    gradedCount++;
                    labels.push(c.course_name.substring(0,6) + '..');
                    datagrades.push(c.grade);
                }
                return `
                <tr>
                    <td><strong>${c.course_name}</strong></td>
                    <td>${c.teacher_name || '-'}</td>
                    <td>${c.class_time || '-'}</td>
                    <td>${c.class_location || '-'}</td>
                    <td>${c.credits}</td>
                    <td>${c.grade !== null ? `<strong style="color:var(--primary)">${c.grade}</strong>` : '<span style="color:#bdc3c7">-</span>'}</td>
                    <td>
                        <button class="btn danger-btn sm-btn" onclick="unenrollCourse(${c.course_id})">退选 (Drop)</button>
                        ${c.teacher_id ? `<button class="btn default-btn sm-btn" style="margin-left:0.5rem;" onclick="openMessageModal(${c.teacher_id}, '${(c.teacher_name || '').replace(/'/g, "\\'")}', ${c.course_id})">消息老师</button>` : ''}
                    </td>
                </tr>`;
            }).join('');
        }
        
        document.getElementById('student-total-credits').textContent = earn;
        document.getElementById('student-gpa').textContent = gradedCount > 0 ? (totalGradePoints / gradedCount).toFixed(1) : '-';
        
        const tbodyAll = document.querySelector('#student-all-courses-table tbody');
        tbodyAll.innerHTML = allCourses.map(c => `
            <tr>
                <td><strong>${c.name}</strong></td>
                <td>${c.teacher_name || '-'}</td>
                <td>${c.class_time || '-'}</td>
                <td>${c.class_location || '-'}</td>
                <td>${c.credits}</td>
                <td>${c.remaining_capacity ?? c.capacity}</td>
                <td>
                    ${myCourseIds.has(c.id) 
                        ? '<span class="btn success-btn sm-btn" style="pointer-events:none;"><i class="fa-solid fa-check"></i> 已选修</span>'
                        : `<button class="btn default-btn sm-btn" onclick="enrollCourse(${c.id})"><i class="fa-solid fa-plus"></i> 选课 (Enroll)</button>`
                    }
                </td>
            </tr>
        `).join('');

        // Timetable
        myCoursesData = myCourses;
        const tbodyTT = document.querySelector('#student-timetable-table tbody');
        if(myCourses.length === 0) {
            tbodyTT.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#7f8c8d;">暂无课表数据</td></tr>`;
        } else {
            tbodyTT.innerHTML = myCourses.map(c => `
                <tr>
                    <td><strong>${c.course_name}</strong></td>
                    <td>${c.teacher_name || '-'}</td>
                    <td>${c.class_time || '-'}</td>
                    <td>${c.class_location || '-'}</td>
                    <td>${c.credits}</td>
                    <td>${c.grade !== null ? `<strong style="color:var(--primary)">${c.grade}</strong>` : '<span style="color:#bdc3c7">-</span>'}</td>
                </tr>
            `).join('');
        }

        // Student Visualization: Radar
        if (typeof window.Chart === 'function') {
            const ctx = getChartContext('studentRadarChart');
            if (ctx) {
                if (studentChartInst) studentChartInst.destroy();
                studentChartInst = new window.Chart(ctx, {
                    type: 'radar',
                    data: {
                        labels: labels.length > 0 ? labels : ['算法', '系统', '网络', '数据库', '数学'],
                        datasets: [{
                            label: '各科成绩',
                            data: datagrades.length > 0 ? datagrades : [0,0,0,0,0],
                            backgroundColor: 'rgba(43, 87, 151, 0.2)',
                            borderColor: '#2b5797',
                            pointBackgroundColor: '#2b5797',
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            r: { angleLines: { display: true }, suggestedMin: 0, suggestedMax: 100 }
                        }
                    }
                });
            } else {
                notifyChartUnavailable('studentRadarChart canvas not found.');
            }
        } else {
            notifyChartUnavailable('Chart.js is not loaded for student chart.');
        }

    } catch(err) { showToast(err.message, true); }
}

window.enrollCourse = async (courseId) => {
    try {
        await apiCall(`/student/courses/${courseId}/enroll`, { method: 'POST' });
        showToast('选课成功 / Enrolled successfully');
        loadStudentData();
    } catch(err) { showToast(err.message, true); }
};

window.unenrollCourse = async (courseId) => {
    if(!confirm('确定要退选这门课吗？ / Drop course?')) return;
    try {
        await apiCall(`/student/courses/${courseId}/unenroll`, { method: 'DELETE' });
        showToast('退选成功 / Dropped successfully');
        loadStudentData();
    } catch(err) { showToast(err.message, true); }
};

// ==== Common: Profile / Notifications / Messaging / Exports ====

function escapeHtml(str) {
    return String(str ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function formatDateTime(dt) {
    try {
        return new Date(dt).toLocaleString('zh-CN');
    } catch (_) {
        return dt;
    }
}

async function loadMeAndFillUI() {
    try {
        const me = await apiCall('/profile/me');
        state.avatarUrl = me.avatar_url || null;
        state.phoneNumber = me.phone_number || null;

        document.getElementById('nav-user-name').textContent = me.name || me.username;
        document.getElementById('profile-name').value = me.name || '';
        document.getElementById('profile-phone').value = me.phone_number || '';

        const navAvatarImg = document.getElementById('nav-avatar-img');
        const navAvatarIcon = document.getElementById('nav-avatar-icon');
        const preview = document.getElementById('profile-avatar-preview');
        if (me.avatar_url) {
            navAvatarImg.src = me.avatar_url;
            navAvatarImg.style.display = 'block';
            navAvatarIcon.style.display = 'none';
            preview.src = me.avatar_url;
        } else {
            navAvatarImg.style.display = 'none';
            navAvatarIcon.style.display = 'flex';
            preview.src = '';
        }
    } catch (err) {
        // profile is not critical for main features
        console.warn('loadMeAndFillUI failed:', err);
    }
}

function renderNotifications(items) {
    const tbody = document.querySelector('#notifications-table tbody');
    const unread = items.filter(n => !n.is_read).length;
    document.getElementById('notifications-unread-count').textContent = `${unread} 未读`;

    if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">暂无通知 / No notifications</td></tr>`;
        return;
    }

    const typeLabel = (t) => {
        if (t === 'announcement') return '系统公告';
        if (t === 'enrollment') return '选课通知';
        if (t === 'unenrollment') return '退选通知';
        if (t === 'grade') return '成绩通知';
        if (t === 'course_update') return '课程变更';
        if (t === 'course_assignment') return '课程分配';
        if (t === 'course_cancelled') return '停课通知';
        if (t === 'direct') return '消息';
        return t;
    };

    tbody.innerHTML = items.map(n => `
        <tr>
            <td><strong>${typeLabel(n.notif_type)}</strong></td>
            <td>
                ${n.title ? `<div style="font-weight:700; margin-bottom:0.2rem;">${escapeHtml(n.title)}</div>` : ''}
                <div style="color:var(--text-main)">${escapeHtml(n.content)}</div>
            </td>
            <td>${formatDateTime(n.created_at)}</td>
            <td>${n.is_read ? '<span style="color:var(--text-muted); font-weight:600;">已读</span>' : '<span style="color:var(--primary); font-weight:700;">未读</span>'}</td>
            <td>
                ${n.is_read ? '' : `<button class="btn default-btn sm-btn" onclick="markNotificationRead(${n.id})"><i class="fa-solid fa-check"></i> 已读</button>`}
            </td>
        </tr>
    `).join('');
}

async function loadNotifications() {
    try {
        const items = await apiCall('/notifications/my');
        renderNotifications(items);
    } catch (err) {
        showToast(err.message, true);
    }
}

window.markNotificationRead = async (id) => {
    try {
        await apiCall(`/notifications/${id}/read`, { method: 'PUT' });
        await loadNotifications();
    } catch (err) {
        showToast(err.message, true);
    }
};

document.getElementById('mark-all-read-btn')?.addEventListener('click', async () => {
    try {
        await apiCall('/notifications/read-all', { method: 'PUT' });
        await loadNotifications();
        showToast('已标记全部已读');
    } catch (err) {
        showToast(err.message, true);
    }
});

// ==== Message modal ====
window.openMessageModal = (receiverId, receiverName, relatedCourseId = null) => {
    document.getElementById('message-receiver-id').value = receiverId;
    document.getElementById('message-related-course-id').value = relatedCourseId ?? '';
    document.getElementById('message-receiver-label').textContent = receiverName ? `@${receiverName}` : '-';
    document.getElementById('message-content').value = '';
    document.getElementById('message-modal').classList.remove('hidden');
};

document.getElementById('send-message-btn')?.addEventListener('click', async () => {
    try {
        const receiverId = parseInt(document.getElementById('message-receiver-id').value);
        const relatedCourseIdRaw = document.getElementById('message-related-course-id').value;
        const relatedCourseId = relatedCourseIdRaw === '' ? null : parseInt(relatedCourseIdRaw);
        const content = document.getElementById('message-content').value;

        if (!receiverId) return showToast('请选择接收人', true);
        if (!content || !content.trim()) return showToast('消息内容不能为空', true);

        await apiCall('/notifications/direct', {
            method: 'POST',
            body: {
                receiver_id: receiverId,
                content,
                related_course_id: relatedCourseId,
            }
        });

        document.getElementById('message-modal').classList.add('hidden');
        showToast('消息发送成功 / Message sent');
        await loadNotifications();
    } catch (err) {
        showToast(err.message, true);
    }
});

// ==== Profile modal ====
document.getElementById('profile-btn')?.addEventListener('click', async () => {
    await loadMeAndFillUI();
    document.getElementById('profile-modal').classList.remove('hidden');
});

document.getElementById('save-profile-btn')?.addEventListener('click', async () => {
    try {
        const name = document.getElementById('profile-name').value;
        const phone = document.getElementById('profile-phone').value;
        await apiCall('/profile/me', {
            method: 'PUT',
            body: {
                name,
                phone_number: phone ? phone.trim() : null,
            }
        });
        showToast('个人信息已更新');
        await loadMeAndFillUI();
    } catch (err) {
        showToast(err.message, true);
    }
});

document.getElementById('password-change-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const current_password = document.getElementById('password-current').value;
        const new_password = document.getElementById('password-new').value;
        await apiCall('/profile/me/password', {
            method: 'PUT',
            body: { current_password, new_password }
        });
        showToast('密码修改成功');
        e.target.reset();
    } catch (err) {
        showToast(err.message, true);
    }
});

document.getElementById('profile-avatar-input')?.addEventListener('change', async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
        const form = new FormData();
        form.append('file', file);
        const res = await apiCall('/profile/me/avatar', { method: 'POST', body: form });
        showToast('头像已更新');
        const avatarUrl = res.avatar_url;
        const navAvatarImg = document.getElementById('nav-avatar-img');
        const navAvatarIcon = document.getElementById('nav-avatar-icon');
        const preview = document.getElementById('profile-avatar-preview');
        if (avatarUrl) {
            navAvatarImg.src = avatarUrl;
            navAvatarImg.style.display = 'block';
            navAvatarIcon.style.display = 'none';
            preview.src = avatarUrl;
        }
    } catch (err) {
        showToast(err.message, true);
    } finally {
        e.target.value = '';
    }
});

// ==== Exports (CSV) ====
function csvEscape(val) {
    const s = String(val ?? '');
    if (/[",\n\r]/.test(s)) return `"${s.replaceAll('"', '""')}"`;
    return s;
}

function downloadCSV(filename, rows) {
    const csv = rows.map(r => r.map(csvEscape).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

function exportStudentTimetable() {
    if (!myCoursesData || myCoursesData.length === 0) {
        showToast('暂无可导出的课表数据', true);
        return;
    }
    const rows = [
        ['课程名称', '教师', '上课时间', '上课地点', '学分', '成绩'],
        ...myCoursesData.map(c => [
            c.course_name,
            c.teacher_name || '',
            c.class_time || '',
            c.class_location || '',
            c.credits,
            c.grade !== null && c.grade !== undefined ? c.grade : '',
        ]),
    ];
    const stamp = new Date().toISOString().slice(0, 10);
    downloadCSV(`student_timetable_${stamp}.csv`, rows);
}

function exportStudentGrades() {
    if (!myCoursesData || myCoursesData.length === 0) {
        showToast('暂无可导出的成绩数据', true);
        return;
    }
    const graded = myCoursesData.filter(c => c.grade !== null && c.grade !== undefined);
    const rows = [
        ['课程名称', '教师', '学分', '成绩'],
        ...(graded.length ? graded : myCoursesData).map(c => [
            c.course_name,
            c.teacher_name || '',
            c.credits,
            c.grade !== null && c.grade !== undefined ? c.grade : '',
        ]),
    ];
    const stamp = new Date().toISOString().slice(0, 10);
    downloadCSV(`student_grades_${stamp}.csv`, rows);
}

document.getElementById('export-timetable-btn')?.addEventListener('click', exportStudentTimetable);
document.getElementById('export-grades-btn')?.addEventListener('click', exportStudentGrades);

// ==== Admin announcement ====
document.getElementById('announcement-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const title = document.getElementById('announcement-title').value;
        const content = document.getElementById('announcement-content').value;
        await apiCall('/admin/announcements', {
            method: 'POST',
            body: { title, content }
        });
        showToast('公告已发送');
        e.target.reset();
        await loadNotifications();
    } catch (err) {
        showToast(err.message, true);
    }
});

init();
