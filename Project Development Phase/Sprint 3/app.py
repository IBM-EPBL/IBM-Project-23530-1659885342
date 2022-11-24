import ibm_db, traceback, os, spacy, pandas as pd
from flask import Flask, url_for, render_template, request, session, redirect, flash, send_file
from authlib.integrations.flask_client import OAuth
from datetime import date
from io import BytesIO
from flask_mail import Mail, Message
from spacy.matcher import Matcher
import connect, skillsrecommendation, jobrecommendation, linkedin, fakejobdetection
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import text
import joblib   

# load pre-trained model
nlp = spacy.load('en_core_web_sm')

# initialize matcher with a vocab
matcher = Matcher(nlp.vocab)
jobs_info_df = pd.DataFrame()

app = Flask(__name__)
mail = Mail(app) # instantiate the mail class

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'sjrjobhunt@gmail.com'
app.config['MAIL_PASSWORD'] = 'raashgiyqmiwleey'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'sjrjobhunt@gmail.com'
mail = Mail(app)

oauth = OAuth(app)
arr2=[]

#LinkedIn Wait Page
@app.route("/linkedinwait")
def linkedin_wait():
    return render_template('linkedinwait.html')

#LinkedIn - Sign Up
@app.route('/linkedin')
def linkedin_register():
    try:
        access_token=linkedin.start()
        li_name, li_mail=linkedin.get_user_info(access_token)
        ln=li_name['localizedLastName']
        fn=li_name['localizedFirstName']
        name=fn+' '+ln
        email=li_mail['elements'][0]['handle~']['emailAddress']
        print(name)
        print(email)
        conn=connect.connection()
        sql="INSERT INTO LINKEDINUSERS(NAME,EMAIL) VALUES(?,?)"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt, 1, name)
        ibm_db.bind_param(stmt, 2, email)
        out=ibm_db.execute(stmt)
        print(out)
    except:
        traceback.print_exc()
    return redirect(url_for('home'))

@app.route('/linkedinsignin/<string:sr>',methods=['GET','POST'])
def linkedin_login(sr):
    try:
        global webhook_return
        access_token=linkedin.start()
        li_name, li_mail=linkedin.get_user_info(access_token)
        ln=li_name['localizedLastName']
        fn=li_name['localizedFirstName']
        name=fn+' '+ln
        email=li_mail['elements'][0]['handle~']['emailAddress']
        print(name)
        print(email)
        conn=connect.connection()
        sql="SELECT COUNT(*) FROM LINKEDINUSERS WHERE EMAIL=?"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt, 1,email)
        ibm_db.execute(stmt)
        out=ibm_db.fetch_assoc(stmt)
        print('hello')
        if out['1']==0: #Not Registered
            return redirect(url_for('registerPage'))
        else: #Registered
            #Session Variables
            session['user']=email
            session['loggedin']= True
            if sr=='seeker': #Seeker
                conn=connect.connection()
                sql="SELECT COUNT(*) FROM SEEKER WHERE EMAIL=?"
                stmt = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(stmt, 1,email)
                ibm_db.execute(stmt)
                out=ibm_db.fetch_assoc(stmt)
                print('a seeker')
                if out['1']==0: #First Time Login
                     conn=connect.connection()
                     var='-'
                     sql="INSERT INTO SEEKER VALUES(?,?,?,?,?,?,?)"
                     stmt = ibm_db.prepare(conn,sql)
                     ibm_db.bind_param(stmt, 1,email)
                     ibm_db.bind_param(stmt, 2,var)
                     ibm_db.bind_param(stmt, 3,name)
                     ibm_db.bind_param(stmt, 4,var)
                     ibm_db.bind_param(stmt, 5,var)
                     ibm_db.bind_param(stmt, 6,var)
                     ibm_db.bind_param(stmt, 7,var)
                     out=ibm_db.execute(stmt)
                     print('inside seeker first time login')
                     return redirect(url_for('complete_profile'))
                else: # Not a First Time Login
                    print('already a seeker')
                    job_recs=jobrecommendation.start(email)
                    s1 = os.linesep.join(job_recs)
                    s2 = 'Best Suited Jobs for your Profile: \n' 
                    webhook_return = {
                        "recommended_jobs": s2+s1
                    }
                    return redirect(url_for('job_listing'))
            else: #Recruiter
                conn=connect.connection()
                sql="SELECT COUNT(*) FROM RECRUITER WHERE EMAIL=?"
                stmt = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(stmt, 1,email)
                ibm_db.execute(stmt)
                out=ibm_db.fetch_assoc(stmt)
                print('a recruiter')
                if out['1']==0: #First Time Login
                    conn=connect.connection()
                    var='-'
                    sql="INSERT INTO RECRUITER VALUES(?,?,?,?,?)"
                    stmt = ibm_db.prepare(conn,sql)
                    ibm_db.bind_param(stmt, 1,email)
                    ibm_db.bind_param(stmt, 2,var)
                    ibm_db.bind_param(stmt, 3,name)
                    ibm_db.bind_param(stmt, 4,var)
                    ibm_db.bind_param(stmt, 5,var)
                    out=ibm_db.execute(stmt)
                else: #Not First Time Login
                    print('already a recruiter')
                return redirect(url_for('recruitermenu'))          
    except Exception as e:
        print(e)
    return render_template('index.html')

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
        session['user']=user['email']
        conn=connect.connection()
        sql="INSERT INTO USERS(NAME,EMAIL) VALUES(?,?)"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt, 1, user['name'])
        ibm_db.bind_param(stmt, 2,user['email'])
        out=ibm_db.execute(stmt)
        print(out)
    except Exception as e:
        print(e)
    return redirect(url_for('home'))

