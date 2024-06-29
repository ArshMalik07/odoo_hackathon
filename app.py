from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = 'odoo_2024'

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
    health_goals TEXT,
    dietary_preferences TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS diet_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    plan_date DATE,
    meals TEXT,
    calories INT,
    protein DECIMAL(5, 2),
    fat DECIMAL(5, 2),
    carbs DECIMAL(5, 2),
    vitamins TEXT,
    minerals TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS foods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    calories INT,
    protein DECIMAL(5, 2),
    fat DECIMAL(5, 2),
    carbs DECIMAL(5, 2),
    vitamins TEXT,
    minerals TEXT
)''')

# Home page route
@app.route('/')
def home():
    return render_template('home.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        
        cursor.execute('''SELECT * FROM users WHERE username = %s''', (username,))
        user = cursor.fetchone()
        
        if user:
            # Verify password using bcrypt
            if bcrypt.checkpw(password, user[2].encode('utf-8')):
                session['username'] = username
                session['role'] = user[3]  # Assuming role is in the fourth column
                flash('Login successful!', 'success')
                return redirect(url_for('user_profile'))
            else:
                error_msg = 'Invalid username or password.'
                app.logger.info('Password mismatch for user: %s', username)
                flash(error_msg, 'error')
        else:
            error_msg = 'User not found.'
            app.logger.info('User not found: %s', username)
            flash(error_msg, 'error')
    
    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())

        # Check if username already exists
        cursor.execute('''SELECT * FROM users WHERE username = %s''', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return render_template('register.html', error='Username already exists. Please choose a different one.')

        # Insert new user into database
        cursor.execute('''INSERT INTO users (username, password) 
                          VALUES (%s, %s)''', 
                          (username, password))
        db.commit()

        session['username'] = username
        session['role'] = 'user'  # Assign default role upon registration
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/foods', methods=['GET', 'POST'])
def manage_foods():
    if request.method == 'POST':
        name = request.form['name']
        calories = request.form['calories']
        protein = request.form['protein']
        fat = request.form['fat']
        carbs = request.form['carbs']
        vitamins = request.form['vitamins']
        minerals = request.form['minerals']
        
        cursor.execute('''INSERT INTO foods (name, calories, protein, fat, carbs, vitamins, minerals)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                       (name, calories, protein, fat, carbs, vitamins, minerals))
        db.commit()
        flash('Food added successfully!', 'success')
        return redirect(url_for('manage_foods'))

    cursor.execute('''SELECT * FROM foods''')
    foods = cursor.fetchall()
    return render_template('foods.html', foods=foods)

@app.route('/foods/search', methods=['GET', 'POST'])
def search_foods():
    if request.method == 'POST':
        search_query = request.form['search_query']
        cursor.execute('''SELECT * FROM foods WHERE name LIKE %s''', ('%' + search_query + '%',))
        foods = cursor.fetchall()
        return render_template('foods.html', foods=foods)

    return redirect(url_for('manage_foods'))

