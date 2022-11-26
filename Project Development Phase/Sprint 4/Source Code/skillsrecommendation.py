import spacy, re, csv
from spacy.matcher import Matcher
from pdfminer.high_level import extract_text
import traceback,ibm_db
from io import BytesIO
from flask import session
import connect
doc=[]
noun_chunks=[]

nlp = spacy.load('en_core_web_sm')

matcher = Matcher(nlp.vocab)

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

def read_resume():
    try:
        conn=connect.connection()
        sql="SELECT * FROM SEEKER WHERE EMAIL='{}'".format(session['user']) # shd be session['user']
        stmt = ibm_db.exec_immediate(conn,sql)
        dictionary = ibm_db.fetch_both(stmt)
        resume=extract_text_from_pdf(BytesIO(dictionary["SEEKERRESUME"]))
        global doc,noun_chunks
        doc=nlp(extract_text_from_pdf(resume))
        noun_chunks = doc.noun_chunks
    except:
        print("SQL QUERY FAILED")
        traceback.print_exc()

#doc=nlp(extract_text_from_pdf(resume))
#noun_chunks = doc.noun_chunks

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

if __name__ == '__main__':
    read_resume()
    try:
        conn=connect.connection()
        sql="SELECT * FROM SEEKER WHERE EMAIL='{}'".format(session['user']) # shd be session['user']
        stmt = ibm_db.exec_immediate(conn,sql)
        dictionary = ibm_db.fetch_both(stmt)
        text=extract_text_from_pdf(BytesIO(dictionary["SEEKERRESUME"]))
    except:
        print("SQL QUERY FAILED")
        traceback.print_exc()
        

    name=extract_name(text)
    print(name)
    email=extract_email(text)
    print(email)
    skills = extract_skills(text)
    print('SKILLS:')
    print(skills)