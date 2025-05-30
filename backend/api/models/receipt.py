from ..utils import db
from datetime import datetime,timezone


class Receipt(db.Model):
    __tablename__ = 'receipts'

    id = db.Column(db.Integer, primary_key=True)
    receipt_file_id = db.Column(db.Integer, db.ForeignKey('receipt_files.id'), nullable=False)

    purchased_at = db.Column(db.DateTime)
    merchant_name = db.Column(db.String(255))
    total_amount = db.Column(db.Float)
    file_path = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))



    def __str__(self):
        return f"<Receipt {self.id}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls,id):
        return cls.query.get_or_404(id)
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()