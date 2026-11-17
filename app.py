from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'

# قاعدة بيانات وهمية مبسطة للتجربة السريعة
# المستخدمين: (username, password, role, name, student_name)
USERS = {
    'admin': {'password': '123', 'role': 'admin', 'name': 'المدير'},
    'teacher1': {'password': '123', 'role': 'teacher', 'name': 'الأستاذ أحمد', 'students': ['خالد أحمد', 'سعيد أحمد']},
    'parent1': {'password': '123', 'role': 'parent', 'name': 'والد خالد', 'student': 'خالد أحمد', 'reports': 'مستوى الطالب ممتاز ومشارك جيد في الفصل.'}
}

# تخزين ملاحظات الطلاب التي يعدلها المدرسون
STUDENT_REPORTS = {
    'خالد أحمد': 'الملاحظة الأولى: منتظم في الحضور وشارك اليوم بتميز.',
    'سعيد أحمد': 'الملاحظة الأولى: يحتاج إلى متابعة في مادة الرياضيات.'
}

# صفحة تسجيل الدخول
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
        button:hover { background: #0056b3; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="card">
        <h2>نظام متابعة الطلاب</h2>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم (مثال: teacher1)" required><br>
            <input type="password" name="password" placeholder="كلمة المرور (123)" required><br>
            <button type="submit">دخول</button>
        </form>
        <p style="font-size: 12px; color: #666; margin-top: 15px;">
            جرب الدخول بـ:<br>
            المدرس: <b>teacher1</b> / كلمة المرور: <b>123</b><br>
            ولي الأمر: <b>parent1</b> / كلمة المرور: <b>123</b>
        </p>
    </div>
</body>
</html>
'''

# لوحة تحكم المدرس
TEACHER_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة المعلم</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #f4f7f6; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
        button { background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .logout { float: left; color: red; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/logout" class="logout">تسجيل خروج</a>
        <h2>أهلاً بك، {{ user.name }}</h2>
        <h3>طلابك المخصصون:</h3>
        <hr>
        {% for student in user.students %}
            <h4>📁 ملف الطالب: {{ student }}</h4>
            <form method="POST" action="/update_student">
                <input type="hidden" name="student_name" value="{{ student }}">
                <textarea name="report">{{ reports.get(student, '') }}</textarea><br>
                <button type="submit">حفظ وتحديث الملف</button>
            </form>
            <hr>
        {% endfor %}
    </div>
</body>
</html>
'''

# لوحة ولي الأمر
PARENT_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        <h3>آخر الأخبار والملاحظات المدرسية:</h3>
        <div class="report-box">
            <p>{{ reports.get(user.student, 'لا توجد ملاحظات حالياً.') }}</p>
        </div>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            if USERS[username]['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif USERS[username]['role'] == 'parent':
                return redirect(url_for('parent_dashboard'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غير صحيحة'
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/teacher')
def teacher_dashboard():
    if 'username' not in USERS or USERS.get(session.get('username'), {}).get('role') != 'teacher':
        return redirect(url_for('login'))
    user = USERS[session['username']]
    return render_template_string(TEACHER_PAGE, user=user, reports=STUDENT_REPORTS)

@app.route('/update_student', methods=['POST'])
def update_student():
    if 'username' not in session:
        return redirect(url_for('login'))
    student_name = request.form.get('student_name')
    new_report = request.form.get('report')
    STUDENT_REPORTS[student_name] = new_report
    return redirect(url_for('teacher_dashboard'))

@app.route('/parent')
def parent_dashboard():
    if 'username' not in session or USERS.get(session.get('username'), {}).get('role') != 'parent':
        return redirect(url_for('login'))
    user = USERS[session['username']]
    return render_template_string(PARENT_PAGE, user=user, reports=STUDENT_REPORTS)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

