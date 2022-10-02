from flask import Flask,render_template,request,flash
import ibm_db

app = Flask(__name__)

def connection():
    try:
        conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=19af6446-6171-4641-8aba-9dcff8e1b6ff.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=30699;PROTOCOL=TCPIP;UID=ddb22023;PWD=pm6CGacdO7nzi3pU;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;", "", "")
        print("CONNECTED TO DATABASE")
        return conn
    except:
        print("CONNECTION FAILED")

@app.route("/",methods=["GET","POST"])
def registerPage():
    if request.method=="POST":
        conn=connection()
        try:
            sql="INSERT INTO USER VALUES('{}','{}','{}','{}')".format(request.form["uemail"],request.form["uname"],request.form["urollno"],request.form["upass"])
            ibm_db.exec_immediate(conn,sql)
            flash("Successfully Registered")
            return render_template('login.html')
        except:
            flash("Account already exists")
            return render_template('register.html')
    else:
        return render_template('register.html')

@app.route("/login",methods=["GET","POST"])
def loginPage():
    if request.method=="POST":
        conn=connection()
        username=request.form["luname"]
        password=request.form["lupass"]
        sql="SELECT COUNT(*) FROM USER WHERE USERNAME=? AND PASSWRD=?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,username)
        ibm_db.bind_param(stmt,2,password)
        ibm_db.execute(stmt)
        res=ibm_db.fetch_assoc(stmt)
        if res['1']==1:
            return render_template("Welcome.html")
        else:
            flash("Wrong Username or Password")
            return render_template('login.html')
    else:
        return render_template('login.html')


if __name__=='__main__':
    app.config['SECRET_KEY']='super secret key'
    app.config['SESSION_TYPE']='filesystem'
    app.run(debug=True)

