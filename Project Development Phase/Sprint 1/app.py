import ibm_db
from flask import Flask, url_for, render_template, request, session, redirect, flash, send_file
from authlib.integrations.flask_client import OAuth
import traceback
from datetime import date
from io import BytesIO
 
app = Flask(__name__)
oauth = OAuth(app)
arr2=[]

def connection():
    try:
        #jesima db2 credential
        conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=b70af05b-76e4-4bca-a1f5-23dbb4c6a74e.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;\
            PORT=32716;PROTOCOL=TCPIP;UID=rmy92863;PWD=DDoUqjA0drfzoKCm;SECURITY=SSL;SSLServiceCertificate=DigiCertGlobalRootCA.crt", "", "")
        print("CONNECTED TO DATABASE")
        return conn
    except:
        print(ibm_db.conn_errormsg())
        print("CONNECTION FAILED")

@app.route('/google')
def google():
    GOOGLE_CLIENT_ID = '367786402665-skc738qj1tacaf0kkrkcgolap5775qia.apps.googleusercontent.com'
    GOOGLE_CLIENT_SECRET = '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'
     
    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    # Redirect to google_auth function
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)
 
@app.route('/google/auth')
def google_auth():
    token = oauth.google.authorize_access_token()
    user = oauth.google.parse_id_token(token,None)
    print(" Google User ", user)
    try:
        conn=connection()
        sql="INSERT INTO USERS VALUES(?,?)"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt, 1, user['name'])
        ibm_db.bind_param(stmt, 2,user['email'])
           
        out=ibm_db.execute(stmt)
    except Exception as e:
        print(e)
    return render_template('index.html')

#Home Page
@app.route("/")
def home():
    return render_template('index.html')

#Logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return render_template("index.html")

#Filter Jobs
@app.route('/FilteredJobs',methods=['POST','GET'])
def FilteredJobs():
    #arr=[]
    if request.method == "POST":
            data = {}   
            data['role'] = request.json['role']
            data['loc'] = request.json['loc']
            data['type'] = request.json['type']

            try:
                conn=connection()
                sql ="SELECT * FROM JOBS WHERE (LOCATION = ? AND JOBTYPE = ?) AND ROLE = ? "
                stmt = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(stmt, 1, data['loc'])
                ibm_db.bind_param(stmt,2,data['type'])
                ibm_db.bind_param(stmt,3,data['role'])
                out=ibm_db.execute(stmt)
                while ibm_db.fetch_row(stmt) != False:
                     inst={}
                     inst['COMPANY']=ibm_db.result(stmt,1)
                     inst['ROLE']=ibm_db.result(stmt,3)
                     inst['SALARY']=ibm_db.result(stmt,11)
                     inst['LOCATION']=ibm_db.result(stmt,10)
                     inst['JOBTYPE']=ibm_db.result(stmt,5)
                     inst['POSTEDDATE']=ibm_db.result(stmt,16)
                
                     arr2.append(inst)
                     print(arr2)
           
            except Exception as e:
                print(e)
           
    return render_template('job_listing.html',arr=arr2)


@app.route('/filter')
def filter():
    return render_template('job_listing.html',arr=arr2)

#Job Listing - Seeker Home Page
@app.route('/job_listing')
def job_listing():
    try:
        conn=connection()
        arr=[]
        sql="SELECT * FROM JOBS"
        stmt = ibm_db.exec_immediate(conn, sql)
        dictionary = ibm_db.fetch_both(stmt)
        while dictionary != False:
             inst={}
             inst['JOBID']=dictionary['JOBID']
             inst['COMPANY']=dictionary['COMPANY']
             inst['ROLE']=dictionary['ROLE']
             inst['SALARY']=dictionary['SALARY']
             inst['LOCATION']=dictionary['LOCATION']
             inst['JOBTYPE']=dictionary['JOBTYPE']
             inst['POSTEDDATE']=dictionary['POSTEDDATE']
             inst['LOGO']=BytesIO(dictionary['LOGO'])
             arr.append(inst)
             dictionary = ibm_db.fetch_both(stmt)         
    except Exception as e:
        print(e)
    return render_template('job_listing.html',arr=arr)

