from flask import Flask, render_template, redirect, request, session, flash, url_for, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import stripe
from flask_mail import Mail, Message
import secrets
import json
app = Flask(__name__)
app.secret_key = "265371"

# إعدادات البريد الإلكتروني
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password_or_app_password'

mail = Mail(app)
stripe.api_key = "sk_test_XXXXXXXXXXXX"


def load_tests():
    with open("tests_data.json", encoding="utf-8") as f:
        return json.load(f)["tests"]
@app.route("/examen_t")
def examen_t():
    return render_template("examen_t.html")    

@app.route("/test/<int:test_id>")
def show_test(test_id):
    if "user_id" not in session:
        return redirect("/inloggen")
    user_id = session["user_id"]
    tests = load_tests()
    test = next((test for test in tests if test['id'] == test_id), None)
    if not test:
        return "اختبار غير موجود", 404
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT attempts FROM user_tests WHERE user_id=? AND test_id=?", (user_id, test_id))
        row = cursor.fetchone()
        attempts_count = row[0] if row else 0
    return render_template("test_page.html", test=test, attempts_count=attempts_count)

@app.route("/api/test/<int:test_id>")
def api_test_questions(test_id):
    tests = load_tests()
    test = next((test for test in tests if test['id'] == test_id), None)
    if not test:
        return jsonify({"error": "not found"}), 404
    return jsonify(test)

def generate_reset_token():
    return secrets.token_urlsafe(32)

@app.route("/")
def home():
    prijzen = {
        'Gouden': 1,
        'Zilveren': 20,
        'Bronzen': 15
    }
    if "user_id" not in session:
        return redirect("/inloggen")
    return render_template("home.html", prijzen=prijzen)

@app.route("/inloggen", methods=["GET", "POST"])
def inloggen():
    if request.method == "POST":
        username_or_email = request.form.get("username_or_email")
        password = request.form.get("password")
        if not username_or_email or not password:
            flash("Gelieve alle velden in te vullen.")
            return redirect("/inloggen")
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? OR email=?", (username_or_email, username_or_email))
            user = cursor.fetchone()
        if user:
            if check_password_hash(user[3], password):
                session["user_id"] = user[0]
                flash("Succesvol ingelogd!")
                return redirect("/dashboard")
            else:
                flash("Het wachtwoord is niet correct.")
        else:
            flash("De gebruikersnaam of e-mail is niet correct.")
    return render_template("inloggen.html")

@app.route("/bestellen", methods=["GET", "POST"])
def bestellen():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        payment = request.form.get("payment")
        password = request.form.get("password")
        if not username or not email or not password or not payment:
            flash("Gelieve alle velden in te vullen.")
            return redirect("/bestellen")
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? OR email=?", (username, email))
            existing = cursor.fetchone()
            if existing:
                flash("Deze gebruikersnaam of e-mail bestaat al.")
                return redirect("/bestellen")
            hash_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, email, password, payment) VALUES (?, ?, ?, ?)",
                        (username, email, hash_password, payment))
            conn.commit()
        
        if payment == "ideal" or payment == "creditcard":
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": "Abonnement",
                        },
                        "unit_amount": 2500,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=url_for('dashboard', _external=True),
                cancel_url=url_for('bestellen', _external=True),
                customer_email=email
            )
            return redirect(checkout_session.url)
        elif payment == "paypal":
            return redirect("https://www.paypal.com/checkoutnow?token=YOUR_PAYPAL_TOKEN")
        else:
            flash("Account aangemaakt! Betaal contant bij de vestiging.")
            return redirect("/inloggen")
    return render_template("bestellen.html")

@app.route("/uitloggen")
def uitloggen():
    session.clear()
    flash("Je bent succesvol uitgelogd.")
    return redirect("/inloggen")

@app.route("/videos_page")
def videos_page():
    return render_template("videos_page.html")

