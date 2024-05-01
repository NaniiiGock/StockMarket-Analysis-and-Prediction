from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
import bcrypt

app = Flask(__name__)
import os
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'login_table'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    pass_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Remove the db.create_all() call from here

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    # Hashing the password before storing it
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = User(username=username, email=email, pass_hash=hashed_password.decode('utf-8'))

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except exc.IntegrityError:
        return jsonify({"error": "This username or email already exists"}), 400

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.checkpw(password.encode('utf-8'), user.pass_hash.encode('utf-8')):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

# Add this block to create all database tables within the application context
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host="0.0.0.0")
