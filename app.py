from flask import Flask, render_template, request, url_for, session, redirect, flash, make_response
from flask_mysqldb import MySQL
from datetime import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'khurana'
app.config['MYSQL_PASSWORD'] = 'ishika321'
app.config['MYSQL_DB'] = 'skincare_suggestion'

mysql = MySQL(app)


@app.route('/')
def main_page():
    return render_template('project_skincare.html')  

@app.route('/login_home')
def login_home():
    return render_template('login_home.html')  # main page


@app.route('/login', methods=['GET', 'POST'])
def login_submit():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT User_id, User_name, password, gender 
            FROM UserInfo 
            WHERE User_name = %s
        """, (username,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user[2], password):
            # login success
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['gender'] = user[3]
            flash("Login successful!", "success")
            return redirect(url_for('skin_info'))
        else:
            flash("Invalid username or password. Try again.", "error")

    return render_template('login.html')


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        age = request.form['age']
        gender = request.form['gender']
        password = request.form['password']

        cur = mysql.connection.cursor()


        username_pattern = r"^[a-zA-Z0-9_]{3,16}$"
        email_pattern = r"^(?!.*\.\.)(?!\.)[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[A-Za-z]{2,}$"
        phone_pattern = r"^(?!([0-9])\1{9})([6-9]\d{9})$"  
        password_pattern =r"^(?=.*[A-Z]).{8,}$"


        if not re.match(username_pattern, username):
            flash("Invalid username! (3–16 letters/numbers/underscores)", "danger")
            return render_template("signin.html", username=username, name=name, email=email, phone=phone, age=age, gender=gender)

        if not re.match(email_pattern, email):
            flash("Invalid email format!", "danger")
            return render_template("signin.html", username=username, name=name, email=email, phone=phone, age=age, gender=gender)

        if not re.match(phone_pattern, phone):
            flash("Invalid phone number! Must be 10 digits starting with 6–9.", "danger")
            return render_template("signin.html", username=username, name=name, email=email, phone=phone, age=age, gender=gender)

        if not re.match(password_pattern, password):
            flash("Weak password! Must be 8+ chars, include uppercase.", "danger")
            return render_template("signin.html", username=username, name=name, email=email, phone=phone, age=age, gender=gender)

        cur.execute("SELECT 1 FROM UserInfo WHERE Email = %s", (email,))
        if cur.fetchone():
            flash("This email is already registered. Please use another one.", "danger")
            return render_template("signin.html", username=username, name=name, email=email, phone=phone, age=age, gender=gender)

        cur.execute("SELECT 1 FROM UserInfo WHERE User_name = %s", (username,))
        if cur.fetchone():
            flash("This username is already taken. Please choose another.", "danger")
            return render_template("signin.html", username=username, name=name, email=email, phone=phone, age=age, gender=gender)

        cur.execute("SELECT 1 FROM UserInfo WHERE Phone_number = %s", (phone,))
        if cur.fetchone():
            flash("This phone number is already registered. Please use another.", "danger")
            return render_template("signin.html", username=username, name=name, email=email, phone=phone, age=age, gender=gender)

        # Insert into DB
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        cur.execute("""
            INSERT INTO UserInfo (User_name, name, Email, Phone_number, password, gender, age, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (username, name, email, phone, hashed_password, gender, age))
        mysql.connection.commit()
        cur.close()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("login_submit"))

    return render_template("signin.html")
    '''else:
                    flash("sign up first")
            '''


@app.route('/skin_info', methods=['GET'])
def skin_info():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))

    return render_template('skin_info.html', gender=session.get('gender'))


@app.route('/submit_skin_info', methods=['POST'])
def submit_skin_info():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))

    Skin_type = request.form.get('skin_type')
    Concern = request.form.get('concern')
    Goal = request.form.get('goal')
    Pregnant = request.form.get('pregnant')
    user_id = session['user_id']

    cursor = mysql.connection.cursor()

    # Check if user has previous quiz entries
    cursor.execute("""
        SELECT Total_num_of_Quiz_taken FROM User_Skin_Info
        WHERE User_id = %s
        ORDER BY ID DESC
        LIMIT 1
    """, (user_id,))
    last_entry = cursor.fetchone()

    if last_entry:
        total_quiz = last_entry[0] + 1
    else:
        total_quiz = 1

    # Insert new quiz entry with incremented counter
    cursor.execute("""
        INSERT INTO User_Skin_Info 
        (User_id, Skin_type, Concern, Goal, Pregnant, Last_updated_at, Total_num_of_Quiz_taken)
        VALUES (%s, %s, %s, %s, %s, NOW(), %s)
    """, (user_id, Skin_type, Concern, Goal, Pregnant, total_quiz))

    mysql.connection.commit()
    cursor.close()

    return redirect(url_for("show_suggestions"))

