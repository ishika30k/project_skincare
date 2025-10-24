from flask import Flask, render_template, request, url_for, session, redirect, flash, make_response,request_finished,request_started
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
import re
from werkzeug.security import generate_password_hash, check_password_hash
import json
import uuid
from blinker import Namespace


app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'khurana'
app.config['MYSQL_PASSWORD'] = 'ishika321'
app.config['MYSQL_DB'] = 'skincare_suggestion'

mysql = MySQL(app)

signals=Namespace()

user_logged_in = signals.signal('user-logged-in')

def after_user_logged_in(sender, user_id, **extra):
    cur = mysql.connection.cursor()
    # Get latest user-specific skin info
    cur.execute("""
        SELECT MAX(Last_updated_at)
        FROM User_Skin_Info
        WHERE User_id = %s
    """, (user_id,))
    last_update = cur.fetchone()[0]
    cur.close()

    last_seen = session.get('last_seen_skin_update')
    if not last_seen or str(last_seen) != str(last_update):
        session['show_skin_update_popup'] = True
        session['last_seen_skin_update'] = str(last_update)
    else:
        session['show_skin_update_popup'] = False

user_logged_in.connect(after_user_logged_in)

@app.route('/')
def main_page():
    return render_template('project_skincare.html')  

def create_user_session(user_id, device_id=None):
    cur = mysql.connection.cursor()
    token = str(uuid.uuid4())
    expiry_time = datetime.now() + timedelta(hours=1)

    # Invalidate old sessions (log out everywhere)
    cur.execute("""
        UPDATE UserInfo
        SET is_logged_in = 0, session_token = NULL, session_expiry = NULL, device_id = NULL
        WHERE User_id = %s
    """, (user_id,))

    # Create new session
    cur.execute("""
        UPDATE UserInfo
        SET is_logged_in = 1,
            session_token = %s,
            last_activity = NOW(),
            session_expiry = %s,
            device_id = %s
        WHERE User_id = %s
    """, (token, expiry_time, device_id, user_id))

    mysql.connection.commit()
    cur.close()
    return token
    print("session created")    

def validate_session(user_id, token):
    """Check if the current session is valid and active."""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT last_activity, session_expiry, is_logged_in
        FROM UserInfo
        WHERE User_id = %s AND session_token = %s
    """, (user_id, token))
    user = cur.fetchone()
    cur.close()

    if not user:
        return False

    last_activity, session_expiry, is_logged_in = user

    # If not logged in or session expired
    if not is_logged_in or datetime.now() > session_expiry:
        deactivate_session(user_id)
        return False

    # Extend session on activity
    new_expiry = datetime.now() + timedelta(minutes=10)
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE UserInfo
        SET last_activity = NOW(), session_expiry = %s
        WHERE User_id = %s
    """, (new_expiry, user_id))
    mysql.connection.commit()
    cur.close()

    return True

def deactivate_session(user_id):
    """Clear session data in UserInfo."""
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE UserInfo
        SET is_logged_in = 0, session_token = NULL,
            session_expiry = NULL, device_id = NULL
        WHERE User_id = %s
    """, (user_id,))
    mysql.connection.commit()
    cur.close()


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
            device_id = request.headers.get('User-Agent')  # identifies the device/browser
            session_token = create_user_session(user[0], device_id)  # user[0] = User_id

            # login success
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['gender'] = user[3]
            session['session_token'] = session_token
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT MAX(Last_updated_at)
                FROM User_Skin_Info
                WHERE User_id = %s
            """, (user[0],))
            last_update = cur.fetchone()[0]
            cur.close()

            last_seen = session.get('last_seen_skin_update')
            if not last_seen or str(last_seen) != str(last_update):
                session['show_skin_update_popup'] = True
                session['last_seen_skin_update'] = str(last_update)
            else:
                session['show_skin_update_popup'] = False
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

