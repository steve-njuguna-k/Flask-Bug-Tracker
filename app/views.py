import datetime
from telnetlib import DO
from app import app
from flask import render_template, flash, redirect, request, url_for
from .token import confirm_token, generate_confirmation_token
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_user, logout_user, login_required
from .email import send_email
from .forms import LoginForm, RegisterForm, CreatePostForm, UpdatePostForm
from .models import db, User, Bugs, Comments, Upvote, Downvote, Tags
import ast

bcrypt = Bcrypt(app)

@app.route('/')
def home():
    return render_template('Index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('Dashboard.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=password, confirmed=False)
        
        email = User.query.filter_by(email=form.email.data).first()
        if email:
            flash ("⚠️ The Email Address Already Exists! Choose Another One", "danger")
            return redirect(url_for("register"))
        
        else:
            db.session.add(new_user)
            db.session.commit()

            token = generate_confirmation_token(new_user.email)
            confirm_url = url_for('confirm_email', token=token, _external=True)
            html = render_template('Activation.html', confirm_url=confirm_url)
            subject = "[PITCH DECK] Confrim Your Email Address"
            send_email(new_user.email, subject, html)

            return redirect(url_for("email_verification_sent"))

    return render_template('Register.html', form=form)

@app.route('/confirm/<token>')
def confirm_email(token):
    if User.confirmed==1:
        flash('✅ Account Already Confirmed! You Can Log In.', 'success')
        return redirect(url_for('login'))

    email = confirm_token(token)
    user = User.query.filter_by(email=email).first_or_404()

    if user.email == email:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('✅ You Have Successfully Confirmed Your Email Address. You Can Now Log In. Thanks!', 'success')
    else:
        flash('⚠️ The Confirmation Link Is Invalid Or Has Expired.', 'danger')

    return redirect(url_for('login'))

@app.route('/sent')
def email_verification_sent():
    if User.confirmed==1:
        flash('✅ You Can Now Log In!', 'success')
        return redirect(url_for('login'))
    else:
        flash('✅ Registration Successful! A Confirmation Link Has Been Sent To The Registered Email Address.', 'success')
        return redirect(url_for('register'))

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.confirmed ==0:
            flash('⚠️ Your Acount Is Not Activated! Please Check Your Email Inbox And Click The Activation Link We Sent To Activate It', 'danger')
            return render_template('Login.html', form=form)

        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        if user and not bcrypt.check_password_hash(user.password, request.form['password']):
            flash('⚠️ Invalid Password!', 'danger')
            return render_template('Login.html', form=form)

        if not user:
            flash('⚠️ Account Does Not Exist!', 'danger')
            return render_template('Login.html', form=form)

    return render_template('Login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    user = current_user
    user.authenticated = False
    logout_user()
    # redirecting to home page
    return redirect(url_for('home'))

@app.route('/bug/add', methods = ['GET', 'POST'])
@login_required
def add_bug():
    form = CreatePostForm()
    if form.validate_on_submit():
        bug = Bugs(form.title.data, form.description.data)
        bug.title = form.title.data
        bug.description = form.description.data
        tag_string = form.tags.data
        tags = tag_string.split(",")
        for tag in tags:
            bug_tag = add_tags(tag)
            print (bug_tag)
            bug.tags.append(bug_tag)
        
        bug.author = current_user._get_current_object().id

        db.session.add(bug)
        db.session.commit()
        flash ('✅ New Bug Post Successfully Created!', 'success')
        return redirect(url_for('add_bug'))
        
    return render_template("Add Bug.html", form = form)

def add_tags(tag):
    existing_tag = Tags.query.filter(Tags.name == tag.lower()).one_or_none()
    """if it does return existing tag objec to list"""
    if existing_tag is not None:
        return existing_tag
    else:
       new_tag = Tags()
       new_tag.name = tag.lower()
       return new_tag

@app.route('/bugs')
def bugs():
    bugs = Bugs.query.all()
    return render_template('Bugs.html', bugs = bugs)

@app.route('/bug-details')
def bugs_details():
    return render_template('Bug Details.html')

@app.route('/profile')
def profile():
    return render_template('Profile.html')

# NOTE: Routes by ismailpervez below
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')

@app.errorhandler(500)
def not_found(e):
    return render_template('500.html')

# get the user - for dashboard
@app.route('/profile/<username>')
def get_public_user(username):
    # username, email, profile_pic
    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('not_found'))

    else:

        return render_template('Profile.html', user=user)

# update the user
@app.route('/update/user/<username>', methods=['GET', 'PUT'])
@login_required
def update_user(username):
    user = User.query.filter_by(username=username).first()
    # get the form
    # form = PostBug()
    # form = CreatePostForm()
    if not user:
        return "not found"

    else:
        if request.method == 'GET':
            '''
            form.data.username = user.username
            form.data.email = user.email
            '''
            return "update user page"

        elif request.method == 'PUT':
            '''
            user.username = form.data.username
            user.email = form.data.email
            db.session.commit()
            '''
            return "updated user"

