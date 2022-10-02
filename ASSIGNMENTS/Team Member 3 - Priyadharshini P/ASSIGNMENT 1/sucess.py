from flask import Flask, request, render_template
 
app = Flask(__name__,template_folder='C:/Users/user/source/repos/IBMAss') 
 

@app.route('/sucess', methods =["POST"])
def successpage():

   form_details = []
   form_details.append(request.form["name"])
   form_details.append(request.form["regno"])
   form_details.append(request.form["email"])
   form_details.append(request.form["pwd"])
   form_details.append(request.form["branch"])
   form_details.append(request.form["gen"])
   form_details.append(request.form["exp"])
   
   return render_template('sucess.html', form_details=form_details)

@app.route('/RegistrationForm')
def studentform():
    return render_template('RegistrationForm.html')

if __name__=='__main__':
   app.run(port=1000)
