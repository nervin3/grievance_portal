from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configure Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '@gmail.com'      # Your Gmail
app.config['MAIL_PASSWORD'] = 'xxxxxxxxxxxxxxxx'           # App password (not your Gmail password)
app.config['MAIL_DEFAULT_SENDER'] = '@gmail.com'

mail = Mail(app)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.secret_key = 'your_secret_key_here'

# User model for database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create tables
with app.app_context():
    db.create_all()

# Departments list
departments = ['IT', 'HR', 'Finance', 'Maintenance']

SECRET_REGISTRATION_CODE = "grv123"  # Your secret code here

@app.route('/')
def index():
    # Show login page if not logged in, else redirect to submit grievance
    if 'username' in session:
        return redirect(url_for('submit_grievance'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        secret_code = request.form.get('secret_code', '').strip()

        if not username or not password or not confirm_password or not secret_code:
            return render_template('register.html', error="Please fill all fields")
        if secret_code != SECRET_REGISTRATION_CODE:
            return render_template('register.html', error="Invalid secret code")
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Username already taken")
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password']

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = user.username
        return redirect(url_for('submit_grievance'))
    else:
        return render_template('index.html', error='Invalid username or password')

@app.route('/submit', methods=['GET', 'POST'])
def submit_grievance():
    if 'username' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title')
        issue = request.form.get('issue')
        department = request.form.get('department')
        severity = request.form.get('severity')

        try:
            msg = Message(subject=f"New Grievance Submitted: {title}",
                          recipients=['@gmail.com'])  # Replace with actual admin email
            msg.body = f"""
New grievance submitted:

Title: {title}
Issue: {issue}
Department: {department}
Severity: {severity}
Submitted by: {session['username']}
"""
            mail.send(msg)
            print("Email sent successfully.")
        except Exception as e:
            print(f"Email failed to send: {e}")
            return f"<h3>Email failed to send: {e}</h3><a href='/submit'>Go back</a>"

        return render_template('thank_you.html', title=title, issue=issue,
                               department=department, severity=severity)

    return render_template('submit.html', departments=departments)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
