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
        return '<User {}>'.format({self.id,self.fullname, self.roles})

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
    content: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
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
    course_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("courses.id"), nullable=False)
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

