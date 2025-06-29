
# SQL Evaluation App

from flask import Flask, request, redirect, render_template, session, send_file, jsonify, Response
from uuid import uuid4
from io import StringIO
import mysql.connector, hashlib, csv, datetime, difflib

## connection config
config = {
            'host':"chaojun.mysql.pythonanywhere-services.com",
            'user':"chaojun",
            'password':"12345!@#$%",
            'database':"chaojun$sqleval",
            'raise_on_warnings': True
            }

app = Flask(__name__)
app.debug = True
app.secret_key = '12345!@#$%'

@app.route('/')  # default home page
def hello_world():
    return render_template("/login.html") #  display login.html
    #return 'Hello from Flask 2!'
    
@app.route("/home", methods=["GET"])
def get_assessment():
    cnx = None
    cursor = None
    try:
        # Establish connection inside the try block
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor(dictionary=True) # dictionary=True is often more useful

        cursor.execute("SELECT a.a_id, a.title a_title, t.t_id, t.title t_title FROM assessments a INNER JOIN tasks t ON t.a_id = a.a_id ORDER BY a.due_date ASC limit 1;")
        eval_rec = cursor.fetchone()
        a_id = eval_rec['a_id']
        a_title = eval_rec['a_title']
        t_id = eval_rec['t_id']
        t_title = eval_rec['t_title']
        return render_template('/home.html', a_id=a_id, a_title=a_title, t_id=t_id, t_title=t_title)
    
    except mysql.connector.Error as err:
            # Handle potential database errors gracefully
            error = f"Database error: {err}"
    finally:
            # This block runs whether the try succeeded, failed, or returned.
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()
    return render_template('/home.html', error=error)

## login
@app.route("/login", methods=['GET', 'POST'])
def sql_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username') # Use .get() to avoid KeyError
        m = hashlib.md5()
        m.update(request.form['password'].encode('UTF-8'))
        password = m.hexdigest()
        cnx = None
        cursor = None
        try:
            # Establish connection inside the try block
            cnx = mysql.connector.connect(**config)
            cursor = cnx.cursor(dictionary=True) # dictionary=True is often more useful

            # Select the user's HASH from the database
            cursor.execute("SELECT username, password_hash FROM students WHERE username=%s and password_hash=%s", (username,password))
            user = cursor.fetchone()

            # 1. Check if user exists
            # 2. If user exists, check if the password hash matches
            if user is None:
                error = 'Invalid credentials. Please try again.'
            else:
                # Login successful, create the session
                session['user'] = user['username'] # Storing username is also useful
                session['number'] = str(uuid4())

                sql = "INSERT INTO sessions (session_num, username, started_at) VALUES (%s, %s, now())"
                cursor.execute(sql, (session['number'], username))
                cnx.commit()

                return redirect('/home') # Redirect on success

        except mysql.connector.Error as err:
            # Handle potential database errors gracefully
            error = f"Database error: {err}"
        finally:
            # This block runs whether the try succeeded, failed, or returned.
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()

    # On a GET request OR a failed POST, render the login page with the error
    return render_template('login.html', error=error)

## create user
@app.route('/register', methods=['POST'])
def register_student():
    username = request.form.get('username')
    m = hashlib.md5()
    m.update(request.form['password'].encode('UTF-8'))
    password = m.hexdigest()
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO students (username, password_hash) VALUES (%s,%s)", (username, password))
        cnx.commit()
        return render_template('login.html', message='Account successfully created.')
    
    except mysql.connector.Error as err:
            error = f"Database error: {err}"
    finally:
        # This block runs whether the try succeeded, failed, or returned.
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
            
    return render_template('login.html', error=error)

