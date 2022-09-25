from asyncio.windows_events import NULL
from pickle import FALSE, TRUE

from threading import activeCount
from flask import Flask, render_template, request, redirect, url_for, session
import ibm_db
app = Flask(__name__,template_folder='C:/Users/user/source/repos/IBMAss')

try:
    conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=b0aebb68-94fa-46ec-a1fc-1c999edb6187.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=31249;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;PROTOCOL=TCPIP;UID=xcq72200;PWD=LMV8M41c4stsjNXi;", "", "")
    print("Connected to DB")
except Exception as e:
    print(e)

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        sql ="SELECT * FROM STUDENT WHERE USERNAME = ? AND PASSWORD = ?"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt, 1, username)
        ibm_db.bind_param(stmt, 2, password)
        out=ibm_db.execute(stmt)
        flag=FALSE
        while ibm_db.fetch_row(stmt) != False:
            flag=TRUE
            session['loggedin'] = True
            session['username'] = ibm_db.result(stmt,0)
            msg = 'Logged in successfully !'
            return render_template('homepage.html', msg = msg)
        if flag==FALSE:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))
 
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        regno=request.form['regno']
        email = request.form['email']
        sql="SELECT * FROM STUDENT WHERE USERNAME = ?"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt, 1, username)
        out=ibm_db.execute(stmt)
        flag=FALSE
        while ibm_db.fetch_row(stmt) != False:
            flag=TRUE
        if flag==TRUE:
            msg = 'Account already exists !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            sql="INSERT INTO STUDENT VALUES(?,?,?,?)"
            stmt = ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt, 1, username)
            ibm_db.bind_param(stmt, 2, email)
            ibm_db.bind_param(stmt, 3, password)
            ibm_db.bind_param(stmt, 4, regno)
            out=ibm_db.execute(stmt)
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)

if __name__=='__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    
    app.run()
