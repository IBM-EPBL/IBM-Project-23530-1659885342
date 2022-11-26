import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import text
import joblib

def clean(text):
    return text.strip().lower()

data = pd.read_csv('data/fake_job_postings.csv')
data.fillna(' ', inplace=True)

data['text']=data['role']+' '+data['jobdescription']+' '+data['keyskills']+' '+data['benefitsandperks']
data.drop(data.iloc[:, 0:12], inplace=True, axis=1)
data['text'] = data['text'].apply(clean)

my_stop_words = text.ENGLISH_STOP_WORDS
tfidf = TfidfVectorizer(max_features = 17,stop_words=my_stop_words,analyzer='word')
x = tfidf.fit_transform(data['text'])

data2 = pd.DataFrame(x.toarray(),columns = tfidf.get_feature_names())
del data['text']
data = pd.concat([data2,data],axis = 1)

X = data.iloc[:, 0:-1]
Y = data.iloc[:, -1]
X_train, X_test, Y_train, Y_test = train_test_split(X,Y, test_size=0.3)

clf = RandomForestClassifier(n_jobs=3,oob_score = True,n_estimators = 100,criterion="entropy") 
clf.fit(X_train,Y_train)

joblib.dump(clf, 'fakejobdetection.pkl') 
clfmodel = joblib.load('fakejobdetection.pkl')
Y_pred = clfmodel.predict(X_test)

vocabulary = tfidf.vocabulary_