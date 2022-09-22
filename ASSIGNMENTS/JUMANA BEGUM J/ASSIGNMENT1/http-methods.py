from flask import Flask, request
 
app = Flask(__name__) 

languages = ['C','C++','Python','Java']

#GET METHOD
@app.route('/get', methods=['GET'])
def getAllLang():
    return languages

#POST METHOD
@app.route('/add/<string:name>', methods=['POST'])
def addLang(name):
    if name in languages:
        return name+" Already Present\n\nUpdated List:\n"+str(languages)
    languages.append(name)
    return name+" Added Successfully\n"+str(languages)

#PUT METHOD
@app.route('/edit/<string:name>', methods=['PUT'])
def editLang(name):
    for i, l in enumerate(languages):
        if l==name:
            languages[i]=request.args['C#']
            return name+" Edited Successfully\n\nUpdated List:\n"+str(languages)
    return name+" Not Found\n"+str(languages)

#DELETE METHOD
@app.route('/remove/<string:name>', methods=['DELETE'])
def removeLang(name):
    for l in languages:
        if l==name:
            languages.remove(l)
            return name+" Deleted Successfully\n\nUpdated List:\n"+str(languages)
    return name+" Not Found\n"+str(languages)

if __name__=='__main__':
   app.run()