from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Question(db.Model):
    """Model for IELTS speaking questions."""
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responses = db.relationship('Response', backref='question', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'topic': self.topic,
            'created_at': self.created_at.isoformat()
        }

class Response(db.Model):
    """Model for user responses to IELTS questions."""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    audio_path = db.Column(db.String(255), nullable=False)
    transcript = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.relationship('Result', backref='response', uselist=False)

class Result(db.Model):
    """Model for analysis results of user responses."""
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey('response.id'), nullable=False)
    fluency_score = db.Column(db.Float, nullable=False)
    vocabulary_score = db.Column(db.Float, nullable=False)
    grammar_score = db.Column(db.Float, nullable=False)
    coherence_score = db.Column(db.Float, nullable=False)
    overall_score = db.Column(db.Float, nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserProgress(db.Model):
    """User progress tracking over time."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, unique=True)
    test_count = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Float, default=0.0)
    average_score = db.Column(db.Float, default=0.0)
    latest_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProgress for user {self.user_id}, avg: {self.average_score}>'

