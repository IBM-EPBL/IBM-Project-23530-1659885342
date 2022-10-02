from flask import Flask,render_template,request
app = Flask(__name__)

@app.route("/success",methods=["GET","POST"])
def dataDisplay():
    if request.method == "POST":
        formdata=[]
        formdata.append(request.form["uname"])
        formdata.append(request.form["uemail"])
        formdata.append(request.form["upass"])
        formdata.append(request.form["ugender"])
        formdata.append(request.form["uaddress"])
        formdata.append(request.form["ucountry"])
    return render_template('DataDisplay.html',formdata=formdata)

if __name__=='__main__':
    app.run(debug=True)