@app.route('/foods/add', methods=['GET', 'POST'])
def add_food():
    if request.method == 'POST':
        name = request.form['name']
        calories = request.form['calories']
        protein = request.form['protein']
        fat = request.form['fat']
        carbs = request.form['carbs']
        vitamins = request.form['vitamins']
        minerals = request.form['minerals']
        
        cursor.execute('''INSERT INTO foods (name, calories, protein, fat, carbs, vitamins, minerals)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                       (name, calories, protein, fat, carbs, vitamins, minerals))
        db.commit()
        flash('Food added successfully!', 'success')
        return redirect(url_for('manage_foods'))

    return render_template('add_food.html')

# User profile route
@app.route('/profile')
def user_profile():
    if 'username' in session:
        username = session['username']
        cursor.execute('''SELECT * FROM users WHERE username = %s''', (username,))
        user = cursor.fetchone()
        return render_template('profile.html', user=user)
    else:
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('login'))
    
@app.route('/profile/update', methods=['GET', 'POST'])
def update_profile():
    if 'username' in session:
        username = session['username']
        if request.method == 'POST':
            age = request.form.get('age')
            gender = request.form.get('gender')
            weight = request.form.get('weight')
            height = request.form.get('height')
            preferences = request.form.get('preferences')
            allergies = request.form.get('allergies')
            health_goals = request.form.get('health_goals')
            dietary_preferences = request.form.get('dietary_preferences')

            # Update user data in the database
            cursor.execute('''UPDATE users SET age=%s, gender=%s, weight=%s, height=%s, 
                              preferences=%s, allergies=%s, health_goals=%s, dietary_preferences=%s
                              WHERE username=%s''',
                           (age, gender, weight, height, preferences, allergies, health_goals,
                            dietary_preferences, username))
            db.commit()

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user_profile'))

        # Fetch current user data for the form
        cursor.execute('''SELECT * FROM users WHERE username = %s''', (username,))
        user = cursor.fetchone()
        return render_template('update_profile.html', user=user)
    else:
        flash('Please log in to update your profile.', 'error')
        return redirect(url_for('login'))

# Diet plan management routes
@app.route('/meal-plans')
def meal_plans():
    if 'username' in session:
        username = session['username']
        cursor.execute('''SELECT * FROM users WHERE username = %s''', (username,))
        user = cursor.fetchone()

        # Example function to generate meal plans (replace with your logic)
        meal_plan_daily = generate_meal_plan(user, 'daily')
        meal_plan_weekly = generate_meal_plan(user, 'weekly')
        meal_plan_monthly = generate_meal_plan(user, 'monthly')
        meal_plan_yearly = generate_meal_plan(user, 'yearly')

        return render_template('meal_plans.html', user=user, 
                               meal_plan_daily=meal_plan_daily, 
                               meal_plan_weekly=meal_plan_weekly,
                               meal_plan_monthly=meal_plan_monthly,
                               meal_plan_yearly=meal_plan_yearly)
    else:
        flash('Please log in to view your meal plans.', 'error')
        return redirect(url_for('login'))

def generate_meal_plan(user, period):
    # Replace with your logic to generate meal plans based on user profile and preferences
    # Example: Fetch meals from database based on dietary preferences and nutritional goals
    # Example: Calculate nutritional values (calories, protein, fat, carbs, vitamins, minerals)
    # Example: Return meal plan as a dictionary or object
    if period == 'daily':
        meal_plan = {
            'meals': [
                {'name': 'Breakfast', 'calories': 400, 'protein': 20, 'fat': 15, 'carbs': 50},
                {'name': 'Lunch', 'calories': 600, 'protein': 30, 'fat': 20, 'carbs': 70},
                {'name': 'Dinner', 'calories': 500, 'protein': 25, 'fat': 18, 'carbs': 60}
            ],
            'total': {'calories': 1500, 'protein': 75, 'fat': 53, 'carbs': 180}
        }
    elif period == 'weekly':
        # Logic to generate weekly meal plan
        meal_plan = {
            'meals': [
                {'name': 'Breakfast', 'calories': 400 * 7, 'protein': 20 * 7, 'fat': 15 * 7, 'carbs': 50 * 7},
                {'name': 'Lunch', 'calories': 600 * 7, 'protein': 30 * 7, 'fat': 20 * 7, 'carbs': 70 * 7},
                {'name': 'Dinner', 'calories': 500 * 7, 'protein': 25 * 7, 'fat': 18 * 7, 'carbs': 60 * 7}
            ],
            'total': {'calories': 1500 * 7, 'protein': 75 * 7, 'fat': 53 * 7, 'carbs': 180 * 7}
        }

    elif period == 'monthly':
        # Logic to generate monthly meal plan
        meal_plan = {
            'meals': [
            {'name': 'Breakfast', 'calories': 400 * 30, 'protein': 20 * 30, 'fat': 15 * 30, 'carbs': 50 * 30},
            {'name': 'Lunch', 'calories': 600 * 30, 'protein': 30 * 30, 'fat': 20 * 30, 'carbs': 70 * 30},
            {'name': 'Dinner', 'calories': 500 * 30, 'protein': 25 * 30, 'fat': 18 * 30, 'carbs': 60 * 30}
            ],
        'total': {'calories': 1500 * 30, 'protein': 75 * 30, 'fat': 53 * 30, 'carbs': 180 * 30}
        }
        
    elif period == 'yearly':
        # Logic to generate yearly meal plan
        meal_plan = {
            'meals': [
            {'name': 'Breakfast', 'calories': 400 * 365, 'protein': 20 * 365, 'fat': 15 * 365, 'carbs': 50 * 365},
            {'name': 'Lunch', 'calories': 600 * 365, 'protein': 30 * 365, 'fat': 20 * 365, 'carbs': 70 * 365},
            {'name': 'Dinner', 'calories': 500 * 365, 'protein': 25 * 365, 'fat': 18 * 365, 'carbs': 60 * 365}
            ],
        'total': {'calories': 1500 * 365, 'protein': 75 * 365, 'fat': 53 * 365, 'carbs': 180 * 365}
        }
    
    return meal_plan

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
