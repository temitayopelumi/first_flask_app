from flask import Flask, render_template,flash,redirect,url_for, session, logging,request
from flask_bootstrap import Bootstrap
from data import Articles
#from flaskext.mysql import MySQL
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
#from wtforms import StringField
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
#bootstrap=Bootstrap(app)
app=Flask(__name__)
from functools import wraps 


#config MySQL
app.config["MYSQL_HOST"]='localhost'
app.config["MYSQL_USER"]='root'
app.config["MYSQL_PASSWORD"]=''
app.config["MYSQL_DB"]='MyFlaskApp'
app.config["MYSQL_CURSORCLASS"]='DictCursor'

mysql=MySQL(app)

#Articles=Articles()

@app.route('/')
def index():
   return render_template('home.html')

@app.route('/about')
def about():
   return render_template('about.html')

@app.route('/articles')
def articles():
   cur = mysql.connection.cursor()

   result =cur.execute("SELECT * FROM articles")

   articles = cur.fetchall()
   if result >0:
      return render_template('articles.html', articles=articles )
   else:
      msg ='No Articles Found'
      return render_template('articles.html', msg=msg)
   cur.close() 
   

@app.route('/article/<string:id>/')
def article(id):
   cur = mysql.connection.cursor()

   result =cur.execute("SELECT * FROM articles where id =%5",[id])

   articles = cur.fetchone() 
   return render_template('articles.html', article=article)

#registeration
class RegisterForm(Form):
   name= StringField('Name', [validators.length(min=1, max=50)])
   username = StringField('Username', [validators.Length(min=1, max=25)])
   email = StringField('Email',[validators.Length(min=6,max=50)])
   password=PasswordField('Password',[validators.DataRequired(),
   validators.EqualTo('confirm', message='Passwords do not match')])
   confirm=PasswordField('confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
   form = RegisterForm(request.form)
   if request.method == 'POST' and form.validate():
      name=form.name.data
      email=form.email.data
      username=form.username.data
      password=sha256_crypt.hash(str(form.password.data))
      # create cursor
      cur= mysql.connection.cursor()
      cur.execute("INSERT INTO users(name,email, username,password) VALUES(%s, %s, %s, %s)", (name, email,username, password))
        
      mysql.connection.commit()
      
      cur.close()
      flash('thank you', 'success')
      return redirect(url_for('index'))
      
   return render_template('register.html', form=form)

#login
@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
      #get form fields
      username= request.form['username']
      password_candidate = request.form['password']
      #create cursor
      cur =mysql.connection.cursor()
      #get user by username
      result = cur.execute('SELECT  * FROM users WHERE username = %s',[username])

      if result>0: 
         # get stored hash
         data=cur.fetchone()

         password = data['password']

         if sha256_crypt.verify(password_candidate, password):
             session['logged_in']=True
             session['username']=username 
             flash('You are now logged in', 'success')
             return redirect(url_for('dashboard'))
         else:
            error ='Invalid login'
            return render_template('login.html', error=error)
         cur.close()
      else:
         error ='Username not found'
         return render_template('login.html', error=error)
   return render_template('login.html')

 # check if user logged in
def is_logged_in(f):
   @wraps(f)
   def wrap(*args, **kwargs):
      if 'logged_in' in session: 
         return f(*args, **kwargs)
      else:
         flash('Unauthorized, Please login','danger')
         return redirect(url_for('login'))
   return wrap 

#logout
@app.route('/logout')
@is_logged_in
def logout():
   session.clear()
   flash('You are now logged out','success')
   return redirect(url_for('login'))

#dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
   cur = mysql.connection.cursor()

   result =cur.execute("SELECT * FROM articles")

   articles = cur.fetchall()
   if result >0:
      return render_template('dashboard.html', articles=articles )
   else:
      msg ='No Articles Found'
      return render_template('dashboard.html', msg=msg)
   cur.close() 
class ArticleForm(Form):
   title= StringField('Title', [validators.length(min=1, max=200)])
   body = TextAreaField('Body', [validators.Length(min=30)])

@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
   form=ArticleForm(request.form)
   if request.method == 'POST' and form.validate():
      title = form.title.data
      body  = form.body.data

      #create Cursor
      cur = mysql.connection.cursor()

      #Execute
      cur.execute('INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)',(title, body, session['username']))

      #commit to DB
      mysql.connection.commit()

      #close
      cur.close()
      flash('Article Created','success')
      return redirect(url_for('dashboard'))
   return render_template('add_article.html', form=form)

   
if __name__ == '__main__':
   app.secret_key='secret123'
   app.run(debug=True)