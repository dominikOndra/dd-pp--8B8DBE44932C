import os
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(SECRET_KEY=os.urandom(24))
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

migrate = Migrate(app, db)


class User(UserMixin, db.Model):
    """Class used to authenticate user and sort tasks"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)

    # password is not hashed for simplicity
    password = db.Column(db.String(20), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    """Flask login module required by module"""
    return User.query.get(user_id)


class Todo(db.Model):
    """Class used to store and sort tasks"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(150))
    date_TBD = db.Column(db.DateTime)
    done = db.Column(db.Boolean, default=False)
    filename = db.Column(db.String(40))
    file_data = db.Column(db.LargeBinary)
    user_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.id


@app.route('/register', methods=['POST', 'GET'])
def register():
    """Register unique user"""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_info = User(username=username, password=password)
        db.session.add(user_info)
        db.session.commit()
        return redirect('/')

    return render_template('register.html')


@app.route("/logout", methods=['GET'])
def logout():
    """Logout user and go back to homepage"""

    logout_user()
    return redirect("/")


@app.route('/', methods=['POST', 'GET'])
def index():
    """Used for login and showing tasks"""

    if current_user.is_authenticated is False:
        if request.method == 'POST':

            username = request.form['username']
            password = request.form['password']
            user_in_db = db.session.query(User).filter_by(username=username) \
                .filter_by(password=password).first()

            if user_in_db is not None:
                login_user(user_in_db)
            else:
                return render_template('index.html', logged=False)

        else:
            return render_template('index.html', logged=False)




    else:
        if request.method == 'POST':
            task_title = request.form['title']
            task_content = request.form['content']

            date_tbd = datetime.strptime(request.form['date_TBD'], '%Y-%m-%dT%H:%M')

            file = request.files['file']
            task_rec = Todo(content=task_content, title=task_title,
                            filename=file.filename, file_data=file.read(),
                            user_id=current_user.get_id(), date_TBD=date_tbd)

            db.session.add(task_rec)
            db.session.commit()
            return redirect('/')

    tasks = Todo.query.filter_by(done=False).filter_by(user_id=current_user.get_id()).all()
    return render_template('index.html', tasks=tasks, logged=True, current_time=datetime.now())


@app.route('/detail/<int:task_id>', methods=['POST', 'GET'])
def detail(task_id):
    """Shows detail of task"""

    task = Todo.query.get(task_id)
    return render_template('detail.html', task=task)


@app.route('/delete/<int:task_id>', methods=['GET', 'POST'])
def delete(task_id):
    """Delete the task with passed id"""

    task_to_delete = Todo.query.get(task_id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect('/')


@app.route('/task_done/<int:task_id>', methods=['POST'])
def task_done(task_id):
    """Mark the task with passed id as done"""

    completed_task = Todo.query.get(task_id)
    completed_task.done = True
    db.session.commit()
    return redirect('/')


@app.route('/download_file/<int:task_id>', methods=['GET'])
def download(task_id):
    """Download file from currently selected task"""

    task = Todo.query.get(task_id)
    return send_file(BytesIO(task.file_data),
                     attachment_filename=task.filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
