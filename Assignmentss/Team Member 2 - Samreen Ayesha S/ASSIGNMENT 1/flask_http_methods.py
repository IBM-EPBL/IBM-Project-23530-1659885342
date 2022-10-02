from flask import Flask,request
app = Flask(__name__)

fruits = ['Apple','Banana','Orange','Mango','Strawberry']

@app.route('/')
def homepage():
    return "Hello"

@app.route('/get',methods=['GET'])
def getAllFruits():
    return fruits

@app.route('/insert/<string:name>',methods=['POST'])
def postFruits(name):
    if name in fruits:
        return name+" Already Present\n\nUpdated List:\n"+str(fruits)
    fruits.append(name)
    return name+" Added Successfully\n"+str(fruits)

@app.route('/update/<string:name>',methods=['PUT'])
def putFruits(name):
    for i,f in enumerate(fruits):
        if f==name:
            fruits[i]=request.args['fruit']
            return name+" Edited Successfully\n\nUpdated List:\n"+str(fruits)
    return name+" Not Found\n"+str(fruits)

@app.route('/delete/<string:name>',methods=['DELETE'])
def delFruits(name):
    if name in fruits:
            fruits.remove(name)
            return name+" Deleted Successfully\n\nUpdated List:\n"+str(fruits)
    return name+" Not Found\n"+str(fruits)

if __name__=='__main__':
    app.run(debug=True)