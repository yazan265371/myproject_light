from flask import Flask, render_template, redirect, request, session, flash, url_for, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import stripe
from flask_mail import Mail, Message
import secrets
import json

app = Flask(__name__)
app.secret_key = "265371"

# =========================
# نظام الترجمة (3 لغات)
# =========================

translations = {
    "ar": {
        "lang_name": "العربية",

        # رسائل فلاش
        "fill_all_fields": "يرجى ملء جميع الحقول.",
        "login_success": "تم تسجيل الدخول بنجاح!",
        "password_incorrect": "كلمة المرور غير صحيحة.",
        "username_or_email_incorrect": "اسم المستخدم أو البريد الإلكتروني غير صحيح.",
        "user_exists": "اسم المستخدم أو البريد الإلكتروني موجود بالفعل.",
        "cash_payment_account_created": "تم إنشاء الحساب! يرجى الدفع نقدًا في الفرع.",
        "logout_success": "تم تسجيل الخروج بنجاح.",
        "reset_link_sent": "تم إرسال رابط استعادة كلمة المرور إلى بريدك الإلكتروني.",
        "mail_send_error": "حدث خطأ أثناء إرسال الرسالة. تأكد من صحة البريد أو تواصل مع الدعم.",
        "email_not_found": "البريد الإلكتروني غير موجود لدينا.",
        "reset_link_invalid": "الرابط غير صالح أو انتهت صلاحيته.",
        "enter_new_password": "يرجى إدخال كلمة مرور جديدة.",
        "password_changed_success": "تم تغيير كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول.",
        "header_choose_package": "اختَر الباقة الأنسب لك",
        "nav_login": "تسجيل الدخول",
        "nav_order_package": "طلب باقة",
        "choose_package_title": "اختر الباقة المناسبة!",
        "start_now": "ابدأ الآن",
        "footer_rights": "جميع الحقوق محفوظة",
                # صفحة تسجيل الدخول
        "login_page_title": "تسجيل الدخول",
        "login_heading": "تسجيل الدخول",
        "username_or_email_label": "اسم المستخدم أو البريد الإلكتروني",
        "password_label": "كلمة المرور",
        "forgot_password_link": "نسيت كلمة المرور؟",
        "login_button": "دخول",
        "no_account": "ليس لديك حساب؟",
        "create_account": "أنشئ حساب جديد",


    },
    "nl": {
        "lang_name": "Nederlands",

        # Flash messages
        "fill_all_fields": "Gelieve alle velden in te vullen.",
        "login_success": "Succesvol ingelogd!",
        "password_incorrect": "Het wachtwoord is niet correct.",
        "username_or_email_incorrect": "De gebruikersnaam of e-mail is niet correct.",
        "user_exists": "Deze gebruikersnaam of e-mail bestaat al.",
        "cash_payment_account_created": "Account aangemaakt! Betaal contant bij de vestiging.",
        "logout_success": "Je bent succesvol uitgelogd.",
        "reset_link_sent": "De link om je wachtwoord te herstellen is naar je e-mail gestuurd.",
        "mail_send_error": "Er is een fout opgetreden bij het verzenden van de e-mail. Controleer je e-mailadres of neem contact op met de ondersteuning.",
        "email_not_found": "Dit e-mailadres is niet bij ons bekend.",
        "reset_link_invalid": "De link is ongeldig of verlopen.",
        "enter_new_password": "Voer een nieuw wachtwoord in.",
        "password_changed_success": "Wachtwoord succesvol gewijzigd! Je kunt nu inloggen.",
        "header_choose_package": "Kies het pakket dat bij je past",
        "nav_login": "Inloggen",
        "nav_order_package": "Pakket bestellen",
        "choose_package_title": "Kies jouw ideale pakket!",
        "start_now": "Nu beginnen",
        "footer_rights": "Alle rechten voorbehouden",
                # Login pagina
        "login_page_title": "Inloggen",
        "login_heading": "Inloggen",
        "username_or_email_label": "Gebruikersnaam of e-mailadres",
        "password_label": "Wachtwoord",
        "forgot_password_link": "Wachtwoord vergeten?",
        "login_button": "Inloggen",
        "no_account": "Heb je nog geen account?",
        "create_account": "Maak een nieuw account aan",


    },
    "en": {
        "lang_name": "English",

        # Flash messages
        "fill_all_fields": "Please fill in all fields.",
        "login_success": "Logged in successfully!",
        "password_incorrect": "The password is incorrect.",
        "username_or_email_incorrect": "The username or email is incorrect.",
        "user_exists": "This username or email already exists.",
        "cash_payment_account_created": "Account created! Please pay in cash at the location.",
        "logout_success": "You have been logged out successfully.",
        "reset_link_sent": "A password reset link has been sent to your email.",
        "mail_send_error": "An error occurred while sending the email. Check your address or contact support.",
        "email_not_found": "This email address was not found.",
        "reset_link_invalid": "The link is invalid or has expired.",
        "enter_new_password": "Please enter a new password.",
        "password_changed_success": "Password changed successfully! You can now log in.",
        "header_choose_package": "Choose the package that suits you best",
        "nav_login": "Log in",
        "nav_order_package": "Order a package",
        "choose_package_title": "Choose your ideal package!",
        "start_now": "Start now",
        "footer_rights": "All rights reserved",
                # Login page
        "login_page_title": "Login",
        "login_heading": "Login",
        "username_or_email_label": "Username or email",
        "password_label": "Password",
        "forgot_password_link": "Forgot your password?",
        "login_button": "Login",
        "no_account": "Don't have an account?",
        "create_account": "Create a new account",


    }
}