#Register
@app.route("/register",methods=["GET","POST"])
def registerPage():
    if request.method=="POST":
        conn=connection()
        try:
            role=request.form["urole"]
            if role=="seeker":
                sql="INSERT INTO SEEKER VALUES('{}','{}','{}','{}','{}','{}')".format(request.form["uemail"],request.form["upass"],request.form["uname"],request.form["umobileno"],request.form["uworkstatus"],request.form["uorganisation"])
            else:
                sql="INSERT INTO RECRUITER VALUES('{}','{}','{}','{}','{}')".format(request.form["uemail"],request.form["upass"],request.form["uname"],request.form["umobileno"],request.form["uorganisation"])
            ibm_db.exec_immediate(conn,sql)
            return render_template('index.html')
        except Exception as error:
            print(error)
            return render_template('register.html')
    else:
        return render_template('register.html')

#Seeker Login
@app.route("/login_seeker",methods=["GET","POST"])
def loginPageSeeker():
    if request.method=="POST":
        conn=connection()
        useremail=request.form["lemail"]
        password=request.form["lpass"]
        sql="SELECT COUNT(*) FROM SEEKER WHERE EMAIL=? AND PASSWORD=?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,useremail)
        ibm_db.bind_param(stmt,2,password)
        ibm_db.execute(stmt)
        res=ibm_db.fetch_assoc(stmt)
        if res['1']==1:
            session['loggedin']= True
            session['user'] = useremail
            return redirect(url_for('job_listing'))
        else:
            print("Wrong Username or Password")
            return render_template('loginseeker.html')
    else:
        return render_template('loginseeker.html')

#Recruiter Login
@app.route("/login_recruiter",methods=["GET","POST"])
def loginPageRecruiter():
    if request.method=="POST":
        conn=connection()
        useremail=request.form["lemail"]
        password=request.form["lpass"]
        sql="SELECT COUNT(*) FROM RECRUITER WHERE EMAIL=? AND PASSWORD=?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,useremail)
        ibm_db.bind_param(stmt,2,password)
        ibm_db.execute(stmt)
        res=ibm_db.fetch_assoc(stmt)
        if res['1']==1:
            session['loggedin']= True
            session['user'] = useremail
            return render_template("recruitermenu.html")
        else:
            print("Wrong Username or Password")
            return render_template('loginrecruiter.html')
    else:
        return render_template('loginrecruiter.html')

#Display Job Description
@app.route("/JobDescription",methods=["GET","POST"])
def JobDescPage():
    if request.method=="POST":
        conn=connection()
        try:
            sql="SELECT * FROM JOBS WHERE JOBID={}".format(request.form['jobidname'])
            #sql="SELECT * FROM JOBS WHERE JOBID=101" #should be replaced with the jobid variable
            stmt = ibm_db.exec_immediate(conn,sql)
            dictionary = ibm_db.fetch_both(stmt)
            if dictionary != False:
                print ("COMPANY: ",  dictionary["COMPANY"])
                print ("ROLE: ",  dictionary["ROLE"])
                print ("SALARY: ",  dictionary["SALARY"])
                print ("LOCATION: ",  dictionary["LOCATION"])
                print ("JOBDESCRIPTION: ",  dictionary["JOBDESCRIPTION"])
                print ("POSTEDDATE: ",  dictionary["POSTEDDATE"])
                print ("APPLICATIONDEADLINE: ",  dictionary["APPLICATIONDEADLINE"])
                print ("JOBID: ",  dictionary["JOBID"])
                print ("JOBTYPE: ",  dictionary["JOBTYPE"])
                print ("EXPERIENCE: ",  dictionary["EXPERIENCE"])
                print ("KEYSKILLS: ",  dictionary["KEYSKILLS"])
                print ("BENEFITSANDPERKS: ",  dictionary["BENEFITSANDPERKS"])
                print ("EDUCATION: ",  dictionary["EDUCATION"])
                print ("NOOFVACANCIES: ",  dictionary["NUMBEROFVACANCIES"])
                print ("DOMAIN: ",  dictionary["DOMAIN"])
                print ("RECRUITERMAIL: ",  dictionary["RECRUITERMAIL"])
                fields=['JOBID','COMPANY','RECRUITER MAIL','ROLE','DOMAIN','JOB TYPE','JOB DESCRIPTION','EDUCATION','KEY SKILLS','EXPERIENCE','LOCATION','SALARY','BENEFITS AND PERKS','APPLICATION DEADLINE','LOGO','NUMBER OF VACANCIES','POSTED DATE']
                today = date.today()
                if today > dictionary['APPLICATIONDEADLINE'] or dictionary["NUMBEROFVACANCIES"]<=0:
                    disable=True
                else:
                    disable=False
                return render_template('JobDescription.html',data=dictionary,fields=fields,disable=disable)
            else:
                print("INVALID JOB ID")
                return render_template('sample.html')
        except:
            print("SQL QUERY NOT EXECUTED")
            return render_template('sample.html')
    else:
        return render_template('sample.html')