## update password
@app.route('/update', methods=['POST'])
def update_password():
    username = request.form.get('username')
    m = hashlib.md5()
    m.update(request.form['password'].encode('UTF-8'))
    password = m.hexdigest()
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        cursor.execute("SELECT * from students WHERE username=%s and password_hash=%s", (username,password))
        rec = cursor.fetchone()
        if not rec:
            return render_template('login.html', error='Username or password is incorrect.')
        
        n = hashlib.md5()
        n.update(request.form['new_password'].encode('UTF-8'))
        password = n.hexdigest()
        cursor.execute("UPDATE students SET password_hash=%s WHERE username=%s", (password, username))
        cnx.commit()
        return render_template('login.html', message='Password updated successfully.')
    
    except mysql.connector.Error as err:
            error = f"Database error: {err}"
    finally:
        # This block runs whether the try succeeded, failed, or returned.
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
            
    return render_template('login.html', error=error)

## grade submission
def grade_submission(username, a_id, t_id):
    db = mysql.connector.connect(**config)
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT submission_id, codebase FROM submissions
            WHERE username = %s AND a_id = %s AND t_id = %s
            ORDER BY attempt_number DESC LIMIT 1
        """, (username, a_id, t_id))
        submission = cursor.fetchone()

        if not submission:
            return {'message': 'Submission not found'}

        submission_id, student_sql = submission

        cursor.execute("""
            SELECT model_answer FROM model_answers
            WHERE a_id = %s AND t_id = %s
        """, (a_id, t_id))
        model = cursor.fetchone()

        if not model:
            return {'message': 'Model answer not found'}

        model_sql = model[0]

        try:
            cursor.execute(student_sql)
            student_result = cursor.fetchall()

            cursor.execute(model_sql)
            model_result = cursor.fetchall()

            if student_result == model_result:
                score = 100
            else:
                similarity = difflib.SequenceMatcher(None, str(sorted(student_result)), str(sorted(model_result))).ratio()
                score = int(similarity * 100)

        except Exception as e:
            score = 0

        cursor.execute("""
            UPDATE submissions SET score = %s
            WHERE submission_id = %s
        """, (score, submission_id))
        db.commit()

        return {'message': 'Grading completed', 'score': score}

    except Exception as e:
        db.rollback()
        return {'message': 'Error', 'error': str(e)}

    finally:
        cursor.close()
        db.close()

## score export
@app.route('/download')
def download_scores():
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute("SELECT stu.username, s.score, s.submission_id FROM submissions s INNER JOIN students stu on s.username = stu.username ORDER BY s.score DESC limit 999;")
    return_rows = cursor.fetchall()
    header = ['Username', 'Score','Submission Id']
    try:
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(header)
        writer.writerows(return_rows)
        output = Response(si.getvalue(), mimetype='text/csv')
        output.headers['Content-Disposition'] = 'attachment; filename=all_student_scores.csv'
        return output
            
    except:
        return render_template('/score', error="Error writing to file.")

'''## submit attempt
@app.route('/submit', methods=['POST'])
def submit_solution():
    data = request.get_json()
    username = data['username']
    a_id = data['a_id']
    t_id = data['t_id']
    sql_solution = data['sql_solution']

    db = mysql.connector.connect(**config)
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1
            FROM submissions
            WHERE username = %s AND a_id = %s AND t_id = %s
        """, (username, a_id, t_id))
        attempt_number = cursor.fetchone()[0]

        #save submission
        cursor.execute("""
            INSERT INTO submissions (username, a_id, t_id, codebase, submit_at, attempt_number, score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (username, a_id, t_id, sql_solution, datetime.now(), attempt_number, None))
        db.commit()

        #auto-grade the submission
        grade_result = grade_submission(username, a_id, t_id)

        return jsonify({
            'message': 'Submission saved and graded',
            'attempt_number': attempt_number,
            'grade_result': grade_result
        })

    except Exception as e:
        db.rollback()
        return jsonify({'message': 'Submission failed', 'error': str(e)}), 400

    finally:
        cursor.close()
        db.close()'''
        
## late submission penalty
@app.route('/submit', methods=['POST'])
def submit_solution():
    a_id = int(request.form['a_id'])
    t_id = int(request.form['t_id'])
    sql_solution = request.form['code']
    submit_time = datetime.datetime.now()
    session_id = session['number']

    db = mysql.connector.connect(**config)
    cursor = db.cursor()

    try:
        cursor.execute("SELECT username FROM sessions WHERE sessions.session_num = %s limit 1;",(session_id,))
        username = cursor.fetchone()[0]
        # Get next attempt number
        cursor.execute("""
            SELECT COALESCE(MAX(attempt_number), 0) + 1
            FROM submissions
            WHERE username = %s AND a_id = %s AND t_id = %s
        """, (username, a_id, t_id))
        attempt_number = cursor.fetchone()[0]

        # Insert submission with NULL score first
        cursor.execute("""
            INSERT INTO submissions (username, a_id, t_id, codebase, submit_at, attempt_number, score)
            VALUES (%s, %s, %s, %s, %s, %s, NULL)
        """, (username, a_id, t_id, sql_solution, submit_time, attempt_number))
        db.commit()

        # Grade the latest submission (updates raw score in DB)
        grade_response = grade_submission(username, a_id, t_id)

        # Get submission_id and raw score (just graded)
        cursor.execute("""
            SELECT submission_id, COALESCE(score,0) FROM submissions
            WHERE username = %s AND a_id = %s AND t_id = %s AND attempt_number = %s
        """, (username, a_id, t_id, attempt_number))
        sub = cursor.fetchone()
        submission_id = sub[0]
        raw_score = sub[1]

        # Get due date
        cursor.execute("SELECT due_date FROM assessments WHERE a_id = %s", (a_id,))
        due_date = cursor.fetchone()[0]

        # Check if late
        if submit_time > due_date:
            penalized_score = round(raw_score * 0.9, 2)
            cursor.execute("""
                UPDATE submissions SET score = %s
                WHERE submission_id = %s
            """, (penalized_score, submission_id))
            db.commit()
            return render_template('/submission.html', message=f'Submission saved and graded. Score: {penalized_score}. Status: Late.')
        else:
            
            return render_template('/submission.html', message=f'Submission saved and graded. Score: {raw_score}. Status: Submitted on time.')


    except Exception as e:
        db.rollback()
        return render_template('/submission.html', error=f"Submission failed. Error: {e}")
        

    finally:
        cursor.close()
        db.close()

## user score detail
@app.route('/score')
def score():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.title AS assessment_title, t.title AS task_title,
               s.attempt_number, s.score, s.submit_at
        FROM submissions s
        JOIN assessments a ON s.a_id = a.a_id
        JOIN tasks t ON s.t_id = t.t_id
        WHERE s.username = %s
        ORDER BY s.submit_at DESC
    """, (username,))
    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('score.html', records=records)