@app.route("/recommendations")
def recommendations():
    if "user_id" not in session:
        flash("Please login to see your recommendations.", "warning")
        return redirect(url_for("login_submit"))

    user_id = session["user_id"]
    cur = mysql.connection.cursor()

    # Get user's latest quiz result including skin goal
    cur.execute("""
        SELECT Skin_type, Concern, Goal
        FROM User_Skin_Info 
        WHERE User_id = %s 
        ORDER BY Last_updated_at DESC 
        LIMIT 1
    """, (user_id,))
    user_skin = cur.fetchone()

    if not user_skin:
        flash("Please complete the skin quiz first.", "warning")
        return redirect(url_for("quiz"))

    skin_type = user_skin[0]
    concern = user_skin[1]
    skin_goal = user_skin[2]  # fetch skin goal

    # Fetch products (tuple-based)
    cur.execute("""
        SELECT Brand_name, Product_name, Price, Discount, ingredients, benefits
        FROM product_info
        WHERE LOWER(skin_type) = %s AND LOWER(concern) = %s
        LIMIT 6
    """, (skin_type.lower(), concern.lower()))
    products = cur.fetchall()

    # Fetch diet (tuple-based) with skin goal
    cur.execute("""
        SELECT recommendations, to_avoid
        FROM diet_info
        WHERE LOWER(skin_type) = %s 
          AND LOWER(concern) = %s
          AND LOWER(skin_goal) = %s
    """, (skin_type.lower(), concern.lower(), skin_goal.lower()))
    diet = cur.fetchall()

    cur.close()

    # Debugging (optional)
    print("Skin Type:", skin_type)
    print("Concern:", concern)
    print("Skin Goal:", skin_goal)
    print("Products:", products)
    print("Diet:", diet)

    return render_template(
        "product.html",
        products=products,
        diet=diet,
        skin_type=skin_type,
        concern=concern,
        skin_goal=skin_goal
    )

@app.route("/show_suggestions")
def show_suggestions():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Get latest quiz for current user
    cur.execute("""
        SELECT Skin_type, Concern, Goal, Pregnant
        FROM User_Skin_Info
        WHERE User_id = %s
        ORDER BY ID DESC
        LIMIT 1
    """, (user_id,))
    user_row = cur.fetchone()

    if not user_row:
        return render_template("show_suggestions.html",
                               skin_type=None, concern=None, goal=None, pregnant=None,
                               recommended_ingredients=[], avoid_ingredients=[])

    skin_type, concern, goal, pregnant = user_row

    # Get recommendations from SkinInfo
    cur.execute("""
    SELECT recommendation, to_avoid
    FROM SkinInfo
    WHERE LOWER(skin_type) = LOWER(%s)
      AND LOWER(concern) = LOWER(%s)
      AND LOWER(skin_goal) = LOWER(%s)
    LIMIT 1
""", (skin_type, concern, goal))

    rec_row = cur.fetchone()
    cur.close()

    if rec_row:
        recommendation, to_avoid = rec_row
        recommended_ingredients = [r.strip() for r in recommendation.split(",")]
        avoid_ingredients = [a.strip() for a in to_avoid.split(",")]
    else:
        recommended_ingredients, avoid_ingredients = [], []

    return render_template("suggestions.html",
                           skin_type=skin_type,
                           concern=concern,
                           goal=goal,
                           pregnant=pregnant,
                           recommended_ingredients=recommended_ingredients,
                           avoid_ingredients=avoid_ingredients)