@app.route('/skin_info')
def skin_info():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))

    user_id = session['user_id']

    # Check session expiry
    cur = mysql.connection.cursor()
    cur.execute("SELECT session_expiry FROM UserInfo WHERE User_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()

    if result:
        expiry_time = result[0]
        if expiry_time and datetime.now() > expiry_time:
            # Expired → clear session and log out
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE UserInfo
                SET is_logged_in = 0, session_token = NULL, session_expiry = NULL, device_id = NULL
                WHERE User_id = %s
            """, (user_id,))
            mysql.connection.commit()
            cur.close()

            session.clear()
            flash("Session expired. Please log in again.", "warning")
            return redirect(url_for('login_submit'))

    # If not expired, continue to page
    show_update = session.pop('show_skin_update_popup', False)
    return render_template('skin_info.html', show_update=show_update)


@app.route('/submit_skin_info', methods=['POST'])
def submit_skin_info():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))

    skin_type = request.form.get('skin_type')
    concern = request.form.get('concern')
    user_id = session['user_id']

    cursor = mysql.connection.cursor()

    # Count previous quizzes
    cursor.execute("""
        SELECT Total_num_of_Quiz_taken FROM User_Skin_Info
        WHERE User_id = %s
        ORDER BY ID DESC
        LIMIT 1
    """, (user_id,))
    last_entry = cursor.fetchone()
    total_quiz = last_entry[0] + 1 if last_entry else 1

    # Insert new entry
    cursor.execute("""
        INSERT INTO User_Skin_Info 
        (User_id, Skin_type, Concern, Last_updated_at, Total_num_of_Quiz_taken)
        VALUES (%s, %s, %s, NOW(), %s)
    """, (user_id, skin_type, concern, total_quiz))

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

    # Get user's latest quiz result
    cur.execute("""
        SELECT Skin_type, Concern
        FROM User_Skin_Info 
        WHERE User_id = %s 
        ORDER BY Last_updated_at DESC 
        LIMIT 1
    """, (user_id,))
    user_skin = cur.fetchone()

    if not user_skin:
        flash("Please complete the skin quiz first.", "warning")
        return render_template("product.html", diet=[], skin_type=None, concern=None, image_url=None)

    skin_type = user_skin[0].strip()
    concern = user_skin[1].strip()

    # Fetch all diet info for that skin_type + concern
    cur.execute("""
        SELECT recommendations, to_avoid
        FROM diet_info
        WHERE LOWER(skin_type) = %s
          AND LOWER(concern) = %s
    """, (skin_type.lower(), concern.lower()))
    diet_rows = cur.fetchall()

    diet = []
    for row in diet_rows:
        diet.append({
            "recommendations": [r.strip() for r in row[0].split(",")] if row[0] else [],
            "to_avoid": [a.strip() for a in row[1].split(",")] if row[1] else []
        })

    # 🔹 Fetch image for this skin type from SkinInfo
    cur.execute("""
        SELECT image_url 
        FROM SkinInfo 
        WHERE LOWER(skin_type) = %s
        LIMIT 1
    """, (skin_type.lower(),))
    image_row = cur.fetchone()
    image_url = image_row[0] if image_row else None

    cur.close()

    return render_template(
        "product.html",
        diet=diet,
        skin_type=skin_type,
        concern=concern,
        image_url=image_url  # 🔹 send to template
    )

@app.route("/show_suggestions")
def show_suggestions():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Get latest quiz
    cur.execute("""
        SELECT Skin_type, Concern
        FROM User_Skin_Info
        WHERE User_id = %s
        ORDER BY ID DESC
        LIMIT 1
    """, (user_id,))
    user_row = cur.fetchone()

    if not user_row:
        return render_template("suggestions.html",
                               skin_type=None, concern=None,
                               am_routine=None, pm_routine=None, description=None)

    skin_type, concern = user_row

    # Fetch routines from SkinInfo
    cur.execute("""
        SELECT description, am_routine, pm_routine,image_url
        FROM SkinInfo
        WHERE LOWER(skin_type) = LOWER(%s)
          AND LOWER(concern) = LOWER(%s)
        LIMIT 1
    """, (skin_type, concern))

    info = cur.fetchone()
    cur.close()

    if info:
        description, am_routine_json, pm_routine_json,image_url = info

        am_routine = json.loads(am_routine_json)
        pm_routine = json.loads(pm_routine_json)
    else:
        description = am_routine = pm_routine = None

    return render_template("suggestions.html",
                           skin_type=skin_type,
                           concern=concern,
                           description=description,
                           am_routine=am_routine,
                           pm_routine=pm_routine,
                           image_url=image_url)


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
        SELECT Skin_type, Concern
        FROM User_Skin_Info
        WHERE user_id = %s
        ORDER BY ID DESC
        LIMIT 1
    """, (current_user_id,))
    
    last_entry = cur.fetchone()

    if last_entry:
        skin_type, concern = last_entry

        # Get skincare routines from SkinInfo
        cur.execute("""
            SELECT am_routine, pm_routine
            FROM SkinInfo
            WHERE LOWER(skin_type) = LOWER(%s)
              AND LOWER(concern) = LOWER(%s)
            LIMIT 1
        """, (skin_type, concern))
        
        routines = cur.fetchone()
        cur.close()

        if routines:
            import ast
            # Convert stringified dicts back to Python dicts
            am_routine = ast.literal_eval(routines[0])
            pm_routine = ast.literal_eval(routines[1])
        else:
            am_routine = {}
            pm_routine = {}

        return render_template(
            'suggestions.html',
            skin_type=skin_type,
            concern=concern,
            gender=gender,
            am_routine=am_routine,
            pm_routine=pm_routine
        )
    else:
        cur.close()
        return render_template(
            'suggestions.html',
            skin_type=None,
            concern=None,
            gender=gender,
            am_routine={},
            pm_routine={}
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
        SELECT Skin_type, Concern
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
                           concern=skin_info[1] if skin_info else "")
""
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
        age_pattern = r"^(1[3-9]|[2-9][0-9])$"  # optional: 13–120 valid ages

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
            flash("Invalid age! Must be between 13 and 99.", "danger")
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

@app.before_request
def check_session_validity():
    protected_routes = ['skin_info', 'show_suggestions', 'profile_page', 
                        'edit_profile', 'submit_skin_info', 'recommendations']

    if request.endpoint in protected_routes:
        user_id = session.get('user_id')
        token = session.get('session_token')

        if not user_id or not token or not validate_session(user_id, token):
            session.clear()
            flash("Session expired or logged in elsewhere. Please log in again.", "warning")
            return redirect(url_for('login_submit'))

@app.route('/skin1')
def skin1():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))
    return render_template('skin1.html', page=1, total_pages=3)

@app.route('/skin2')
def skin2():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))
    return render_template('skin2.html', page=2, total_pages=3)

@app.route('/skin3')
def skin3():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('login_submit'))
    return render_template('skin3.html', page=3, total_pages=3)


@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        deactivate_session(user_id)

    session.clear()
    flash("You have been logged out.", "info")

    response = make_response(redirect(url_for('login_submit')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


if __name__ == "__main__":
    app.run(debug=True)