@app.route('/googlesignin/<string:sr>', methods=['GET','POST'])
def googlesignin(sr):
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
    redirect_uri = url_for('google_authsignin',sr=sr, _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/google/authsignin/<string:sr>')
def google_authsignin(sr):
    global webhook_return
    token = oauth.google.authorize_access_token()
    user = oauth.google.parse_id_token(token,None)
    print(" Google User ", user)
    try:
        session['user']=user['email']
        conn=connect.connection()
        sql="SELECT COUNT(*) FROM USERS WHERE EMAIL=?"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt, 1,user['email'])
        ibm_db.execute(stmt)
        out=ibm_db.fetch_assoc(stmt)
        print('hello')
        if out['1']==0:
            return redirect(url_for('registerPage'))
        else:
            if sr=='seeker':
                conn=connect.connection()
                sql="SELECT COUNT(*) FROM SEEKER WHERE EMAIL=?"
                stmt = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(stmt, 1,user['email'])
                ibm_db.execute(stmt)
                out=ibm_db.fetch_assoc(stmt)
                print('a seeker')
                if out['1']==0:
                     conn=connect.connection()
                     var='-'
                     sql="INSERT INTO SEEKER VALUES(?,?,?,?,?,?,?)"
                     stmt = ibm_db.prepare(conn,sql)
                     ibm_db.bind_param(stmt, 1,user['email'])
                     ibm_db.bind_param(stmt, 2,var)
                     ibm_db.bind_param(stmt, 3,user['name'])
                     ibm_db.bind_param(stmt, 4,var)
                     ibm_db.bind_param(stmt, 5,var)
                     ibm_db.bind_param(stmt, 6,var)
                     ibm_db.bind_param(stmt, 7,var)
                     out=ibm_db.execute(stmt)
                     print('inside seeker first time login')
                     return redirect(url_for('complete_profile'))
                else:
                    print('already a seeker')
                    seekermail=session['user']
                    job_recs=jobrecommendation.start(seekermail)
                    s1 = os.linesep.join(job_recs)
                    s2 = 'Best Suited Jobs for your Profile: \n' 
                    webhook_return = {
                        "recommended_jobs": s2+s1
                    }
                    return redirect(url_for('job_listing'))
            else:
                        conn=connect.connection()
                        sql="SELECT COUNT(*) FROM RECRUITER WHERE EMAIL=?"
                        stmt = ibm_db.prepare(conn,sql)
                        ibm_db.bind_param(stmt, 1,user['email'])
                        ibm_db.execute(stmt)
                        out=ibm_db.fetch_assoc(stmt)
                        print('a recruiter')
                        if out['1']==0:
                             conn=connect.connection()
                             var='-'
                             sql="INSERT INTO RECRUITER VALUES(?,?,?,?,?)"
                             stmt = ibm_db.prepare(conn,sql)
                             ibm_db.bind_param(stmt, 1,user['email'])
                             ibm_db.bind_param(stmt, 2,var)
                             ibm_db.bind_param(stmt, 3,user['name'])
                             ibm_db.bind_param(stmt, 4,var)
                             ibm_db.bind_param(stmt, 5,var)
                             out=ibm_db.execute(stmt)
                             return redirect(url_for('recruitermenu'))
                        else:
                            print('already a recruiter')
                            return redirect(url_for('recruitermenu'))
             
    except Exception as e:
        print(e)
    return redirect(url_for('home'))