@app.route("/search_hub", methods=["GET", "POST"])
def search_hub():
    results = []
    not_found = False
    
    if request.method == "POST":
        search_query = request.form["ingredient"]
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT ingredient_name, benefits, skin_type, avoid_for
            FROM Skin_Ingredient_Info
            WHERE ingredient_name LIKE %s
        """, ("%" + search_query + "%",))
        results = cur.fetchall()
        cur.close()
        
        if not results:
            not_found = True
    
    return render_template("search_hub.html", results=results, not_found=not_found)

@app.route('/about_us', methods=['GET'])
def about_us():
    return render_template('about_us.html')

@app.route('/about_us_logout', methods=['GET'])
def about_us_logout():
    return render_template('about_us1.html')


@app.route('/current_recommendations', methods=['GET'])
def current_recommendation():
    cur = mysql.connection.cursor()

    # Current logged-in user
    current_user_id = session.get('user_id')

    # Get gender from UserInfo
    cur.execute("SELECT gender FROM UserInfo WHERE User_id = %s", (current_user_id,))
    gender_row = cur.fetchone()
    gender = gender_row[0] if gender_row else None

    # Get last quiz entry
    cur.execute("""
        SELECT Skin_type, Concern, Goal, Pregnant
        FROM User_Skin_Info
        WHERE user_id = %s
        ORDER BY ID DESC
        LIMIT 1
    """, (current_user_id,))
    
    last_entry = cur.fetchone()

    if last_entry:
        skin_type, concern, goal, pregnant = last_entry

        # Get recommendations from SkinInfo
        cur.execute("""
            SELECT recommendation, to_avoid
            FROM SkinInfo
            WHERE LOWER(skin_type) = LOWER(%s)
              AND LOWER(concern) = LOWER(%s)
            LIMIT 1
        """, (skin_type, concern))
        
        rec = cur.fetchone()
        cur.close()

        if rec:
            recommended_ingredients = rec[0].split(", ")
            avoid_ingredients = rec[1].split(", ")
        else:
            recommended_ingredients = []
            avoid_ingredients = []

        return render_template(
            'suggestions.html',
            skin_type=skin_type,
            concern=concern,
            goal=goal,
            pregnant=pregnant,
            gender=gender,
            recommended_ingredients=recommended_ingredients,
            avoid_ingredients=avoid_ingredients
        )
    else:
        cur.close()
        return render_template(
            'suggestions.html',
            skin_type=None,
            concern=None,
            goal=None,
            pregnant=None,
            gender=gender,
            recommended_ingredients=[],
            avoid_ingredients=[]
        )


@app.route('/description', methods=['GET'])
def description():
    return render_template('description.html')




@app.route('/profile_page', methods=['GET'])
def profile_page():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Get user info from UserInfo table
    cur.execute("""
        SELECT User_name, name, Email, Phone_number, age, gender
        FROM UserInfo
        WHERE User_id = %s
    """, (user_id,))
    user_info = cur.fetchone()

    # Get user's latest skin info from User_Skin_Info
    cur.execute("""
        SELECT Skin_type, Concern, Goal, Pregnant
        FROM User_Skin_Info
        WHERE User_id = %s
        ORDER BY Last_updated_at DESC
        LIMIT 1
    """, (user_id,))
    skin_info = cur.fetchone()

    cur.close()

    return render_template('profile_page.html',
                           username=user_info[0] if user_info else "",
                           full_name=user_info[1] if user_info else "",
                           email=user_info[2] if user_info else "",
                           phone=user_info[3] if user_info else "",
                           age=user_info[4] if user_info else "",
                           gender=user_info[5] if user_info else "",
                           skin_type=skin_info[0] if skin_info else "",
                           concern=skin_info[1] if skin_info else "",
                           goal=skin_info[2] if skin_info else "",
                           pregnant=skin_info[3] if skin_info else "")

@app.route('/info_page', methods=['GET'])
def info_page():
    return render_template('info.html')


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        username = request.form['username']
        name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        age = request.form['age']
        gender = request.form['gender']

        # --- Regex patterns (same as signin) ---
        username_pattern = r"^[a-zA-Z0-9_]{3,16}$"
        email_pattern = r"^(?!.*\.\.)(?!\.)[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[A-Za-z]{2,}$"
        phone_pattern = r"^[6-9]\d{9}$"   # Indian 10-digit phone
        age_pattern = r"^(1[3-9]|[2-9][0-9]|1[01][0-9]|120)$"  # optional: 13–120 valid ages

        # --- Validation checks ---
        if not re.match(username_pattern, username):
            flash("Invalid username! (3–16 letters/numbers/underscores)", "danger")
            return redirect(url_for("edit_profile"))

        if not re.match(email_pattern, email):
            flash("Invalid email format!", "danger")
            return redirect(url_for("edit_profile"))

        if not re.match(phone_pattern, phone):
            flash("Invalid phone number! Must be 10 digits starting with 6–9.", "danger")
            return redirect(url_for("edit_profile"))

        if age and not re.match(age_pattern, age):
            flash("Invalid age! Must be between 13 and 120.", "danger")
            return redirect(url_for("edit_profile"))

        cur.execute("""
            UPDATE UserInfo
            SET User_name=%s, name=%s, Email=%s, Phone_number=%s, age=%s, gender=%s
            WHERE User_id=%s
        """, (username, name, email, phone, age, gender, user_id))
        mysql.connection.commit()
        cur.close()

        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile_page'))

    cur.execute("SELECT User_name, name, Email, Phone_number, age, gender FROM UserInfo WHERE User_id=%s", (user_id,))
    user_info = cur.fetchone()
    cur.close()

    return render_template('edit_profile.html',
                           username=user_info[0],
                           full_name=user_info[1],
                           email=user_info[2],
                           phone=user_info[3],
                           age=user_info[4],
                           gender=user_info[5])

@app.route('/ingredients', methods=['GET', 'POST'])
def ingredients():
    result = None
    not_found = False

    if request.method == 'POST':
        search_term = request.form['search'].strip()

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT Ingredient_name, Description, Benefits, Skin_type, Avoid_for
            FROM Skin_Ingredient_Info
            WHERE Ingredient_name LIKE %s
        """, ("%" + search_term + "%",))
        result = cur.fetchone()
        cur.close()

        if not result:
            not_found = True

    return render_template('ingredients.html', result=result, not_found=not_found)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


# @app.route('/logout')
# def logout():
#     session.clear()
#     flash("You have been logged out.", "info")
#     response = make_response(redirect(url_for('login_submit')))
#     response.headers['Cache-Control'] = 'no-cache, no_store, must_revalidate'
#     response.headers['Pragma'] = 'no-cache'
#     response.headers['Expires'] = '0'
#     return response
#     #return redirect(url_for('login_submit'))

@app.route('/logout')
def logout():
    # Remove only login-related session keys
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('gender', None)

    flash("You have been logged out.", "info")

    # Redirect to login with headers to prevent caching
    response = make_response(redirect(url_for('login_submit')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == "__main__":
    app.run(debug=True)
