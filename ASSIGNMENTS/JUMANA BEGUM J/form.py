from flask import Flask, request, render_template
 
app = Flask(__name__) 
 

@app.route('/display', methods =["POST"])
def successpage():

   form_details = []
   form_details.append(request.form["fname"])
   form_details.append(request.form["lname"])
   form_details.append(request.form["dob"])
   form_details.append(request.form["gender"])
   form_details.append(request.form["address"])
   form_details.append(request.form["course"])
   form_details.append(request.form["email"])
   form_details.append(request.form["password"])
   
   return render_template('display.html', form_details=form_details)

@app.route('/form')
def studentform():
    return render_template('form.html')
 
if __name__=='__main__':
   app.run(debug = True)