@app.route("/complete_profile")
def complete_profile():
    return render_template('CompleteProfile.html')

@app.route("/addresume", methods=['POST'])
def addresume():
    global webhook_return
    if request.method=="POST":
        conn=connect.connection()
        uploaded_file = request.files['seekerresume']
        if uploaded_file.filename != '':
            contents=uploaded_file.read()
            sql2="UPDATE SEEKER SET SEEKERRESUME = ? WHERE EMAIL=?"
            stmt = ibm_db.prepare(conn,sql2)
            ibm_db.bind_param(stmt, 1, contents)
            ibm_db.bind_param(stmt,2,session['user'])
            ibm_db.execute(stmt)
            seekermail=session['user']
            job_recs=jobrecommendation.start(seekermail)
            s1 = os.linesep.join(job_recs)
            s2 = 'Best Suited Jobs for your Profile: \n' 
            webhook_return = {
                "recommended_jobs": s2+s1
            }
            return redirect(url_for('job_listing'))
        else:
            return redirect(url_for('complete_profile'))

    return redirect(url_for('complete_profile'))

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

            bookmarkedjobsarr=[]
            try:
                conn=connect.connection()
                sql="SELECT * FROM SEEKER WHERE EMAIL='{}'".format(session['user']) # shd be session['user']
                stmt = ibm_db.exec_immediate(conn,sql)
                dictionary = ibm_db.fetch_both(stmt)
                text=jobrecommendation.extract_text_from_pdf(BytesIO(dictionary['SEEKERRESUME']))
                skills = jobrecommendation.extract_skills(text)
                jobs_info_df['resumeskills']=pd.Series(skills)
                sql ="SELECT * FROM JOBS WHERE (LOCATION = ? AND JOBTYPE = ?) AND ROLE = ? "
                stmt = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(stmt, 1, data['loc'])
                ibm_db.bind_param(stmt,2,data['type'])
                ibm_db.bind_param(stmt,3,data['role'])
                out=ibm_db.execute(stmt)
                while ibm_db.fetch_row(stmt) != False:
                     inst={}
                     inst['JOBID']=ibm_db.result(stmt,0)
                     inst['COMPANY']=ibm_db.result(stmt,1)
                     inst['ROLE']=ibm_db.result(stmt,3)
                     inst['SALARY']=ibm_db.result(stmt,11)
                     inst['LOCATION']=ibm_db.result(stmt,10)
                     inst['JOBTYPE']=ibm_db.result(stmt,5)
                     inst['POSTEDDATE']=ibm_db.result(stmt,16)
                     inst['KEYSKILLS']=ibm_db.result(stmt,8)
                     similarity=cal_similarity(inst)
                     inst['SIMILARITY']=round(similarity*100)
                     arr2.append(inst)

                sql2="SELECT * FROM BOOKMARKS WHERE EMAILID='{}'".format(session['user'])
                stmt2 = ibm_db.exec_immediate(conn,sql2)
                dictionary = ibm_db.fetch_both(stmt2)
                while dictionary != False:
                    bookmarkedjobsarr.append(dictionary['JOBID'])
                    dictionary = ibm_db.fetch_both(stmt2)
                print("IN FILTERED JOBS")
                print(bookmarkedjobsarr)
           
            except Exception as e:
                print(e)
           
    return render_template('job_listing.html',arr=arr2,bja=bookmarkedjobsarr)

@app.route('/filter')
def filter():
    global arr2
    filtered_jobs=[]
    for x in range(0,len(arr2)):
        filtered_jobs.append(arr2[x])
    arr2=[]
    session['filter']='true'
    bookmarkedjobsarr=[]
    try:
        conn=connect.connection()
        sql2="SELECT * FROM BOOKMARKS WHERE EMAILID='{}'".format(session['user'])
        stmt2 = ibm_db.exec_immediate(conn,sql2)
        dictionary = ibm_db.fetch_both(stmt2)
        while dictionary != False:
            bookmarkedjobsarr.append(dictionary['JOBID'])
            dictionary = ibm_db.fetch_both(stmt2)
            print('IN FILTER:')
            print(bookmarkedjobsarr)    
            print(filtered_jobs)
    except:
        print("SQL QUERY FAILED")
        traceback.print_exc()
        return render_template('sample.html')
    return render_template('job_listing.html',arr=filtered_jobs,bja=bookmarkedjobsarr)