# delete user
@app.route('/delete/user/<username>', methods=['DELETE'])
@login_required
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return "not found"

    else:
        db.session.delete(user)
        db.session.commit()

        return "user deleted"

# get all posts - from latest
@app.route('/all/posts')
def get_posts():
    posts = Bugs.query.all()
    return render_template('Bugs.html', bugs=posts)

# get full post
@app.route('/post/<post_id>')
def get_post(post_id):
    post = Bugs.query.get(post_id)

    if not post:
        return redirect(url_for('not_found'))

    else:
        return render_template('Bug Details.html', bug=post)

# update post
@app.route('/update/post/<post_id>', methods=['GET', 'PUT'])
@login_required
def update_post(post_id):
    post = Bugs.query.get(post_id)
    form = UpdatePostForm()
    if not post:
        return render_template('404.html')

    else:
        if request.method == 'GET':
            
            form.title.data = post.title
            form.description.data = post.description
            # form.tags.data = ' '.join(ast.literal_eval(post.tags))
            form.status.data = post.status
            
            return render_template('Update Bug.html', form=form)

        elif request.method == 'PUT':
            
            post.title = form.title.data
            post.description = form.description.data
            post.tags = str(post.tags.data.split(' '))
            # post.status = form.status.data

            db.session.commit()
            
            return render_template('Update Bug.html', form=form)

# delete post
@login_required
@app.route('/delete/post/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = Bugs.query.get(post_id)

    if not post:
        return render_template('404.html')

    else:
        db.session.delete(post)
        db.session.commit()

        return render_template('Dashboard.html')

# create comment
@app.route('/create/comment/<post_id>', methods=['GET','POST'])
@login_required
def post_comment(post_id):
    # form = CreateComment()
    if request.method == 'GET':
        '''
        if current_user:
            return render_template('Bug Details.html', form=form)
        
        else:
            return render_template('Bug Details.html')
        '''

    elif request.method == 'POST':
        '''
        if form.validate_on_submit():
            comment = Comments(
                comment=form.content.data,
                user_id=current_user.id,
                bug_id=post_id
            )

            db.session.add(comment)
            db.session.commit()
        '''
        return render_template('Bug Details.html', form=form) 

# update comment - NOTE: i don't think its important to implement

# delete comment
@app.route('/delete/comment/<comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = Comments.query.get(comment_id)

    if not comment:
        return render_template('404.html')

    else:
        db.session.delete(comment)
        db.session.commit()

        return render_template('Bug Details.html')

# upvote post
@app.route('/upvote/post/<post_id>')
@login_required
def like_post(post_id):
    post = Bugs.query.get(post_id)

    if not post:
        return "post not found"

    else:
        like = Upvote.query.filter_by(user_id=current_user.id, post_id=post_id).first()

        if like:
            # dislike the post
            db.session.delete(like)
            db.session.commit()

            return render_template('Bug Details.html')

        else:
            like = Upvote(
                user_id=current_user.id,
                post_id=post_id
            )

            db.session.add(like)
            db.session.commit()

        return render_template('Bug Details.html')

# downvote post
@app.route('/downvote/post/<post_id>')
@login_required
def dislike_post(post_id):
    post = Bugs.query.get(post_id)

    if not post:
        return "post not found"

    else:
        dislike = Downvote.query.filter_by(user_id=current_user.id, post_id=post_id).first()

        if dislike:
            # dislike the post
            db.session.delete(dislike)
            db.session.commit()

            return render_template('Bug Details.html')
        else:
            dislike = Downvote(
                user_id=current_user.id,
                post_id=post_id
            )

            db.session.add(dislike)
            db.session.commit()

        return render_template('Bug Details.html')

# upvote comment
@app.route('/upvote/comment/<comment_id>')
@login_required
def like_comment(comment_id):
    post = Bugs.query.get(comment_id)

    if not post:
        return "post not found"

    else:
        like = Upvote.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

        if like:
            # dislike the post
            db.session.delete(like)
            db.session.commit()

            return render_template('Bug Details.html')

        else:
            like = Upvote(
                user_id=current_user.id,
                comment_id=comment_id
            )

            db.session.add(like)
            db.session.commit()

        return render_template('Bug Details.html')

# downvote comment
@app.route('/downvote/comment/<comment_id>')
@login_required
def dislike_comment(comment_id):
    post = Bugs.query.get(comment_id)

    if not post:
        return "post not found"

    else:
        dislike = Downvote.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

        if dislike:
            # dislike the post
            db.session.delete(dislike)
            db.session.commit()

            return render_template('Bug Details.html')

        else:
            dislike = Downvote(
                user_id=current_user.id,
                comment_id=comment_id
            )

            db.session.add(dislike)
            db.session.commit()

        return render_template('Bug Details.html')
