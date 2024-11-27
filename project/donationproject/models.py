from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from donationproject import db,login_manager,app
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return user.query.get(int(user_id))

class user(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('donation', backref='author', lazy=True)

    def get_reset_token(self,expires_sec=1800):
        s= Serializer(app.config['SECRET_KEY'],expires_sec)
        return s.dumps({'user_id':self.id}).decode('utf-8')
    
    @staticmethod
    def verify_reset_token(token):
        s= Serializer(app.config['SECRET_KEY'])
        try:
            user_id=s.loads(token)['user_id']
        except:
            return None
        return user.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phonenumber = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    organization = db.Column(db.String(100), nullable=False)
    donation_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Donation('{self.donation_date}', '{self.user_id}')"
    
class event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=False, nullable=False)
    author = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    organization = db.Column(db.String(100), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"event('{self.creation_date}', '{self.user_id}','{self.title}', '{self.description}', '{self.organization}', )"