#Compute Similarity
def cal_similarity(job):
        similarity=jobrecommendation.get_jaccard_sim(set(jobs_info_df['resumeskills']), set(job['KEYSKILLS']))
        return similarity

#Job Listing - Seeker Home Page
@app.route('/job_listing')
def job_listing():
    bookmarkedjobsarr=[]
    try:
        session['filter']='false'
        arr=[]
        conn=connect.connection()
        sql="SELECT * FROM SEEKER WHERE EMAIL='{}'".format(session['user']) # shd be session['user']
        stmt = ibm_db.exec_immediate(conn,sql)
        dictionary = ibm_db.fetch_both(stmt)
        text=jobrecommendation.extract_text_from_pdf(BytesIO(dictionary['SEEKERRESUME']))
        skills = jobrecommendation.extract_skills(text)
        jobs_info_df['resumeskills']=pd.Series(skills)
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
             inst['KEYSKILLS']=dictionary['KEYSKILLS']
             similarity=cal_similarity(inst)
             inst['SIMILARITY']=round(similarity*100)
             arr.append(inst)
             dictionary = ibm_db.fetch_both(stmt)  

       
        sql2="SELECT * FROM BOOKMARKS WHERE EMAILID='{}'".format(session['user'])
        stmt2 = ibm_db.exec_immediate(conn,sql2)
        dictionary2 = ibm_db.fetch_both(stmt2)
        while dictionary2 != False:
            bookmarkedjobsarr.append(dictionary2['JOBID'])
            dictionary2 = ibm_db.fetch_both(stmt2)
        print(bookmarkedjobsarr)
       
    except Exception as e:
        print(e)
    return render_template('job_listing.html',arr=arr,bja=bookmarkedjobsarr)

#Register
@app.route("/register",methods=["GET","POST"])
def registerPage():
    if request.method=="POST":
        conn=connect.connection()
        try:
            role=request.form["urole"]
            if role=="seeker":
                uploaded_file = request.files['seekerresume']
                if uploaded_file.filename != '':
                    contents=uploaded_file.read()
                    print(contents)
                    #sql="INSERT INTO SEEKER VALUES('{}','{}','{}','{}','{}','{}','{}')".format(request.form["uemail"],request.form["upass"],request.form["uname"],request.form["umobileno"],request.form["uworkstatus"],request.form["uorganisation"],contents)
                    sql="INSERT INTO SEEKER (EMAIL,PASSWORD,NAME,MOBILENO,WORKSTATUS,ORGANISATION,SEEKERRESUME) VALUES(?,?,?,?,?,?,?)"
                    stmt = ibm_db.prepare(conn, sql)
                    ibm_db.bind_param(stmt, 1, request.form["uemail"])
                    ibm_db.bind_param(stmt, 2, request.form["upass"])
                    ibm_db.bind_param(stmt, 3, request.form["uname"])
                    ibm_db.bind_param(stmt, 4, request.form["umobileno"])
                    ibm_db.bind_param(stmt, 5, request.form["uworkstatus"])
                    ibm_db.bind_param(stmt, 6, request.form["uorganisation"])
                    ibm_db.bind_param(stmt, 7, contents)
                    ibm_db.execute(stmt)
                else:
                    print("Resume Not Uploaded")
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
    global seekermail
    global webhook_return
    if request.method=="POST":
        conn=connect.connection()
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
            
            seekermail=session['user']
           
            job_recs=jobrecommendation.start(seekermail)
            s1 = os.linesep.join(job_recs)
            s2 = 'Best Suited Jobs for your Profile: \n' 
            webhook_return = {
                "recommended_jobs": s2+s1
            }  
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
        conn=connect.connection()
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
        conn=connect.connection()
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
                    conn=connect.connection()
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
            conn=connect.connection()
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