def get_current_lang():
    lang = session.get("lang", "ar")
    if lang not in translations:
        lang = "ar"
    return lang


def get_text(key):
    lang = get_current_lang()
    return translations[lang].get(key, key)


@app.before_request
def set_language():
    # نقرأ اللغة من الرابط ?lang=ar/nl/en إن وُجدت
    lang = request.args.get("lang")
    if lang in translations:
        session["lang"] = lang


@app.context_processor
def inject_translations():
    # هذا يجعل المتغيرين t و lang متاحين في كل القوالب
    lang = get_current_lang()
    t = translations[lang]
    return dict(lang=lang, t=t)


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
            flash(get_text("fill_all_fields"))
            return redirect("/inloggen")
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? OR email=?", (username_or_email, username_or_email))
            user = cursor.fetchone()
        if user:
            if check_password_hash(user[3], password):
                session["user_id"] = user[0]
                flash(get_text("login_success"))
                return redirect("/dashboard")
            else:
                flash(get_text("password_incorrect"))
        else:
            flash(get_text("username_or_email_incorrect"))
    return render_template("inloggen.html")


@app.route("/bestellen", methods=["GET", "POST"])
def bestellen():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        payment = request.form.get("payment")
        password = request.form.get("password")
        if not username or not email or not password or not payment:
            flash(get_text("fill_all_fields"))
            return redirect("/bestellen")
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? OR email=?", (username, email))
            existing = cursor.fetchone()
            if existing:
                flash(get_text("user_exists"))
                return redirect("/bestellen")
            hash_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, email, password, payment) VALUES (?, ?, ?, ?)",
                (username, email, hash_password, payment)
            )
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
            flash(get_text("cash_payment_account_created"))
            return redirect("/inloggen")
    return render_template("bestellen.html")


@app.route("/uitloggen")
def uitloggen():
    session.clear()
    flash(get_text("logout_success"))
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
    for test_id in range(1, TOTAL_TESTS + 1):
        if test_id not in attempts:
            attempts[test_id] = 0
    return render_template("examen.html", attempts=attempts)


def add_attempt(user_id, test_id):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT attempts FROM user_tests WHERE user_id=? AND test_id=?", (user_id, test_id))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                "UPDATE user_tests SET attempts=attempts+1 WHERE user_id=? AND test_id=?",
                (user_id, test_id)
            )
        else:
            cursor.execute(
                "INSERT INTO user_tests (user_id, test_id, attempts) VALUES (?, ?, 1)",
                (user_id, test_id)
            )
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
                flash(get_text("reset_link_sent"))
            except Exception as e:
                print(e)
                flash(get_text("mail_send_error"))
        else:
            flash(get_text("email_not_found"))
        return redirect("/inloggen")
    return render_template("forgot_password.html")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM password_resets WHERE token=?", (token,))
        row = cursor.fetchone()
    if not row:
        flash(get_text("reset_link_invalid"))
        return redirect("/inloggen")
    if request.method == "POST":
        new_password = request.form.get("password")
        if not new_password:
            flash(get_text("enter_new_password"))
            return redirect(request.url)
        hash_pass = generate_password_hash(new_password)
        user_id = row[0]
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password=? WHERE id=?", (hash_pass, user_id))
            cursor.execute("DELETE FROM password_resets WHERE token=?", (token,))
            conn.commit()
        flash(get_text("password_changed_success"))
        return redirect("/inloggen")
    return render_template("reset_password.html", token=token)


@app.route("/intro_video")
def intro_video():
    return render_template("intro_video.html")


if __name__ == "__main__":
    app.run(debug=True)
