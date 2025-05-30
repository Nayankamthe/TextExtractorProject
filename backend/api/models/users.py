from ..utils import db


class User(db.Model):
    __tablename__='users'
    id = db.Column(db.Integer(),primary_key=True)
    email = db.Column(db.String(50),nullable=False,unique=True)
    username = db.Column(db.String(45),nullable=False)
    password_hash = db.Column(db.Text(),nullable=False)
    is_active = db.Column(db.Boolean(),default=False)

    # Relationship: One user has many uploaded files
    receipt_files = db.relationship('ReceiptFile', backref='user', lazy=True)
    

    def __repr__(self):
        return f"<User {self.username}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()
        
    def add(self):
        db.session.add(self)

    @classmethod
    def get_by_id(cls,id):
        return cls.query.get_or_404(id)