#Job Alerts
@app.route('/job_alerts', methods =["GET","POST"])
def job_alerts():
    try:
        jobidstr=request.args.get('jobid')
        jobid=(int)(jobidstr)
        print(jobid)

        conn=connect.connection()
            
        sql1="SELECT EMAIL, SEEKERRESUME FROM SEEKER"
        stmt1 = ibm_db.prepare(conn, sql1)
        ibm_db.execute(stmt1)
        seeker_dictionary = ibm_db.fetch_both(stmt1)

        sql2="SELECT * FROM JOBS WHERE JOBID=?"
        stmt2=ibm_db.prepare(conn,sql2)
        ibm_db.bind_param(stmt2,1,jobid)
        ibm_db.execute(stmt2)
        job_dictionary = ibm_db.fetch_both(stmt2)

        seekermails=[]

        while seeker_dictionary != False:
            #Extract Seeker Resume Skills
            text=jobrecommendation.extract_text_from_pdf(BytesIO(seeker_dictionary['SEEKERRESUME']))
            skills = jobrecommendation.extract_skills(text)
            jobs_info_df['resumeskills']=pd.Series(skills)
            print(skills)
            
            #Job Skills
            inst={}
            inst['KEYSKILLS']=job_dictionary['KEYSKILLS']
            print(inst['KEYSKILLS'])
            
            #Compute Similarity
            similarity=cal_similarity(inst)
            print(similarity)
            
            if similarity > 0.02 :
                seekermails.append(seeker_dictionary["EMAIL"])
            seeker_dictionary = ibm_db.fetch_both(stmt1)
        print(seekermails)

        msg = Message(
				"Job Alert: "+(str)(job_dictionary[1])+' is hiring '+(str)(job_dictionary[3])+'!',
				recipients = seekermails
			)
        msg.body = 'Dear User,\n\n'+(str)(job_dictionary[1])+' is hiring '+(str)(job_dictionary[3])+'.\nLocation: '+(str)(job_dictionary[10])+'\nSalary: '+(str)(job_dictionary[11])+'\nCheck out the Job Requirements and Submit your applications on or before '+(str)(job_dictionary[13])+' though our app!\n\nBest Wishes,\nTeam Job Hunt\n'
        mail.send(msg)
        print("Job Alert Mail Sent Successfully")
    except:
        print("Job Alert Mail Failure\n")
        traceback.print_exc()
    
    flash("Job Successfully Posted!")
    return render_template('recruitermenu.html')

#Post Job       
@app.route('/postjob', methods =["GET","POST"])
def postjob():
    try:
        if request.method=="POST":
            conn=connect.connection()
            
            role = request.form["role"]
            jobdescription = request.form["jobdes"]
            keyskills = request.form["skills"]
            benefitsandperks = request.form["benefits"]

            my_stop_words = text.ENGLISH_STOP_WORDS
            des = role + " " + jobdescription + " " + keyskills + " " + benefitsandperks
            des = des.strip().lower()
            des = [des]

            tfidf2 = TfidfVectorizer(max_features = 20,stop_words=my_stop_words,analyzer='word',vocabulary=fakejobdetection.vocabulary)
            x = tfidf2.fit_transform(des)
            data = pd.DataFrame(x.toarray(),columns = tfidf2.get_feature_names())

            clfmodel = joblib.load('fakejobdetection.pkl')
            Y_pred = clfmodel.predict(data)

            if Y_pred==0 :
                print("NOT FAKE!!!")
                sql1="SELECT ORGANISATION FROM RECRUITER WHERE EMAIL=?"
                stmt = ibm_db.prepare(conn, sql1)
                ibm_db.bind_param(stmt, 1, session['user'])
                ibm_db.execute(stmt)
                company = ibm_db.fetch_assoc(stmt)
                
                sql = "SELECT JOBID FROM FINAL TABLE\
                    (INSERT INTO JOBS(COMPANY, RECRUITERMAIL, ROLE, DOMAIN, JOBTYPE, JOBDESCRIPTION, EDUCATION, KEYSKILLS, \
                    EXPERIENCE, LOCATION, SALARY, BENEFITSANDPERKS, APPLICATIONDEADLINE, LOGO, NUMBEROFVACANCIES, POSTEDDATE) \
                    values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?))"
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

                res = ibm_db.fetch_assoc(stmt)
                jobid = res['JOBID']
                
                return redirect(url_for('job_alerts', jobid=jobid)) 

            else:
                return render_template('postjob.html')
        else:
            return render_template('postjob.html')
    except:
        traceback.print_exc()

    
