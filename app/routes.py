from app import app
import sqlalchemy as sa
from flask import jsonify, request
import requests
from app.config import Config
from app.models import User, Course,Category, Enrollment, ActivityLog,Donation,Lesson, AuditLog, Certificate
from app import db
from app import jwt
from flask_cors import CORS
import flask_jwt_extended
import hmac
import hashlib
from flask_mail import Message
from app import mail
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.emails import send_password_reset_email, send_donation_email
import os
from werkzeug.utils import secure_filename
from app.helpers.allowedfiles import allowed_file
import time
import uuid
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode
from PIL import Image
import io
from flask import send_file, current_app
from datetime import datetime



CORS(app)

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    existing_user = db.session.scalar(sa.select(User).where(User.email == data['email']))
    if existing_user:
        return jsonify({'message': 'Email already registered'}), 400
    
    new_user = User(
        email=data['email'],
        fullname=data['full_name']
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    ActivityLog.log_activity("user", f"Registered user: {new_user.fullname}")
    return jsonify({'message': 'Registration successful'}), 201



@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    user = db.session.scalar(sa.select(User).where(User.email == data['email']))
    role = user.roles
    if user and user.check_password(data['password']):
        access_token = flask_jwt_extended.create_access_token(identity=str(user.id), additional_claims={"role": role})
        return jsonify({'message': 'Login successful', 'access_token': access_token, 'role': role}), 200
    

    return jsonify({'message': 'Invalid email or password'}), 401





@app.route('/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    email = data['email'].strip().lower()
    user = db.session.scalar(sa.select(User).where(User.email == email))
    if user:
        send_password_reset_email(user)
        return jsonify({'message': 'Password reset link has been sent to your email'}), 200
    ActivityLog.log_activity("user", f"Password reset requested for non-existent email: {email}")
    return jsonify({'message': 'User not found'}), 404





@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    password = data.get('password')
    token = data.get('token')
    if not token or not password:
        return jsonify({'error': 'Password is required'}), 400

    # Use the static method
    user = User.verify_reset_password_token(token)
    if not user:
        return jsonify({'error': 'Invalid or expired token'}), 400

    user.set_password(password)
    db.session.commit()

    return jsonify({'message': 'Your password has been reset successfully'}), 200




@app.route('/courses', methods=['GET'])
def get_courses():
    courses = db.session.scalars(sa.select(Course)).all()
    return jsonify([course.to_dict() for course in courses]), 200


@app.route('/courses/<int:id>', methods=['GET'])
def get_course(id):
    course = db.session.get(Course, id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    return jsonify(course.to_dict()), 200



@app.route('/create_course', methods=['POST'])
def create_course():
    # Get form fields directly from request.form
    title = request.form.get('title')
    description = request.form.get('description')
    time = request.form.get('time')
    level = request.form.get('level')
    raw_tags = request.form.get('tags', '')
    video_url = request.form.get('video_url')
    is_premium = request.form.get('is_premium') == 'true'
    is_multipart = request.form.get('is_multipart') == 'true'
    category_id = request.form.get('category_id')

    # Handle tags
    tags_list = [tag.strip() for tag in raw_tags.split(',') if tag.strip()]
    tags = ', '.join(tags_list)

    # Handle file upload
    pdf_file_path = None
    if not is_multipart and 'pdf_file' in request.files:
        pdf_file = request.files.get('pdf_file')
        if allowed_file(pdf_file.filename):
            filename = secure_filename(pdf_file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf_file.save(pdf_path)
            pdf_file_path = pdf_path

    # Create and save course
    new_course = Course(
        title=title,
        description=description,
        video_url=video_url,
        is_premium=is_premium,
        time=time,
        level=level,
        tags=tags,
        is_multipart=is_multipart,
        category_id=category_id,
        pdf_url=pdf_file_path
    )

    db.session.add(new_course)
    db.session.commit()
    ActivityLog.log_activity("course", f"Created course: {title}")

    return jsonify({'message': 'Course created successfully'}), 201



@app.route('/courses/<int:id>', methods=['PUT'])
def update_course(id):
    course = db.session.get(Course, id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    course.title =request.form.get('title')
    course.description = request.form.get('description')
    course.video_url = request.form.get('video_url')
    course.time = request.form.get('time')
    course.level = request.form.get('level')
    course.tags = request.form.get('tags')
    course.is_multipart = request.form.get('is_multipart') == 'true'
    course.pdf_url = request.form.get('pdf_url') 
    course.is_premium = request.form.get('is_premium') == 'true'
    course.category_id = request.form.get('category_id')

    db.session.commit()
    ActivityLog.log_activity("course", f"Updated course: {course.title}")

    return jsonify({'message': 'Course updated successfully'}), 200



@app.route('/courses/<int:id>', methods=['DELETE'])
def delete_course(id):
    course = db.session.get(Course, id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    db.session.delete(course)
    db.session.commit()
    ActivityLog.log_activity("course", f"Deleted course: {course.title}")

    return jsonify({'message': 'Course deleted successfully'}), 200



@app.route('/courses/<int:id>/lessons', methods=['POST'])
def add_lesson(id):
    course = db.session.get(Course, id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    data = request.get_json()
    new_lesson = Lesson(
        title=data['title'],
        # content=data['content'],
        video_url=data['video_url'],
        pdf_url=data['content_url'],
        order=data['order'],
        course=course
    )

    db.session.add(new_lesson)
    db.session.commit()
    ActivityLog.log_activity("lesson", f"Created lesson: {new_lesson.title} for course: {course.title}")

    return jsonify({'message': 'Lesson created successfully'}), 201




@app.route('/courses/<int:course_id>/lessons/<int:lesson_id>', methods=['PUT'])
def update_lesson(course_id, lesson_id):
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        return jsonify({'error': 'Lesson not found'}), 404

    data = request.get_json()
    lesson.title = data['title']
    lesson.content = data['content']
    lesson.video_url = data['video_url']
    lesson.pdf_url = data['pdf_url']
    lesson.order = data['order']

    db.session.commit()
    ActivityLog.log_activity("lesson", f"Updated lesson: {lesson.title} for course: {course.title}")

    return jsonify({'message': 'Lesson updated successfully'}), 200


@app.route('/courses/<int:course_id>/lessons', methods=['GET'])
def get_lessons(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    lessons = db.session.scalars(sa.select(Lesson).where(Lesson.course_id == course_id)).all()
    return jsonify([lesson.to_dict() for lesson in lessons]), 200


@app.route('/courses/<int:course_id>/lessons/<int:lesson_id>', methods=['DELETE'])
def delete_lesson(course_id, lesson_id):
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        return jsonify({'error': 'Lesson not found'}), 404

    db.session.delete(lesson)
    db.session.commit()
    ActivityLog.log_activity("lesson", f"Deleted lesson: {lesson.title} for course: {course.title}")

    return jsonify({'message': 'Lesson deleted successfully'}), 200



@app.route('/courses/<int:course_id>/enrollment_status', methods=['GET'])
@jwt_required()
def get_enrollment_status(course_id):
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401

    enrollment = db.session.scalar(sa.select(Enrollment).where(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id
    ))

    # Check if user has made ANY donation (any donation unlocks all premium content)
    has_donation = db.session.scalar(
        sa.select(sa.func.count(Donation.id)).where(Donation.user_id == user_id)
    ) > 0

    return jsonify({
        'is_enrolled': enrollment is not None,
        'has_donated': has_donation,
        'progress': enrollment.progress if enrollment else 0
    }), 200
    


@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
@jwt_required()
def enroll_course(course_id):
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    course = db.session.get(Course, course_id)
    user = db.session.get(User, user_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    if not user:
        return jsonify({'error': 'User not found'}), 404

    existing_enrollment = db.session.scalar(sa.select(Enrollment).where(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id
    ))
    if existing_enrollment:
        return jsonify({'error': 'User already enrolled in this course'}), 400
    
    new_enrollment = Enrollment(
        user_id=user_id,
        course_id=course_id
    )

    db.session.add(new_enrollment)
    db.session.commit()
    ActivityLog.log_activity("enrollment", f" user: {user.fullname} enrolled in course: {course.title}")

    return jsonify({'message': 'Enrollment successful'}), 201



@app.route('/courses/<int:course_id>/progress', methods=['PUT'])
@jwt_required()
def update_progress(course_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    progress = min(100, max(0, data.get('progress', 0)))  # Clamp 0-100
    
    enrollment = db.session.scalar(sa.select(Enrollment).where(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id
    ))
    
    if enrollment:
        enrollment.progress = progress
        db.session.commit()
        return jsonify({'progress': progress}), 200
    
    return jsonify({'error': 'Not enrolled'}), 404




@app.route('/enrolled', methods=['GET'])
@jwt_required()
def get_user_enrollments():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    enrollments = db.session.scalars(sa.select(Enrollment).where(Enrollment.user_id == user_id)).all()
    return jsonify([enrollment.to_dict() for enrollment in enrollments]), 200





@app.route('/users', methods=['GET'])
def get_users():
    users = db.session.scalars(sa.select(User)).all()
    return jsonify([user.to_dict() for user in users]), 200


@app.route('/users/<int:id>/role', methods=['PUT'])
def update_user_role(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    user.roles = data['roles']
    db.session.commit()
    ActivityLog.log_activity("user", f"Updated user role: {user.fullname}")

    return jsonify({'message': 'User role updated successfully'}), 200


@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()
    ActivityLog.log_activity("user", f"Deleted user: {user.fullname}")

    return jsonify({'message': 'User deleted successfully'}), 200



@app.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200



@app.route("/stats", methods=["GET"])
def get_stats():
    # current_user = flask_jwt_extended.get_jwt_identity()
    # claims = flask_jwt_extended.get_jwt()
    total_users = db.session.query(User).count()
    total_courses = db.session.query(Course).count()
    total_categories = db.session.query(Category).count()
    total_enrollments = db.session.query(Enrollment).count()

    return jsonify({
        # "current_user": current_user,
        # "role": claims.get("role"),
        "users": total_users,
        "courses": total_courses,
        "categories": total_categories,
        "enrollments": total_enrollments
    })

@app.route('/activity/recent', methods=['GET'])
def get_recent_activity():
    activities = db.session.scalars(sa.select(ActivityLog).order_by(ActivityLog.timestamp.desc())).all()
    return jsonify([activity.to_dict() for activity in activities]), 200


@app.route('/categories', methods=['GET'])
def get_categories():
    categories = db.session.scalars(sa.select(Category)).all()
    return jsonify([category.to_dict() for category in categories]), 200


@app.route('/categories/create', methods=['POST'])
def create_category():
    data = request.get_json()
    new_category = Category(
        name=data['name']
    )
    db.session.add(new_category)
    db.session.commit()
    ActivityLog.log_activity("category", f"Created category: {new_category.name}")
    return jsonify({'message': 'Category created successfully'}), 201


@app.route('/categories/delete/<int:id>', methods=['DELETE'])
def delete_category(id):
    category = db.session.get(Category, id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404

    db.session.delete(category)
    db.session.commit()
    ActivityLog.log_activity("category", f"Deleted category: {category.name}")

    return jsonify({'message': 'Category deleted successfully'}), 200



@app.route('/categories/edit/<int:id>', methods=['PUT'])
def edit_category(id):
    category = db.session.get(Category, id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404

    data = request.get_json()
    category.name = data['name']

    db.session.commit()
    ActivityLog.log_activity("category", f"Edited category: {category.name}")

    return jsonify({'message': 'Category updated successfully'}), 200


@app.route('/enrollments', methods=['GET'])
def get_enrollments():
    enrollments = db.session.scalars(sa.select(Enrollment)).all()
    return jsonify([enrollment.to_dict() for enrollment in enrollments]), 200



@app.route('/enrollments/<int:id>', methods=['DELETE'])
def delete_enrollment(id):
    enrollment = db.session.get(Enrollment, id)
    if not enrollment:
        return jsonify({'error': 'Enrollment not found'}), 404

    db.session.delete(enrollment)
    db.session.commit()
    ActivityLog.log_activity("enrollment", f"Deleted enrollment: {enrollment.id}")
    return jsonify({'message': 'Enrollment deleted successfully'}), 200





@app.route('/secondary_admin', methods=['GET'])
def get_secondary_admin():
    secondary_admin = db.session.scalars(sa.select(User).filter_by(roles='secondary_admin')).all()
    return jsonify([admin.to_dict() for admin in secondary_admin]), 200


@app.route('/create/secondary-admins', methods=['POST'])
def add_secondary_admin():
    data = request.get_json()
    email = data['email']
    fullname = data['name']
    password = data['password']
    roles = data['role']

    if not email or not fullname or not password:
        return jsonify({'error': 'Email, full name, and password are required'}), 400

    new_user = User(
        email=email,
        fullname=fullname,
        roles=roles
    )

    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    ActivityLog.log_activity("user", f"Added secondary admin: {new_user.fullname}")

    return jsonify({'message': 'Secondary admin added successfully'}), 201


@app.route('/admin/profile', methods=['PUT'])
@jwt_required()
def update_admin_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    user.fullname = data['name']
    user.email = data['email']
    user.roles = data['roles']

    db.session.commit()
    ActivityLog.log_activity("user", f"Updated admin profile: {user.fullname}")

    return jsonify({'message': 'Admin profile updated successfully'}), 200


@app.route('/admin/password', methods=['PUT'])
def change_admin_password():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    password = data['password']
    user.set_password(password)

    db.session.commit()
    ActivityLog.log_activity("user", f"Changed admin password: {user.fullname}")

    return jsonify({'message': 'Admin password changed successfully'}), 200



@app.route('/student/profile', methods=['GET'])
@jwt_required()
def student_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200



@app.route('/student/change-profile', methods=['PUT'])
@jwt_required()
def change_student_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    user.fullname = data['name']
    email = data['email']

    if db.session.scalar(sa.select(User).where(User.email == email)):
        return jsonify({'error': 'Email already in use'}), 400
    user.email = email
    db.session.commit()
    ActivityLog.log_activity("user", f"Updated student profile: {user.fullname}")
    return jsonify(user.to_dict()), 200



@app.route('/student/change-password', methods=['PUT'])
@jwt_required()
def change_student_password():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    password = data['password']
    user.set_password(password)

    db.session.commit()
    ActivityLog.log_activity("user", f"Changed student password: {user.fullname}")

    return jsonify({'message': 'Student password changed successfully'}), 200



def generate_reference(prefix="donate"):
    """Generate a unique transaction reference string."""
    return f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:6]}"



@app.route('/donations', methods=['GET'])
def get_donations():
    donations = db.session.scalars(sa.select(Donation)).all()
    return jsonify([donation.to_dict() for donation in donations]), 200



@app.route('/donations/create_payment_session', methods=['POST'])
@jwt_required()
def create_donation_payment_session():
    data = request.get_json()
    amount = data['amount']
    callback_url = data.get('callback_url')
    currency = data.get('currency', 'GHS')
    user_id = get_jwt_identity()

    if not amount or amount < 50 or amount > 100 or not user_id:
        return jsonify({"error": "Invalid amount"}), 400
        

    # Generate a unique reference for the transaction
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    email = user.email
    reference = generate_reference()

    # Here you would integrate with your payment gateway to create a payment session
    payload = {
        "email": email,
        "amount": int(amount * 100),
        "reference": reference,
        "callback_url": callback_url
    }

    headers = {
        "Authorization": f"Bearer {Config.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
        res_data = response.json()
    except Exception as e:
        return jsonify({"error": f"Payment initialization failed: {str(e)}"}), 500


    if not res_data.get("status"):
        return jsonify({"error": "Failed to initialize payment"}), 400

    # For demonstration, we'll just return the reference and amount
    donation = Donation(
        user_id=user_id,
        amount=amount,
        currency=currency,
        transaction_ref=reference,
        status="pending",
    )
    db.session.add(donation)
    db.session.commit()

    ActivityLog.log_activity("donation", f"Created donation payment session for user ID: {user_id} with amount: {amount}")


    return jsonify({
        "authorization_url": res_data["data"]["authorization_url"],
        "reference": reference
    }), 200





@app.route("/payment/public-key", methods=["GET"])
def get_public_key():
    """Return Paystack public key to frontend"""
    public_key = os.getenv("PAYSTACK_PUBLIC_KEY")
    return jsonify({"publicKey": public_key})




@app.route('/payments/webhook', methods=['POST'])
def paystack_webhook():
    # Verify Paystack signature
    signature = request.headers.get('x-paystack-signature')
    if not signature:
        return jsonify({"error": "Missing signature"}), 400

    computed_hash = hmac.new(
        Config.PAYSTACK_SECRET_KEY.encode('utf-8'),
        request.data,
        hashlib.sha512
    ).hexdigest()

    if signature != computed_hash:
        return jsonify({"error": "Invalid signature"}), 403

    # Process webhook event
    event = request.get_json()
    if event['event'] == 'charge.success':
        data = event['data']
        reference = data['reference']
        amount = data['amount'] / 100  # Convert from kobo to GHS

        donation = db.session.scalar(sa.select(Donation).where(Donation.transaction_ref == reference))
        if donation and donation.status != 'success':
            donation.status = 'success'
            donation.amount = amount
            donation.webhook_confirmed = True
            db.session.commit()

            # Get user info
            user = db.session.get(User, donation.user_id)

            # Send confirmation email
            send_donation_email(user, donation.amount, donation.transaction_ref)

    return jsonify({"message": "Webhook received successfully"}), 200


@app.route('/verify-payment/<reference>', methods=['GET'])
@jwt_required()
def verify_payment(reference):
    user_id = get_jwt_identity()
    donation = db.session.scalar(sa.select(Donation).where(
        Donation.transaction_ref == reference,
        Donation.user_id == user_id
    ))

    if not donation:
        return jsonify({"error": "Donation not found"}), 404

    if donation.status == 'success':
        return jsonify({"message": "Payment already verified", "status": donation.status}), 200

    headers = {
        "Authorization": f"Bearer {Config.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers,timeout=15)
        res_data = response.json()
    except Exception as e:
        return jsonify({"error": f"Payment verification failed: {str(e)}"}), 500

    if not res_data.get("status"):
        return jsonify({"error": "Failed to verify payment"}), 400

    payment_status = res_data["data"]["status"]
    if payment_status == "success":
        donation.status = 'success'
        donation.webhook_confirmed = True
        db.session.commit()
        ActivityLog.log_activity("donation", f"Verified donation payment for user ID: {user_id} with reference: {reference}")
        return jsonify({"message": "Payment verified successfully", "status": donation.status}), 200
    else:
        donation.status = payment_status
        db.session.commit()
        return jsonify({"message": "Payment not successful", "status": donation.status}), 400


@app.route('/api/exchange-rates', methods=['GET'])
def get_exchange_rates():
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        data = response.json()
        
        # Extract GHS rate
        ghs_rate = data['rates']['GHS']
        
        return jsonify({
            "GHS": ghs_rate,
            "USD": 1.0
        }), 200
    except Exception as e:
        # Fallback to static rate if API fails
        return jsonify({"GHS": 15.5, "USD": 1.0}), 200
























# certificates.py (OR paste directly into your app.py)


# If you use SQLAlchemy/your models:
# from app import db
# from app.models import Student, Certificate

# SECRET for signing certificate verification links - store in env vars
SIGNING_SECRET = os.getenv('CERT_SIGNING_KEY')


def generate_signature(cert_id: str) -> str:
    """Generate HMAC-SHA256 signature"""
    return hmac.new(
        SIGNING_SECRET.encode(),
        cert_id.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_signature(cert_id: str, sig: str) -> bool:
    expected = generate_signature(cert_id)
    return hmac.compare_digest(expected, sig)


def make_qr_image(url: str, box_size=8) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=box_size,
        border=2
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img


def draw_certificate_pdf(buffer, student_name, course_title, date_str, cert_id, qr_img):
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=(width, height))

    # Background
    c.setFillColorRGB(0.95, 0.95, 0.98)
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # Title
    c.setFillColorRGB(0.08, 0.12, 0.27)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width/2, height - 50*mm, "Certificate of Completion")

    # Subtitle
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height - 70*mm, "This certifies that")

    # Student Name
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width/2, height - 95*mm, student_name)

    # Course
    c.setFont("Helvetica", 16)
    c.drawCentredString(width/2, height - 115*mm, f"has completed the course: {course_title}")

    # Date + Certificate ID
    c.setFont("Helvetica", 12)
    c.drawString(25*mm, 25*mm, f"Issue Date: {date_str}")
    c.drawString(25*mm, 20*mm, f"Certificate ID: {cert_id}")

    # Signature line
    c.line(width - 80*mm, 35*mm, width - 25*mm, 35*mm)
    c.setFont("Helvetica", 10)
    c.drawString(width - 75*mm, 30*mm, "Authorized Signature")

    # Logo (optional)
    logo_path = current_app.config.get("CERT_LOGO_PATH")
    if logo_path and os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, 25*mm, height - 40*mm, width=30*mm, height=30*mm)

    # Insert QR Code
    qr_reader = ImageReader(qr_img)
    qr_width = 35*mm
    c.drawImage(qr_reader, width - 55*mm, 25*mm, width=qr_width, height=qr_width)

    c.setFont("Helvetica", 8)
    c.drawCentredString(width - 37*mm, 20*mm, "Scan to verify")

    c.showPage()
    c.save()


# ====================
# ROUTES WITHOUT BLUEPRINTS
# ==================


@app.route("/certificates/generate/<int:course_id>", methods=["POST"])
@jwt_required()
def generate_certificate(course_id):
    user_id = get_jwt_identity()
    
    user = db.session.get(User, user_id)
    course = db.session.get(Course, course_id)
    
    if not user or not course:
        return jsonify({"error": "User or course not found"}), 404
    
    # Check enrollment and progress
    enrollment = db.session.scalar(sa.select(Enrollment).where(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id
    ))
    
    if not enrollment:
        return jsonify({"error": "Not enrolled in this course"}), 400
    
    if enrollment.progress < 100:
        return jsonify({"error": "Course not completed yet"}), 400
    
    # Check if certificate already exists
    existing_cert = db.session.scalar(sa.select(Certificate).where(
        Certificate.user_id == user_id,
        Certificate.course_id == course_id
    ))
    
    if existing_cert:
        return jsonify({"error": "Certificate already generated"}), 400
    
    student_name = user.fullname
    course_title = course.title
    date_str = datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    # Create certificate ID + signature
    cert_id = f"cert_{user_id}_{course_id}_{int(time.time())}"
    sig = generate_signature(cert_id)

    # Save certificate to database
    certificate = Certificate(
        cert_id=cert_id,
        user_id=user_id,
        course_id=course_id,
        student_name=student_name,
        course_title=course_title,
        signature=sig
    )
    db.session.add(certificate)
    db.session.commit()

    # After db.session.commit() in generate_certificate
    AuditLog.log_audit(
    id=user_id,
    name=user.fullname,
    role=user.roles,
    action="Generated Certificate",
    action_type="certificate",
    description=f"Generated certificate for course: {course_title}",
    target_type="certificate",
    target_id=certificate.id,
    ip_address=request.remote_addr,
    user_agent=request.headers.get('User-Agent')
)


    # Verification URL encoded into QR
    base_url = current_app.config.get("BASE_URL", "https://yckf-app.vercel.app")
    verify_url = f"{base_url}/certificates/verify/{cert_id}?sig={sig}"

    qr_img = make_qr_image(verify_url)

    # Generate PDF in memory
    buffer = io.BytesIO()
    draw_certificate_pdf(buffer, student_name, course_title, date_str, cert_id, qr_img)
    buffer.seek(0)

    ActivityLog.log_activity("certificate", f"Generated certificate for {student_name} - {course_title}")
    
    filename = f"certificate_{user.fullname}_{course.title}.pdf".replace(" ", "_")
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")



@app.route("/certificates/verify/<cert_id>", methods=["GET"])
def verify_certificate(cert_id):
    sig = request.args.get("sig", "")
    if not sig or not verify_signature(cert_id, sig):
        return jsonify({"valid": False, "error": "Invalid signature"}), 400

    return jsonify({
        "valid": True,
        "certificate_id": cert_id,
        "message": "Certificate is authentic."
    })

