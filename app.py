import os, json, time
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lightbulb_json_2026'

# Path handling for Render Persistent Disk
STORAGE_DIR = '/data' if os.environ.get('RENDER') else 'data'
if not os.path.exists(STORAGE_DIR): os.makedirs(STORAGE_DIR)
if not os.path.exists('static/uploads'): os.makedirs('static/uploads')

# Helper functions to read/write JSON
def load_data(file):
    path = os.path.join(STORAGE_DIR, f'{file}.json')
    if not os.path.exists(path): return []
    with open(path, 'r') as f: return json.load(f)

def save_data(file, data):
    path = os.path.join(STORAGE_DIR, f'{file}.json')
    with open(path, 'w') as f: json.dump(data, f, indent=4)

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('auth'))
    return render_template('dashboard.html', 
                           user=session['user'], 
                           assignments=load_data('assignments'),
                           submissions=load_data('submissions'))

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        users = load_data('users')
        fn, li, pw = request.form.get('fn'), request.form.get('li'), request.form.get('pw')
        
        # Signup
        if request.form.get('email'):
            user = {
                "fn": fn, "li": li, "age": request.form.get('age'),
                "email": request.form.get('email'),
                "pw": generate_password_hash(pw),
                "is_teacher": False # Manually change to True in JSON for yourself
            }
            users.append(user)
            save_data('users', users)
            session['user'] = user
            return redirect(url_for('index'))
            
        # Login
        user = next((u for u in users if u['fn'] == fn and u['li'] == li), None)
        if user and check_password_hash(user['pw'], pw):
            session['user'] = user
            return redirect(url_for('index'))
    return render_template('auth.html')

@app.route('/assign', methods=['POST'])
def assign():
    tasks = load_data('assignments')
    task = {
        "id": int(time.time()),
        "title": request.form['title'],
        "type": request.form['type'],
        "min_s": request.form.get('min_s', 0),
        "file": ""
    }
    if 'file' in request.files:
        f = request.files['file']
        if f.filename:
            name = secure_filename(f.filename)
            f.save(os.path.join('static/uploads', name))
            task['file'] = name
    tasks.append(task)
    save_data('assignments', tasks)
    return redirect(url_for('index'))

@app.route('/submit/<int:task_id>', methods=['POST'])
def submit(task_id):
    subs = load_data('submissions')
    sub = {
        "task_id": task_id,
        "student": session['user']['fn'],
        "content": request.form.get('essay_text', ""),
        "replay": request.form.get('replay_json', ""),
        "grade": -1
    }
    if 'worksheet_file' in request.files:
        f = request.files['worksheet_file']
        if f.filename:
            name = f"sub_{int(time.time())}_{secure_filename(f.filename)}"
            f.save(os.path.join('static/uploads', name))
            sub['content'] = name
    subs.append(sub)
    save_data('submissions', subs)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)