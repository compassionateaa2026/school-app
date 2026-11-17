import os
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'

# إعداد مجلد لرفع الملفات (صور، فيديو، مستندات)
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'docx', 'doc'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# قاعدة بيانات تجريبية قابلة للتحديث
USERS = {
    'agent1': {'password': '123', 'role': 'agent', 'name': 'الوكيل العام'},
    'teacher1': {'password': '123', 'role': 'teacher', 'name': 'الأستاذ أحمد', 'students': []},
    'parent1': {'password': '123', 'role': 'parent', 'name': 'والد خالد', 'student': 'خالد أحمد'}
}

# تخزين بيانات الطلاب وتقاريرهم ومرفقاتهم
STUDENTS_DATA = {
    'خالد أحمد': {'reports': 'الملاحظة الأولى: منتظم في الحضور.', 'files': []}
}

LOGIN_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - النظام المدرسي</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #f4f7f6; padding: 20px; text-align: center; }
        .card { background: white; max-width: 400px; margin: 50px auto; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        input, button { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; font-size: 16px; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="card">
        <h2>نظام متابعة الطلاب</h2>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required><br>
            <input type="password" name="password" placeholder="كلمة المرور" required><br>
            <button type="submit">دخول</button>
        </form>
        <p style="font-size: 11px; color: #666; margin-top: 15px;">
            الوكيل: <b>agent1</b> / 123<br>
            المعلم: <b>teacher1</b> / 123<br>
            ولي الأمر: <b>parent1</b> / 123
        </p>
    </div>
</body>
</html>
'''

AGENT_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة الوكيل</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #f4f7f6; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        input, button { width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; }
        button { background: #28a745; color: white; border: none; cursor: pointer; }
        .logout { float: left; color: red; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/logout" class="logout">تسجيل خروج</a>
        <h2>لوحة تحكم الوكيل: {{ user.name }}</h2>
        <hr>
        <h3>إضافة مدرس جديد</h3>
        <form method="POST" action="/add_teacher">
            <input type="text" name="teacher_username" placeholder="اسم مستخدم المعلم (مثل: teacher2)" required><br>
            <input type="password" name="teacher_password" placeholder="كلمة المرور" required><br>
            <input type="text" name="teacher_name" placeholder="اسم المعلم الرباعي" required><br>
            <button type="submit">إضافة المدرس</button>
        </form>
        <h3>المدرسون المسجلون:</h3>
        <ul>
            {% for uname, udata in users.items() if udata.role == 'teacher' %}
                <li>{{ udata.name }} (اسم المستخدم: {{ uname }})</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
'''

TEACHER_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة المعلم</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #f4f7f6; padding: 20px; }
        .container { max-width: 650px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        textarea, input { width: 95%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 5px; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .logout { float: left; color: red; text-decoration: none; }
        .student-card { background: #f9f9f9; padding: 15px; margin-top: 15px; border-radius: 5px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/logout" class="logout">تسجيل خروج</a>
        <h2>أهلاً بك يا استاذ: {{ user.name }}</h2>
        <p>عدد طلابك الحاليين: {{ user.students|length }} / 20</p>
        <hr>
        
        {% if user.students|length < 20 %}
        <h3>إضافة طالب جديد</h3>
        <form method="POST" action="/add_student">
            <input type="text" name="student_name" placeholder="اسم الطالب الكامل" required>
            <button type="submit">إضافة الطالب</button>
        </form>
        <hr>
        {% else %}
        <p style="color: red;">لقد وصلت الحد الأقصى (20 طالباً).</p>
        {% endif %}

        <h3>إدارة طلابك ورفع الملفات (صور، فيديو، تقارير PDF/Word):</h3>
        {% for student in user.students %}
            <div class="student-card">
                <h4>📁 الطالب: {{ student }}</h4>
                <form method="POST" action="/update_student" enctype="multipart/form-data">
                    <input type="hidden" name="student_name" value="{{ student }}">
                    <label>التقرير المكتوب:</label><br>
                    <textarea name="report">{{ students_data.get(student, {}).get('reports', '') }}</textarea><br>
                    <label>إرفاق ملف (صورة، فيديو، PDF، Word):</label><br>
                    <input type="file" name="file"><br>
                    <button type="submit">حفظ وتحديث الملف</button>
                </form>
                
                {% if students_data.get(student, {}).get('files') %}
                    <p><b>الملفات المرفوعة:</b></p>
                    <ul>
                    {% for f in students_data[student]['files'] %}
                        <li><a href="{{ url_for('download_file', filename=f) }}" target="_blank">{{ f }}</a></li>
                    {% endfor %}
                    </ul>
                {% endif %}
            </div>
        {% endfor %}
    </div>
</body>
</html>
'''

PARENT_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>متابعة ولي الأمر</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #f4f7f6; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .report-box { background: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 15px; }
        .logout { float: left; color: red; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/logout" class="logout">تسجيل خروج</a>
        <h2>متابعة الطالب: {{ user.student }}</h2>
        <p>ولي الأمر: {{ user.name }}</p>
        <hr>
        <h3>التقارير والمرفقات المدرسية:</h3>
        <div class="report-box">
            <p>{{ students_data.get(user.student, {}).get('reports', 'لا توجد ملاحظات حالياً.') }}</p>
            {% if students_data.get(user.student, {}).get('files') %}
                <p><b>المرفقات:</b></p>
                <ul>
                {% for f in students_data[user.student]['files'] %}
                    <li><a href="{{ url_for('download_file', filename=f) }}" target="_blank">تحميل / عرض: {{ f }}</a></li>
                {% endfor %}
                </ul>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            role = USERS[username]['role']
            if role == 'agent':
                return redirect(url_for('agent_dashboard'))
            elif role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif role == 'parent':
                return redirect(url_for('parent_dashboard'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غير صحيحة'
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/agent')
def agent_dashboard():
    if 'username' not in session or USERS.get(session['username'], {}).get('role') != 'agent':
        return redirect(url_for('login'))
    return render_template_string(AGENT_PAGE, user=USERS[session['username']], users=USERS)

@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    if 'username' not in session or USERS.get(session['username'], {}).get('role') != 'agent':
        return redirect(url_for('login'))
    t_user = request.form.get('teacher_username').strip()
    t_pass = request.form.get('teacher_password').strip()
    t_name = request.form.get('teacher_name').strip()
    if t_user and t_user not in USERS:
        USERS[t_user] = {'password': t_pass, 'role': 'teacher', 'name': t_name, 'students': []}
    return redirect(url_for('agent_dashboard'))

@app.route('/teacher')
def teacher_dashboard():
    if 'username' not in session or USERS.get(session['username'], {}).get('role') != 'teacher':
        return redirect(url_for('login'))
    user = USERS[session['username']]
    return render_template_string(TEACHER_PAGE, user=user, students_data=STUDENTS_DATA)

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'username' not in session or USERS.get(session['username'], {}).get('role') != 'teacher':
        return redirect(url_for('login'))
    user = USERS[session['username']]
    student_name = request.form.get('student_name').strip()
    
    if student_name and len(user['students']) < 20 and student_name not in user['students']:
        user['students'].append(student_name)
        if student_name not in STUDENTS_DATA:
            STUDENTS_DATA[student_name] = {'reports': '', 'files': []}
            
    return redirect(url_for('teacher_dashboard'))

@app.route('/update_student', methods=['POST'])
def update_student():
    if 'username' not in session or USERS.get(session['username'], {}).get('role') != 'teacher':
        return redirect(url_for('login'))
    student_name = request.form.get('student_name')
    new_report = request.form.get('report')
    
    if student_name in STUDENTS_DATA:
        STUDENTS_DATA[student_name]['reports'] = new_report
        
    file = request.files.get('file')
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        if filename not in STUDENTS_DATA[student_name]['files']:
            STUDENTS_DATA[student_name]['files'].append(filename)
            
    return redirect(url_for('teacher_dashboard'))

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/parent')
def parent_dashboard():
    if 'username' not in session or USERS.get(session['username'], {}).get('role') != 'parent':
        return redirect(url_for('login'))
    user = USERS[session['username']]
    return render_template_string(PARENT_PAGE, user=user, students_data=STUDENTS_DATA)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

