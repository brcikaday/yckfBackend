import jwt
from app import db
import sqlalchemy as sa
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy.orm as so 
from typing import Optional
from app import app
from time import time
from datetime import datetime, timezone



class User(db.Model):
    __tablename__ = "users"

    id : so.Mapped[int] = so.mapped_column( primary_key=True)
    fullname: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    roles: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64), default='student')
    donations: so.Mapped[list["Donation"]] = so.relationship("Donation", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return '<User {}>'.format({self.id,self.fullname, self.roles,self.password_hash})

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash,password)
    
    def get_reset_password_token(self,expires_in = 600):
        return jwt.encode(
            {'reset_password': self.id, 'pw_hash': self.password_hash, 'exp': time() + expires_in},
        app.config['SECRET_KEY'], algorithm='HS256'
        )
    
    def to_dict(self):
        return {
            "id": self.id,
            "fullname": self.fullname,
            "email": self.email,
            "roles": self.roles
        }

    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token,app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User,id)
    
    

    


class Course(db.Model):
    __tablename__ = "courses"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    description: so.Mapped[str] = so.mapped_column(sa.Text)
    pdf_url: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255), nullable=True)
    video_url: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255), nullable=True)
    level: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50), nullable=True)
    # Determines course type
    is_multipart: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    is_premium: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    time: so.Mapped[Optional[float]] = so.mapped_column(sa.Float, default=0.0)
    tags: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255), nullable=True)

    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=sa.func.now())
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())

    category_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("categories.id"), nullable=True)

    lessons: so.Mapped[list["Lesson"]] = so.relationship("Lesson", back_populates="course", cascade="all, delete")
    enrollments: so.Mapped[list["Enrollment"]] = so.relationship("Enrollment", back_populates="course", cascade="all, delete")

    category: so.Mapped["Category"] = so.relationship("Category", back_populates="courses")
    donations: so.Mapped[list["Donation"]] = so.relationship("Donation", back_populates="course", cascade="all, delete")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "pdf_url": self.pdf_url,
            "level": self.level,
            "time": self.time,
            "tags": self.tags,
            "video_url": self.video_url,
            "is_multipart": self.is_multipart,
            "is_premium": self.is_premium,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "category_id": self.category_id
        }




class Lesson(db.Model):
    __tablename__ = "lessons"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    # content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    video_url: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=True)
    pdf_url: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=True)
    order: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)  # For ordering lessons

    course_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )

    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    course: so.Mapped["Course"] = so.relationship("Course", back_populates="lessons")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            # "content": self.content,
            "video_url": self.video_url,
            "pdf_url": self.pdf_url,
            "order": self.order,
            "course_id": self.course_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Enrollment(db.Model):

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )

    progress: so.Mapped[float] = so.mapped_column(sa.Float, default=0.0)  # 0–100%
    enrolled_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    course: so.Mapped["Course"] = so.relationship("Course", back_populates="enrollments")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "course": {
            "id": self.course.id,
            "title": self.course.title,
            },
            "progress": self.progress,
            "enrolled_at": self.enrolled_at.strftime("%Y-%m-%d %H:%M:%S"),
        }



class Category(db.Model):
    __tablename__ = "categories"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, nullable=False)

    courses: so.Mapped[list["Course"]] = so.relationship(
        "Course", back_populates="category", cascade="all, delete"
    )
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


class Donation(db.Model):
    __tablename__ = "donations"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("users.id"), nullable=False)
    amount: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)
    course_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("courses.id"), nullable=True)
    currency: so.Mapped[str] = so.mapped_column(sa.String(10), default="GHS")
    payment_method: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)
    status: so.Mapped[str] = so.mapped_column(sa.String(20), default="pending")
    transaction_ref: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True, nullable=True)
    webhook_confirmed: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc))

    user: so.Mapped["User"] = so.relationship("User", back_populates="donations")
    course: so.Mapped["Course"] = so.relationship("Course", back_populates="donations")
    

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    action_type: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False)  # e.g., 'user', 'course', 'enrollment'
    description: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=sa.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.action_type,
            "message": self.description,
            "date": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
    

    def log_activity(action_type, description):
        activity = ActivityLog(action_type=action_type, description=description)
        db.session.add(activity)
        db.session.commit()










class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    
    # Who performed the action
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("users.id"), nullable=False)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)
    role: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False)  # ' or 'secondary'
    
    # What action was performed
    action: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)  # e.g., 'Updated Payment Key'
    action_type: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False)  # e.g., 'financial', 'user', 'course'
    description: so.Mapped[str] = so.mapped_column(sa.String(500), nullable=False)
    
    # Target of the action (optional)
    target_type: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)  # e.g., 'user', 'course', 'payment_key'
    target_id: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    
    # When and where
    timestamp: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=sa.func.now(), index=True)
    ip_address: so.Mapped[str] = so.mapped_column(sa.String(45), nullable=True)  # IPv4 or IPv6
    user_agent: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=True)
    
    # Status
    status: so.Mapped[str] = so.mapped_column(sa.String(20), default='success')  # 'success' or 'failed'
    error_message: so.Mapped[str] = so.mapped_column(sa.String(500), nullable=True)
    
    # Additional metadata (JSON for flexibility)
    meta_data: so.Mapped[dict] = so.mapped_column(sa.JSON, nullable=True)
    
    # Relationship
    admin = db.relationship("User", backref="audit_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role,
            "action": self.action,
            "action_type": self.action_type,
            "description": self.description,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
            "meta_data": self.meta_data
        }

    @staticmethod
    def log_audit(id, name, role, action, action_type, description, 
                  target_type=None, target_id=None, ip_address=None, user_agent=None, 
                  status='success', error_message=None, meta_data=None):
        """
        Log an audit entry
        
        Example usage:
        AuditLog.log_audit(
            id=1,
            name="John Doe",
            role="",
            action="Updated Payment Key",
            action_type="financial",
            description="Updated Flutterwave API keys",
            target_type="payment_key",
            target_id=5,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            status='success',
            meta_data={"provider": "Flutterwave"}
        )
        """
        audit = AuditLog(
            id=id,
            name=name,
            role=role,
            action=action,
            action_type=action_type,
            description=description,
            target_type=target_type,
            target_id=target_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
            meta_data=meta_data
        )
        db.session.add(audit)
        db.session.commit()
        return audit


    @staticmethod
    def get_logs_filtered(name=None, action_type=None, date_from=None, date_to=None, status=None):
        """Get filtered audit logs"""
        query = AuditLog.query
        
        if name:
            query = query.filter(AuditLog.name.ilike(f'%{name}%'))
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        if date_from:
            query = query.filter(AuditLog.timestamp >= date_from)
        if date_to:
            query = query.filter(AuditLog.timestamp <= date_to)
        if status:
            query = query.filter(AuditLog.status == status)
            
        return query.order_by(AuditLog.timestamp.desc()).all()




class Certificate(db.Model):
    __tablename__ = "certificates"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    cert_id: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("users.id"), nullable=False)
    course_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("courses.id"), nullable=False)
    student_name: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    course_title: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    issue_date: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc))
    signature: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    
    user: so.Mapped["User"] = so.relationship("User")
    course: so.Mapped["Course"] = so.relationship("Course")
    
    def to_dict(self):
        return {
            "id": self.id,
            "cert_id": self.cert_id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "student_name": self.student_name,
            "course_title": self.course_title,
            "issue_date": self.issue_date.strftime("%Y-%m-%d %H:%M:%S"),
            "signature": self.signature
        }