## score leaderboard
@app.route('/leaderboard')
def leaderboard():
    if 'user' not in session:
        return redirect('/login')

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM assessments")
    assessments = cursor.fetchall()

    aid = request.args.get('a_id') or (assessments[0]['a_id'] if assessments else None)

    if aid:
        cursor.execute("""
            SELECT s.username, AVG(s.score) AS avg_score
            FROM submissions s
            JOIN (
                SELECT username, t_id, MAX(attempt_number) AS max_attempt
                FROM submissions
                WHERE a_id = %s
                GROUP BY username, t_id
            ) latest
            ON s.username = latest.username AND s.t_id = latest.t_id AND s.attempt_number = latest.max_attempt
            WHERE s.a_id = %s AND s.score IS NOT NULL
            GROUP BY s.username
            ORDER BY avg_score DESC
            LIMIT 5
        """, (aid, aid))
        leaders = cursor.fetchall()
    else:
        leaders = []

    cursor.close()
    conn.close()

    return render_template('leaderboard.html', leaders=leaders, assessments=assessments, selected_aid=int(aid) if aid else None)

## resubmission tracker
@app.route('/submission-history', methods=['GET'])
def submission_history():
    username = request.args.get('username')  # or get from current session?
    db = mysql.connector.connect(**config)
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT a_id, t_id, attempt_number, codebase, score, submit_at
        FROM submissions
        WHERE username = %s
        ORDER BY a_id, t_id, attempt_number DESC
    """, (username,))
    records = cursor.fetchall()

    cursor.close()
    db.close()
    return jsonify(records), 200