#Apply Jobs
@app.route("/JobApplicationForm",methods=["GET","POST"])
def loadApplForm():
    if request.method=="POST":
        jobid=request.form["Applbutton"]
        print(jobid)
        return render_template('JobApplication.html',jobid=jobid)
    else:
        return render_template("sample.html")

#Apply Job Status Page
@app.route("/JobApplicationSubmit",methods=["GET","POST"])
def jobApplSubmit():
    if request.method=="POST":
        try:
            uploaded_file = request.files['uresume']
            if uploaded_file.filename != '':
                contents=uploaded_file.read()
                print(contents)
                try:
                    conn=connection()
                    sql="INSERT INTO APPLICATIONS (JOBID,FIRSTNAME,LASTNAME,EMAILID,PHONENO,DOB,GENDER,PLACEOFBIRTH,CITIZENSHIP,PALINE1,PALINE2,PAZIPCODE,PACITY,PASTATE,PACOUNTRY,CURLINE1,CURLINE2,CURZIPCODE,CURCITY,CURSTATE,CURCOUNTRY,XBOARD,XPERCENT,XYOP,XIIBOARD,XIIPERCENT,XIIYOP,GRADPERCENT,GRADYOP,MASTERSPERCENT,MASTERSYOP,WORKEXPERIENCE,RESUME) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                    stmt = ibm_db.prepare(conn, sql)
                    ibm_db.bind_param(stmt, 1, request.form["jobidname"])
                    ibm_db.bind_param(stmt, 2, request.form["ufname"])
                    ibm_db.bind_param(stmt, 3, request.form["ulname"])
                    ibm_db.bind_param(stmt, 4, request.form["uemail"])
                    ibm_db.bind_param(stmt, 5, request.form["uphone"])
                    ibm_db.bind_param(stmt, 6, request.form["udob"])
                    ibm_db.bind_param(stmt, 7, request.form["ugender"])
                    ibm_db.bind_param(stmt, 8, request.form["upob"])
                    ibm_db.bind_param(stmt, 9, request.form["uciti"])
                    ibm_db.bind_param(stmt, 10, request.form["pAL1"])
                    ibm_db.bind_param(stmt, 11, request.form["pAL2"])
                    ibm_db.bind_param(stmt, 12, request.form["pzip"])
                    ibm_db.bind_param(stmt, 13, request.form["pcity"])
                    ibm_db.bind_param(stmt, 14, request.form["pstate"])
                    ibm_db.bind_param(stmt, 15, request.form["pcntry"])
                    ibm_db.bind_param(stmt, 16, request.form["curAL1"])
                    ibm_db.bind_param(stmt, 17, request.form["curAL2"])
                    ibm_db.bind_param(stmt, 18, request.form["curzip"])
                    ibm_db.bind_param(stmt, 19, request.form["curcity"])
                    ibm_db.bind_param(stmt, 20, request.form["curstate"])
                    ibm_db.bind_param(stmt, 21, request.form["curcntry"])
                    ibm_db.bind_param(stmt, 22, request.form["Xboard"])
                    ibm_db.bind_param(stmt, 23, request.form["XPercent"])
                    ibm_db.bind_param(stmt, 24, request.form["XYOP"])
                    ibm_db.bind_param(stmt, 25, request.form["XIIboard"])
                    ibm_db.bind_param(stmt, 26, request.form["XIIPercent"])
                    ibm_db.bind_param(stmt, 27, request.form["XIIYOP"])
                    ibm_db.bind_param(stmt, 28, request.form["GradPercent"])
                    ibm_db.bind_param(stmt, 29, request.form["GradYOP"])
                    ibm_db.bind_param(stmt, 30, request.form["MastersPercent"])
                    ibm_db.bind_param(stmt, 31, request.form["MastersYOP"])
                    ibm_db.bind_param(stmt, 32, request.form["work"])
                    ibm_db.bind_param(stmt, 33, contents)
                    ibm_db.execute(stmt)
                    uemail=request.form["uemail"]
                    
                    #REDUCE THE NO OF VACANCIES BY 1
                    sql2="UPDATE JOBS SET NUMBEROFVACANCIES = NUMBEROFVACANCIES-1 WHERE JOBID='{}'".format(request.form["jobidname"])
                    stmt = ibm_db.exec_immediate(conn,sql2)
                    return render_template("JobApplicationSuccess.html",uemail=uemail)
                except:
                    print("SQL QUERY FAILED")
                    traceback.print_exc()
                    return render_template('sample.html')
        except:
            print("FILE UPLOAD FAILED")
            return render_template("sample.html")
    else:
        return render_template("sample.html")