@app.route("/image_page")
def image_page():
    if "user_id" not in session:
        return redirect("/inloggen")
    user_id = session["user_id"]
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT attempts FROM user_tests WHERE user_id=? AND test_id=?", (user_id, 2))
        row = cursor.fetchone()
        attempts_count = row[0] if row else 0
    return render_template("image_page.html", attempts_count=attempts_count)

@app.route("/get_attempts/<int:test_id>")
def get_attempts(test_id):
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401
    user_id = session["user_id"]
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT attempts FROM user_tests WHERE user_id=? AND test_id=?", (user_id, test_id))
        row = cursor.fetchone()
        attempts_count = row[0] if row else 0
    return jsonify({"attempts_count": attempts_count}), 200

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/inloggen")
    user_id = session["user_id"]
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()
    username = user[0] if user else ""
    email = user[1] if user else ""
    return render_template("dashboard.html", username=username, email=email)

@app.route("/examen")
def examen():
    if "user_id" not in session:
        return redirect("/inloggen")
    user_id = session["user_id"]
    attempts = {}
    TOTAL_TESTS = 20
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT test_id, attempts FROM user_tests WHERE user_id=?", (user_id,))
        rows = cursor.fetchall()
        for test_id, attempt_count in rows:
            attempts[test_id] = attempt_count
    for test_id in range(1, TOTAL_TESTS+1):
        if test_id not in attempts:
            attempts[test_id] = 0
    return render_template("examen.html", attempts=attempts)

def add_attempt(user_id, test_id):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT attempts FROM user_tests WHERE user_id=? AND test_id=?", (user_id, test_id))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE user_tests SET attempts=attempts+1 WHERE user_id=? AND test_id=?", (user_id, test_id))
        else:
            cursor.execute("INSERT INTO user_tests (user_id, test_id, attempts) VALUES (?, ?, 1)", (user_id, test_id))
        conn.commit()

@app.route("/finish_test/<int:test_id>", methods=["POST"])
def finish_test(test_id):
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401
    user_id = session["user_id"]
    add_attempt(user_id, test_id)
    return jsonify({"ok": True}), 200

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email=?", (email,))
            user = cursor.fetchone()
        if user:
            user_id = user[0]
            token = generate_reset_token()
            with sqlite3.connect("users.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO password_resets (user_id, token) VALUES (?, ?)", (user_id, token))
                conn.commit()
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message(
                subject="إعادة تعيين كلمة المرور",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email],
                body=f"لإعادة تعيين كلمة المرور، اضغط على الرابط التالي:\n{reset_link}\nهذا الرابط صالح لمرة واحدة فقط."
            )
            try:
                mail.send(msg)
                flash("تم إرسال رابط استعادة كلمة المرور إلى بريدك الإلكتروني.")
            except Exception as e:
                print(e)
                flash("حدث خطأ أثناء إرسال الرسالة. تأكد من صحة البريد أو تواصل مع الدعم.")
        else:
            flash("البريد غير موجود لدينا.")
        return redirect("/inloggen")
    return render_template("forgot_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM password_resets WHERE token=?", (token,))
        row = cursor.fetchone()
    if not row:
        flash("الرابط غير صالح أو انتهت صلاحيته.")
        return redirect("/inloggen")
    if request.method == "POST":
        new_password = request.form.get("password")
        if not new_password:
            flash("يرجى إدخال كلمة مرور جديدة")
            return redirect(request.url)
        hash_pass = generate_password_hash(new_password)
        user_id = row[0]
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password=? WHERE id=?", (hash_pass, user_id))
            cursor.execute("DELETE FROM password_resets WHERE token=?", (token,))
            conn.commit()
        flash("تم تغيير كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول.")
        return redirect("/inloggen")
    return render_template("reset_password.html", token=token)

@app.route("/intro_video")
def intro_video():
    return render_template("intro_video.html")

if __name__ == "__main__":
    app.run(debug=True)