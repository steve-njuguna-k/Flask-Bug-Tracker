import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

bug_tags = db.Table('bug_tags',
    db.Column('bug_id', db.Integer, db.ForeignKey('bugs.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(256), unique=True)
    bugs = db.relationship('Bugs',backref = 'user_bug',lazy = "dynamic")
    comments = db.relationship('Comments',backref = 'user_comment',lazy = "dynamic")
    profile_pic = db.Column(db.String(500), nullable=False, default='https://upload.wikimedia.org/wikipedia/commons/7/7c/Profile_avatar_placeholder_large.png')
    registered_on = db.Column(db.DateTime, nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    def __init__(self, username, email, password, confirmed, confirmed_on=None):
        self.username = username
        self.email = email
        self.password = password
        self.registered_on = datetime.datetime.now()
        self.confirmed = confirmed
        self.confirmed_on = confirmed_on

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'User: {self.username}'

class Bugs(db.Model):
    __tablename__ = 'bugs'

    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(20000), nullable=False)
    comment = db.relationship('Comments', backref='bug_comment', lazy='dynamic')
    tags = db.relationship('Tags',secondary=bug_tags, back_populates="bugs")
    author = db.Column(db.Integer,db.ForeignKey('users.id'))
    bug_status = db.Column(db.String, nullable=False, default='Unresolved')
    created_on = db.Column(db.DateTime, default = datetime.datetime.utcnow())
    updated_on = db.Column(db.DateTime, nullable=True)
    upvotes = db.relationship('Upvote', backref='bug_upvotes')
    downvotes = db.relationship('Downvote', backref='bug_downvotes')

    def __init__(self, title, description):
        self.title = title
        self.description = description
        self.registered_on = datetime.datetime.now()

    def __repr__(self):
        return '<Bugs: {}>'.format(self.description)

class Comments(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer,primary_key=True)
    comment = db.Column(db.String(1000), nullable=False)
    bug = db.Column(db.Integer, db.ForeignKey('bugs.id'))
    date_published = db.Column(db.DateTime, default = datetime.datetime.utcnow)
    user = db.Column(db.Integer,db.ForeignKey('users.id'))
    upvotes = db.relationship('Upvote', backref='comment_upvotes')
    downvotes = db.relationship('Downvote', backref='comment_downvotes')

    def __init__(self, comment):
        self.comment = comment

    def __repr__(self):
        return '<Comment: {}>'.format(self.comment)

class Tags(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    bugs = db.relationship('Bugs', secondary = bug_tags, back_populates = "tags")
    created_on = db.Column(db.DateTime, default = datetime.datetime.utcnow)

    def __repr__(self):
        return "<{}:{}>".format(self.id, self.name)

class Upvote(db.Model):
    __tablename__ = 'upvotes'

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    bug_id = db.Column(db.Integer,db.ForeignKey('bugs.id'))
    comment_id = db.Column(db.Integer,db.ForeignKey('comments.id'))

    @classmethod
    def get_upvotes(cls,id):
        upvote = Upvote.query.filter_by(bug_id=id).all()
        return upvote

    def __repr__(self):
        return f'{self.user_id}:{self.bug_id}'

class Downvote(db.Model):
    __tablename__ = 'downvotes'

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    bug_id = db.Column(db.Integer,db.ForeignKey('bugs.id'))
    comment_id = db.Column(db.Integer,db.ForeignKey('comments.id'))
    
    @classmethod
    def get_downvotes(cls,id):
        downvote = Downvote.query.filter_by(bug_id=id).all()
        return downvote

    def __repr__(self):
        return f'{self.user_id}:{self.bug_id}'