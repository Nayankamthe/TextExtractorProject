from ..utils import db
from datetime import datetime,timezone



class ReceiptFile(db.Model):
    __tablename__ = 'receipt_files'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    is_valid = db.Column(db.Boolean, default=False)
    invalid_reason = db.Column(db.String(255))
    is_processed = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship: One receipt file can have one or more receipts extracted
    receipts = db.relationship('Receipt', backref='receipt_file', lazy=True)

    def __str__(self):
        return f"<ReceiptFile {self.id}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls,id):
        return cls.query.get_or_404(id)
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()