
# SQL Evaluation App

from flask import Flask, request, redirect, render_template, session, send_file
from uuid import uuid4

import mysql.connector
import hashlib
import csv

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

@app.route("/home", methods=["GET"])
def doesntmatter():
    return render_template("/home.html")

@app.route("/home", methods=["POST"])
def sql_submit():
    aid = int(request.form['aid'])
    tid = int(request.form['tid'])
    code = request.form['code']
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    result = cursor.callproc("submit_sql", (session['number'], aid, tid, code, ''))
    cnx.commit()
    cursor.close()
    cnx.close()
    return "submitted"
    #return render_template('submit_result.html', username=result[4], aid=aid, tid=tid, code=code)
    #return render_template('submit.html')


@app.route("/login", methods=['GET', 'POST'])
def sql_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        m = hashlib.md5()
        m.update(request.form['password'].encode('UTF-8'))
        password = m.hexdigest()
        cnx = mysql.connector.connect(**config)

        cursor = cnx.cursor()
        cursor.execute("SELECT username FROM students WHERE username=%s AND password_hash=%s", (username, password))  #student/students
        result_rows = cursor.fetchone()
        #return "success3"
        if len(result_rows) != 1 or result_rows[0][0] != username:
            error = 'Invalid Credentials. Please try again.'
            cursor.close()
            cnx.close()
            #return "success4"
            return error
        else:
            session['number'] = str(uuid4())
            cursor.execute("INSERT INTO sessions (session_num, started_at, username) VALUES (%s, now(), %s)", (session['number'], username)) #start_at/started_at
            cnx.commit()
            cursor.close()
            cnx.close()
            #return "success"
            return redirect('/home')                 #POST is go to next page (@app.route("/home", methods=["GET"]) look above
    return render_template('login.html', error=error) #GET is Display this login.html

@app.route('/register', methods=['POST'])
def register_student():
    username = request.form.get('username')
    m = hashlib.md5()
    m.update(request.form['password'].encode('UTF-8'))
    password = m.hexdigest()
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute("INSERT INTO students (username, password_hash) VALUES (%s,%s)", (username, password))
    cnx.commit()
    cursor.close()
    cnx.close()
    return render_template('login.html', message='Account successfully created.')


@app.route('/')  # default home page
def hello_world():
    return render_template("/login.html") #  display login.html
    #return 'Hello from Flask 2!'
    
@app.route('/download')
def download_scores():
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute("SELECT students.username, submissions.score FROM submissions INNER JOIN students on submissions.username = students.username ORDER BY submissions.score DESC limit 999;")
    return_rows = cursor.fetchall()
    try:
        with open('output_scores.csv', 'w', newline='') as scores:
            csv_writer = csv.writer(scores)
            csv_writer.writerows(return_rows)
            scores.close()
    except:
        return "Error writing to file."
    cursor.close()
    cnx.close()
    return send_file(scores, mimetype='text', as_attachment=True, download_name='scores.csv')
    
   