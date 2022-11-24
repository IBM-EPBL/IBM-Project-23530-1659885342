import spacy, re, csv, ibm_db, pandas as pd
from spacy.matcher import Matcher
from nltk.corpus import stopwords
from pdfminer.high_level import extract_text
from io import BytesIO
import traceback
from flask import render_template,session
import connect
doc=[]
noun_chunks=[]

nlp = spacy.load('en_core_web_sm')

matcher = Matcher(nlp.vocab)
jobs_info_df = pd.DataFrame()

def extract_name(resume_text):
    nlp_text = nlp(resume_text)
    
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
    
    matcher.add('NAME',[pattern],on_match=None)
    
    matches = matcher(nlp_text)
    
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        return span.text

def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

def extract_email(email):
    email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", email)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None

def read_resume(seekermail):
    try:
        conn=connect.connection()
        sql="SELECT * FROM SEEKER WHERE EMAIL='{}'".format(seekermail) # shd be session['user']
        stmt = ibm_db.exec_immediate(conn,sql)
        dictionary = ibm_db.fetch_both(stmt)
        resume=extract_text_from_pdf(BytesIO(dictionary["SEEKERRESUME"]))
        global doc,noun_chunks
        doc=nlp(resume)
        noun_chunks = doc.noun_chunks
    except:
        print("SQL QUERY FAILED")
        traceback.print_exc()

def extract_education(resume_text):
    STOPWORDS = set(stopwords.words('english'))

    EDUCATION = [
            'BE','B.E.', 'B.E', 'BS', 'B.S', 
            'ME', 'M.E', 'M.E.', 'MS', 'M.S', 
            'BTECH', 'B.TECH', 'M.TECH', 'MTECH', 
            'SSC', 'HSC', 'CBSE', 'ICSE', 'X', 'XII'
        ]
    nlp_text = nlp(resume_text)

    nlp_text = [sent.text.strip() for sent in nlp_text.sents]

    edu = {}
    for index, text in enumerate(nlp_text):
        for tex in text.split():
            tex = re.sub(r'[?|$|.|!|,]', r'', tex)
            if tex.upper() in EDUCATION and tex not in STOPWORDS:
                edu[tex] = text + nlp_text[index + 1]

    education = []
    for key in edu.keys():
        year = re.search(re.compile(r'(((20|19)(\d{2})))'), edu[key])
        if year:
            education.append((key, ''.join(year[0])))
        else:
            education.append(key)
    return education

def extract_skills(resume_text):
    nlp_text = nlp(resume_text)

    tokens = [token.text for token in nlp_text if not token.is_stop]

    with open('data/skills_dataset.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter = ',')
        list_of_column_names = []
        for row in csv_reader:
            list_of_column_names.append(row)
            break
    skills = list(list_of_column_names[0])
    
    skillset = []
    
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)
    
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)
    
    return [i.capitalize() for i in set([i.lower() for i in skillset])]

def get_jaccard_sim(x_set, y_set):         
        intersection = x_set.intersection(y_set)
        return float(len(intersection)) / (len(x_set) + len(y_set) - len(intersection))

def cal_similarity():    
        num_jobs_return = 3
        similarity = []
 
        jobs_info_df['jobs_keywords'].fillna(method='ffill', inplace=True)
        for job_skills in jobs_info_df['jobs_keywords']:
            similarity.append(get_jaccard_sim(set(jobs_info_df['resumeskills']), set(job_skills[8])))
        jobs_info_df['similarity'] = similarity
        top_match = jobs_info_df.sort_values(by='similarity', ascending=False).head(num_jobs_return)        
        top_match.index=[0,1,2]
        print("Top Matches\n")
        print(top_match)
        return top_match

def extract_jobskills():
    try:
        conn=connect.connection()
        sql="SELECT * FROM JOBS"
        stmt = ibm_db.exec_immediate(conn, sql)
        dictionary = ibm_db.fetch_both(stmt)
        
        arr=[]
        while dictionary != False:
            
                jobid=dictionary['JOBID']
                print(jobid)
                company=dictionary['COMPANY']
                recruitermail=dictionary['RECRUITERMAIL']
                print(recruitermail)
                role=dictionary['ROLE']
                print(role)
                domain=dictionary['DOMAIN']
                print(domain)
                jobtype=dictionary['JOBTYPE']
                print(jobtype)
                jobdescription=dictionary['JOBDESCRIPTION']
                print(jobdescription)
                education=dictionary['EDUCATION']
                print(education)
                keyskills=dictionary['KEYSKILLS']
                print(keyskills)
                experience=dictionary['EXPERIENCE']
                print(experience)
                location=dictionary['LOCATION']
                print(location)
                salary=dictionary['SALARY']
                print(salary)
                benefitsandperks=dictionary['BENEFITSANDPERKS']
                print(benefitsandperks)
                applicationdeadline=dictionary['APPLICATIONDEADLINE']
                print(applicationdeadline)
                logo=dictionary['LOGO']
                numberofvacancies=dictionary['NUMBEROFVACANCIES']
                print(numberofvacancies)
                posteddate=dictionary['POSTEDDATE']
                print(posteddate)
                inst=[]
                inst.append(jobid)
                inst.append(company)
                inst.append(recruitermail)
                inst.append(role)
                inst.append(domain)
                inst.append(jobtype)
                inst.append(jobdescription)
                inst.append(education)
                inst.append(keyskills)
                inst.append(experience)
                inst.append(location)
                inst.append(salary)
                inst.append(benefitsandperks)
                inst.append(applicationdeadline)
                inst.append(numberofvacancies)
                inst.append(posteddate)
                arr.append(inst)
                dictionary = ibm_db.fetch_both(stmt)
        return arr
    except Exception as e:
        print(e)

def start(seekermail):
    read_resume(seekermail)
    try:
        conn=connect.connection()
        sql="SELECT * FROM SEEKER WHERE EMAIL='{}'".format(seekermail) # shd be session['user']
        stmt = ibm_db.exec_immediate(conn,sql)
        print("hii")
        dictionary = ibm_db.fetch_both(stmt)
        text=extract_text_from_pdf(BytesIO(dictionary["SEEKERRESUME"]))
    except:
        print("SQL QUERY FAILED")
        traceback.print_exc()
        return render_template('sample.html')

    skills = extract_skills(text)
    print(skills)
    jobs_info_df['resumeskills']=pd.Series(skills)
    jobs=extract_jobskills()
    jobs_info_df['jobs_keywords']=pd.Series(jobs)

    recommendation=cal_similarity()
    rj=[]
    for i in range(0,3):
        rj.append(recommendation.jobs_keywords[i][3])
    recommended_jobs=set(rj)
    print('RECOMMENDED JOBS:\n'+(str)(recommended_jobs))
    return recommended_jobs