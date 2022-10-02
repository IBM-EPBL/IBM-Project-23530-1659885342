from flask import Flask,jsonify
app=Flask(__name__)

courses = [{"name": "C++","description":"C++ is an object oriented programming language","course_id":"0"},
           {"name": "Python","description":"Python is an object oriented programming language","course_id":"1"},
           {"name":"C","description":"C is a procedural programming language","course_id":"2"}]

@app.route('/')
def index():
    return "Welcome to IBM Course"

@app.route("/courses",methods=['GET'])
def get():
    return jsonify({'Courses':courses})

@app.route("/courses/<int:course_id>",methods=['GET'])
def get_course(course_id):
    return jsonify({'Course': courses[course_id]})

@app.route("/courses",methods=['POST'])
def create():
    course={"name":"Java","description":"Java is an object oriented programming language","course_id":"3"}
    courses.append(course)
    return jsonify({"Created": course})

@app.route("/courses/<int:course_id>",methods=['PUT'])
def course_update(course_id):
    courses[course_id]["description"]="Java is an object-oriented programming language"
    return jsonify({'course':courses[course_id]})

@app.route("/courses/<int:course_id>",methods=['DELETE'])
def course_delete(course_id):
    courses.remove(courses[course_id])
    return jsonify({'result':True})

if __name__=='__main__':
    app.run(port=1000)
