from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.utils import secure_filename
import sqlite3
import threading
import os

# Create a thread-local storage for the database connection
# This ensures that each thread has its own connection object
_db_connections = threading.local()

def get_db():
    # Get the connection for the current thread
    if not hasattr(_db_connections, 'connection'):
        _db_connections.connection = sqlite3.connect('database.db')
    return _db_connections.connection

#connect database
conn = sqlite3.connect('your_database_name.db')

#function to query databse
def query_db(username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username=?", (username,))
    result = cur.fetchone()
    cur.close()
    return result[0] if result else None
app = Flask(__name__, template_folder='templates')

app.secret_key = "secret_key"

# Set up file upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'

# Set up allowed file types
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

# Check if a file is an allowed file type
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Homepage
@app.route('/')
@login_required
def admin_index():
    return render_template('admin_index.html')

@app.route('/')
@login_required
def user_index():
    return render_template('user_index.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'otp' in request.form:
            # Handle OTP submission
            otp = request.form['otp']
            # Process OTP here
            stored_otp = query_db(otp)
            if stored_otp is not None and stored_otp == otp:
                return redirect(url_for('registeration'))
            else:
                flash('Invalid Otp')
        else:
            # Handle username and password submission
            username = request.form['username']
            password = request.form['password']
            stored_password = query_db(username)
            # Process username and password here
            if username == 'admin' and password == 'admin':
                session['username'] = username
                return redirect(url_for('admin_index')) 
            elif stored_password is not None and stored_password == password:
                session['username'] = username
                return redirect(url_for('user_index'))                
            else:
                flash('Invalid username or password')
    # Display login form
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Upload file
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File uploaded successfully')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type')
    return render_template('upload.html')

# Download file
@app.route('/download/<filename>')
@login_required
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Edit file
@app.route('/edit/<filename>', methods=['GET', 'POST'])
@login_required
def edit(filename):
    if request.method == 'POST':
        new_text = request.form['text']
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'w') as f:
            f.write(new_text)
            flash('File edited successfully')
            return redirect(url_for('index'))
    else:
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as f:
            text = f.read()
        return render_template('edit.html', filename=filename, text=text)

# Share file
@app.route('/share/<filename>', methods=['GET', 'POST'])
@login_required
def share(filename):
    if request.method == 'POST':
        recipient = request.form['recipient']
        # code to send the file to the recipient goes here
        flash('File shared successfully')
        return redirect(url_for('index'))
    else:
        return render_template('share.html', filename=filename)

# Delete file
@app.route('/delete/<filename>')
@login_required
def delete(filename):
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    flash('File deleted successfully')

# Recycle bin
@app.route('/recycle-bin')
@login_required
def recycle_bin():
    deleted_files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('.'):
            continue
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.isfile(file_path):
                continue
                deleted_files.append(filename)
    return render_template('recycle-bin.html', deleted_files=deleted_files)

# Empty recycle bin
@app.route('/empty-recycle-bin')
@login_required
def empty_recycle_bin():
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('.'):
            continue
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.isfile(file_path):
                continue
                os.remove(file_path)
                flash('Recycle bin emptied successfully')
    return redirect(url_for('recycle_bin'))

# User management
@app.route('/user-management')
@login_required
def user_management():
    # code to retrieve all users and their information goes here
    return render_template('user-management.html')

# Add user
@app.route('/add-user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        # code to create a new user with the given information goes here
        flash('User added successfully')
        return redirect(url_for('user_management'))
    else:
            return render_template('add-user.html')

# Generate user pin
@app.route('/generate-user-pin/<user_id>')
@login_required
def generate_user_pin(user_id):
    # code to generate a PIN for the specified user goes here
    flash('PIN generated successfully')
    return redirect(url_for('user_management'))

# Disable user
@app.route('/disable-user/<user_id>')
@login_required
def disable_user(user_id):
    # code to disable the specified user goes here
    flash('User disabled successfully')
    return redirect(url_for('user_management'))

# Delete user
@app.route('/delete-user/<user_id>')
@login_required
def delete_user(user_id):
    # code to delete the specified user goes here
    flash('User deleted successfully')
    return redirect(url_for('user_management'))

# System configuration
@app.route('/system-configuration', methods=['GET', 'POST'])
@login_required
def system_configuration():
    if request.method == 'POST':
        # code to update the system configuration goes here
        flash('System configuration updated successfully')
        return redirect(url_for('system_configuration'))
    else:
        # code to retrieve the current system configuration goes here
        return render_template('system-configuration.html')

# Back up system
@app.route('/backup-system')
@login_required
def backup_system():
    # code to back up the system goes here
    flash('System backed up successfully')
    return redirect(url_for('index'))

# Manage logs
@app.route('/manage-logs')
@login_required
def manage_logs():
    # code to retrieve and display the system logs goes here
    return render_template('manage-logs.html')

# Send document
@app.route('/send-document/<filename>')
@login_required
def send_document(filename):
    # code to send the document to a recipient goes here
    flash('Document sent successfully')
    return redirect(url_for('index'))

# Perform user functions
@app.route('/user-functions')
@login_required
def user_functions():
    # code to display user-specific functions goes here
    return render_template('user-functions.html')

    if name == 'main':
        app.run(debug=True)