@app.route('/skillsRecommendation', methods =["GET","POST"])
def recommendedSkills():
    try:
        #usermail='sam123@gmail.com'
        conn=connect.connection()
        sql="SELECT * FROM SEEKER WHERE EMAIL='{}'".format(session['user']) # shd be session['user']
        stmt = ibm_db.exec_immediate(conn,sql)
        dictionary = ibm_db.fetch_both(stmt)

        text=skillsrecommendation.extract_text_from_pdf(BytesIO(dictionary["SEEKERRESUME"]))#shd be replaced with the resume url of the user session variable
        email=skillsrecommendation.extract_email(text)
        print('IN FLASK: email')
        print(email)
        #usermail='sam133@gmail.com'
        userskills = skillsrecommendation.extract_skills(text)
        print('IN FLASK: SKILLS:')
        print(userskills)
        rec_skills=set()

        sql="SELECT JOBS.KEYSKILLS FROM JOBS INNER JOIN APPLICATIONS ON JOBS.JOBID = APPLICATIONS.JOBID WHERE APPLICATIONS.EMAILID='{}'".format(session['user'])# shd be session['user']
        stmt=ibm_db.exec_immediate(conn,sql)
        requiredskills = ibm_db.fetch_tuple(stmt)
        while requiredskills != False:
            for x in requiredskills[0].split(','):
                rec_skills.add(x)
            requiredskills = ibm_db.fetch_tuple(stmt)
        for x in userskills:
            if x in rec_skills:
                rec_skills.remove(x)
        print ("The skills needed are : ", rec_skills)
        return render_template('skillsrecommended.html',skills=rec_skills)
    except:
        print("SQL QUERY FAILED")
        traceback.print_exc()
        return render_template('sample.html')

@app.route('/jobrecommendation', methods =["GET","POST"])
def recommendjobs():
        print("hello")
        return webhook_return

@app.route('/bookmarkedJobs', methods =["GET","POST"])
def bookmarkedJobs():
    try:
        arr=[]
        conn=connect.connection()
        sql="SELECT * FROM BOOKMARKS INNER JOIN JOBS ON JOBS.JOBID=BOOKMARKS.JOBID WHERE BOOKMARKS.EMAILID='{}'".format(session['user'])#shd be session['user']
        stmt = ibm_db.exec_immediate(conn,sql)
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
        return render_template('BookmarkedJobs.html',arr=arr)
    except:
        print("SQL QUERY FAILED")
        traceback.print_exc()
        return render_template('sample.html')

@app.route('/bookmarkJob', methods =["GET","POST"])
def bookmarkJob():
    try:
        bookmarkedjobsarr=[]
        conn=connect.connection()
        sql="INSERT INTO BOOKMARKS VALUES(?,?)"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, request.form["jobidname"])
        ibm_db.bind_param(stmt, 2, session['user'])
        ibm_db.execute(stmt)
        
        sql2="SELECT * FROM BOOKMARKS WHERE EMAILID='{}'".format(session['user'])
        stmt2 = ibm_db.exec_immediate(conn,sql2)
        dictionary = ibm_db.fetch_both(stmt2)
        while dictionary != False:
            bookmarkedjobsarr.append(dictionary['JOBID'])
            dictionary = ibm_db.fetch_both(stmt2)
        print(bookmarkedjobsarr)

        arr=[]
        sql3="SELECT * FROM JOBS"
        stmt3 = ibm_db.exec_immediate(conn, sql3)
        dictionary3 = ibm_db.fetch_both(stmt3)
        while dictionary3 != False:
            inst={}
            inst['JOBID']=dictionary3['JOBID']
            inst['COMPANY']=dictionary3['COMPANY']
            inst['ROLE']=dictionary3['ROLE']
            inst['SALARY']=dictionary3['SALARY']
            inst['LOCATION']=dictionary3['LOCATION']
            inst['JOBTYPE']=dictionary3['JOBTYPE']
            inst['POSTEDDATE']=dictionary3['POSTEDDATE']
            inst['LOGO']=BytesIO(dictionary3['LOGO'])
            arr.append(inst)
            dictionary3 = ibm_db.fetch_both(stmt3)      
        return render_template('job_listing.html',arr=arr,bja=bookmarkedjobsarr)
    except:
        print("SQL QUERY FAILED")
        traceback.print_exc()
        return render_template('sample.html')

@app.route('/removeBookmark',methods=['GET','POST'])
def removeBookmark():
    try:
        conn=connect.connection()
        print(request.form["jobidname"])
        sql="DELETE FROM BOOKMARKS WHERE EMAILID=? AND JOBID=?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session['user'])
        ibm_db.bind_param(stmt,2,request.form["jobidname"])
        ibm_db.execute(stmt)
        return redirect(url_for('bookmarkedJobs'))

    except:
        print("SQL QUERY FAILED")
        traceback.print_exc()
        return render_template('sample.html')

if __name__=='__main__':
    app.config['SECRET_KEY']='super secret key'
    app.config['SESSION_TYPE']='filesystem'
    app.run(debug=True)