#Download Resume
@app.route("/ResumeDownload",methods=["GET","POST"])
def downloadResume():
    if request.method=="POST":
        try:
            conn=connection()
            sql="SELECT * FROM APPLICATIONS WHERE EMAILID='{}'".format(request.form["uemail"])
            stmt = ibm_db.exec_immediate(conn,sql)
            dictionary = ibm_db.fetch_both(stmt)
            return send_file(BytesIO(dictionary["RESUME"]),download_name="resume.pdf", as_attachment=True)
        except:
            print("SELECT QUERY FAILED")
            traceback.print_exc()
            return render_template('sample.html')
    else:
        return render_template("sample.html")

#Recruiter Menu
@app.route('/recruitermenu', methods =["GET","POST"])
def recruitermenu():
    return render_template('recruitermenu.html')

#Post Job       
@app.route('/postjob', methods =["GET","POST"])
def postjob():
    try:
        if request.method=="POST":
            conn=connection()
            
            sql1="SELECT ORGANISATION FROM RECRUITER WHERE EMAIL=?"
            stmt = ibm_db.prepare(conn, sql1)
            ibm_db.bind_param(stmt, 1, session['user'])
            ibm_db.execute(stmt)
            company = ibm_db.fetch_assoc(stmt)
            
            sql = "INSERT INTO JOBS(COMPANY, RECRUITERMAIL, ROLE, DOMAIN, JOBTYPE, JOBDESCRIPTION, EDUCATION, KEYSKILLS, \
                EXPERIENCE, LOCATION, SALARY, BENEFITSANDPERKS, APPLICATIONDEADLINE, LOGO, NUMBEROFVACANCIES, POSTEDDATE) \
                    values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            stmt = ibm_db.prepare(conn, sql)
            
            ibm_db.bind_param(stmt, 1, list(company.values())[0])
            ibm_db.bind_param(stmt, 2, session['user'])
            ibm_db.bind_param(stmt, 3, request.form["role"])
            ibm_db.bind_param(stmt, 4, request.form["domain"])
            ibm_db.bind_param(stmt, 5, request.form["jobtype"])
            ibm_db.bind_param(stmt, 6, request.form["jobdes"])
            ibm_db.bind_param(stmt, 7, request.form["education"])
            ibm_db.bind_param(stmt, 8, request.form["skills"])
            ibm_db.bind_param(stmt, 9, request.form["experience"])
            ibm_db.bind_param(stmt, 10, request.form["location"])
            ibm_db.bind_param(stmt, 11, request.form["salary"])
            ibm_db.bind_param(stmt, 12, request.form["benefits"])
            ibm_db.bind_param(stmt, 13, request.form["deadline"])
            ibm_db.bind_param(stmt, 14, request.files["logo"].read())
            ibm_db.bind_param(stmt, 15, (int)(request.form["vacancies"]))
            ibm_db.bind_param(stmt, 16, date.today())
            ibm_db.execute(stmt)

            flash("Job Successfully Posted!")
            return render_template('recruitermenu.html')
        else:
            return render_template('postjob.html')
    except:
        traceback.print_exc()

if __name__=='__main__':
    app.config['SECRET_KEY']='super secret key'
    app.config['SESSION_TYPE']='filesystem'
    app.run(debug=True)
