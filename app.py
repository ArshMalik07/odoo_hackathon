from flask import Flask, render_template, request, redirect, session,url_for
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="diet"
)
cursor = db.cursor()

# Create tables if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(100),
    role ENUM('user', 'admin') DEFAULT 'user',
    age INT,
    gender ENUM('male', 'female', 'other'),
    weight DECIMAL(5, 2),
    height DECIMAL(5, 2),
    preferences TEXT,
    allergies TEXT,
    health_goals TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS diet_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    date DATE,
    meals TEXT,
    calories INT,
    protein DECIMAL(5, 2),
    fat DECIMAL(5, 2),
    carbs DECIMAL(5, 2),
    FOREIGN KEY (user_id) REFERENCES users(id)
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS foods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    calories INT,
    protein DECIMAL(5, 2),
    fat DECIMAL(5, 2),
    carbs DECIMAL(5, 2),
    vitamins TEXT,
    minerals TEXT
)''')

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    else:
        return render_template('index.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password.decode('utf-8')))
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            session['user_id'] = user[0]
            session['role'] = user[3]
            return redirect(url_for('profile'))
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    age = request.form['age']
    weight = request.form['weight']
    height = request.form['height']
    preferences = request.form['preferences']
    allergies = request.form['allergies']
    health_goals = request.form['health_goals']
    cursor.execute("""
        UPDATE users
        SET age=%s, weight=%s, height=%s, preferences=%s, allergies=%s, health_goals=%s
        WHERE id=%s
    """, (age, weight, height, preferences, allergies, health_goals, user_id))
    db.commit()
    return redirect('/profile')

@app.route('/generate_diet_plan')
def generate_diet_plan():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    # Example plan (replace with actual algorithm or API integration)
    diet_plan = {
        'calories': 2000,
        'protein': 150,
        'fat': 70,
        'carbs': 250
    }
    cursor.execute("""
        INSERT INTO diet_plans (user_id, date, meals, calories, protein, fat, carbs)
        VALUES (%s, CURDATE(), %s, %s, %s, %s, %s)
    """, (user_id, 'Sample meals', diet_plan['calories'], diet_plan['protein'], diet_plan['fat'], diet_plan['carbs']))
    db.commit()
    return redirect('/profile')

@app.route('/search_foods', methods=['GET', 'POST'])
def search_foods():
    if request.method == 'POST':
        query = request.form['query']
        cursor.execute("SELECT * FROM foods WHERE name LIKE %s", (f'%{query}%',))
        foods = cursor.fetchall()
        return render_template('search_results.html', foods=foods)
    return render_template('search_foods.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
