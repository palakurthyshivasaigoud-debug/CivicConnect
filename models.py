from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(12), unique=True, nullable=False)
    user_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    image_path = db.Column(db.String(300), nullable=True)
    category = db.Column(db.String(80))
    sentiment = db.Column(db.String(50))
    status = db.Column(db.String(80), default="Submitted")
    priority = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    language = db.Column(db.String(10), default="en")
    feedback = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "tracking_id": self.tracking_id,
            "user_name": self.user_name,
            "email": self.email,
            "title": self.title,
            "description": self.description,
            "image_path": self.image_path,
            "category": self.category,
            "sentiment": self.sentiment,
            "status": self.status,
            "priority": self.priority,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "language": self.language,
            "feedback": self.feedback,
            "rating": self.rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
