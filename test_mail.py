from flask_mail import Mail, Message
from flask import Flask

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'

mail = Mail(app)

with app.app_context():
    msg = Message(
        subject="اختبار البريد",
        sender=app.config['MAIL_USERNAME'],
        recipients=['your_email@gmail.com'],  # جرب ترسل لنفسك أولاً
        body="هذه رسالة اختبار من Flask-Mail"
    )
    mail.send(msg)
    print("تم الإرسال!")