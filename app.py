import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = 'students.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/students')
def students():
    db = get_db()
    students_list = db.execute('SELECT * FROM student').fetchall()
    return render_template('students.html', students=students_list)

@app.route('/courses')
def courses():
    db = get_db()
    courses_list = db.execute('SELECT * FROM course').fetchall()
    return render_template('courses.html', courses=courses_list)

@app.route('/grades')
def grades():
    db = get_db()
    query = """
        SELECT p.id, s.name as student_name, c.title as course_title, p.value 
        FROM points p
        JOIN student s ON p.id_student = s.id
        JOIN course c ON p.id_course = c.id
    """
    grades_list = db.execute(query).fetchall()
    return render_template('grades.html', grades=grades_list)

@app.route('/student/<int:id_student>')
def student_grades(id_student):
    db = get_db()
    student = db.execute('SELECT * FROM student WHERE id = ?', (id_student,)).fetchone()
    query = """
        SELECT c.title, c.semester, p.value, p.id
        FROM points p
        JOIN course c ON p.id_course = c.id
        WHERE p.id_student = ?
    """
    grades = db.execute(query, (id_student,)).fetchall()
    return render_template('student_grades.html', student=student, grades=grades)

@app.route('/add_grade', methods=['GET', 'POST'])
def add_grade():
    db = get_db()
    if request.method == 'POST':
        id_student = request.form['id_student']
        id_course = request.form['id_course']
        value = request.form['value']
        db.execute('INSERT INTO points (id_student, id_course, value) VALUES (?, ?, ?)',
                   (id_student, id_course, value))
        db.commit()
        return redirect(url_for('grades'))
    
    all_students = db.execute('SELECT * FROM student').fetchall()
    all_courses = db.execute('SELECT * FROM course').fetchall()
    return render_template('add_grade.html', students=all_students, courses=all_courses)

@app.route('/delete_grade/<int:id>', methods=['POST'])
def delete_grade(id):
    db = get_db()
    db.execute('DELETE FROM points WHERE id = ?', (id,))
    db.commit()
    return redirect(request.referrer or url_for('grades'))

@app.route('/stats')
def stats():
    db = get_db()
    avg_query = """
        SELECT c.title, AVG(p.value) as avg_score
        FROM points p
        JOIN course c ON p.id_course = c.id
        GROUP BY c.title
    """
    avg_results = db.execute(avg_query).fetchall()
    
    ects_query = """
        SELECT c.title,
               COUNT(CASE WHEN p.value >= 90 THEN 1 END) as count_A,
               COUNT(CASE WHEN p.value >= 75 AND p.value < 90 THEN 1 END) as count_B,
               COUNT(CASE WHEN p.value >= 60 AND p.value < 75 THEN 1 END) as count_C,
               COUNT(CASE WHEN p.value < 60 THEN 1 END) as count_F
        FROM points p
        JOIN course c ON p.id_course = c.id
        GROUP BY c.title
    """
    ects_results = db.execute(ects_query).fetchall()
    return render_template('stats.html', avg_results=avg_results, ects_results=ects_results)

@app.route('/hello2')
def hello2():
    name = request.args.get('name', 'World')
    return render_template('hello.html.j2', name=name)

@app.after_request
def add_security_headers(response): 
    policy = (
        "default-src 'self' https://cdn.jsdelivr.net; "
        "script-src 'self'; "
        "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'"
    )
    response.headers['Content-Security-Policy'] = policy
    return response

if __name__ == '__main__':
    app.run(debug=True)