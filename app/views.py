import datetime
from telnetlib import DO

from sqlalchemy import desc
from app import app
from flask import render_template, flash, redirect, request, url_for
from .token import confirm_token, generate_confirmation_token
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_user, logout_user, login_required
from .email import send_email
from .forms import AddCommentsForm, EditCommentsForm, LoginForm, RegisterForm, CreatePostForm, UpdatePostForm
from .models import db, User, Bugs, Comments, Upvote, Downvote, Tags
import ast

bcrypt = Bcrypt(app)

@app.route('/')
def home():
    return render_template('Index.html')

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
        return redirect(url_for('dashboard'))
        
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

@app.route('/bug/<int:id>/bug-details', methods = ['POST', 'GET'])
def bugs_details(id):
    form = AddCommentsForm()
    comments = Comments.query.filter_by(bug_id = id).order_by(desc(Comments.date_published)).all()
    bugs = Bugs.query.all()
    bug = Bugs.query.filter_by(id = id).first()

    return render_template('Bug Details.html', form = form, bug = bug, bugs = bugs, comments = comments)

# update post
@app.route('/bug/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def update_bug_post(id):
    bug = Bugs.query.get_or_404(id)
    form = UpdatePostForm(request.form)

    if form.validate_on_submit():        
        bug.title = form.title.data
        bug.description = form.description.data
        bug.bug_status = form.bug_status.data
        bug.author = current_user._get_current_object().id

        db.session.add(bug)
        db.session.commit()

        flash ('✅ The Bug Post Has Been Successfully Updated!', 'success')
        return redirect(url_for('update_bug_post', id = id))
    
    elif request.method == 'GET':
        form.title.data = bug.title
        form.description.data = bug.description
        form.bug_status.data = bug.bug_status

    if current_user.id != bug.author:
        flash('⚠️ You Are Not Authorized To Edit This Post! You Are Not The Author', 'danger')
        return redirect(url_for('bugs_details', id = id))
    
    return render_template('Edit Bug.html', bug = bug, form = form)

# delete post
@app.route('/bug/<int:id>/delete', methods=['POST', 'GET'])
@login_required
def delete_post(id):
    bug = Bugs.query.get_or_404(id)

    if current_user.id != bug.author:
        flash('⚠️ You Are Not Authorized To Delete This Post! You Are Not The Author', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(bug)
    db.session.commit()
    flash ('✅ The Bug Post Has Been Successfully Delete!', 'success')
    return redirect(url_for('dashboard', id = id))

@app.route('/dashboard')
@login_required
def dashboard():
    bugs = Bugs.query.filter_by(author = current_user._get_current_object().id)
    return render_template('Dashboard.html', bugs = bugs)

@app.route('/profile')
def profile():
    bugs = Bugs.query.filter_by(author = current_user._get_current_object().id)
    user = current_user._get_current_object()
    return render_template('Profile.html', bugs = bugs, user = user)

# create comment
@app.route('/bug/<int:id>/comment', methods = ['GET', 'POST'])
@login_required
def add_comment(id):
    bug_id = Bugs.query.get(id).id
    bug = Bugs.query.filter_by(id = id).first()
    form = AddCommentsForm()
    comment = form.comment.data
    author = current_user.id
    if form.validate_on_submit():
        comment = Comments(comment = comment, bug_id = bug_id, author = author)
        db.session.add(comment)
        db.session.commit()

        flash ('✅ Your Comment Has Been Successfully Added!', 'success')
        return redirect(url_for('add_comment', id = id))

    return render_template('Add Comment.html', form = form, bug = bug)

# update post
@app.route('/bug/<int:id>/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(id, comment_id):
    form = EditCommentsForm(request.form)
    comment = Comments.query.filter_by(id = comment_id).first()
    bug = Bugs.query.filter_by(id = id).first()

    if form.validate_on_submit():        
        comment.comment = form.comment.data
        comment.author = current_user._get_current_object().id

        db.session.add(comment)
        db.session.commit()

        flash ('✅ The Comment Has Been Successfully Updated!', 'success')
        return redirect(url_for('edit_comment', id = bug.id, form = form, comment_id = comment_id))
    
    elif request.method == 'GET':
        form.comment.data = comment.comment

    if current_user.id != comment.author:
        flash('⚠️ You Are Not Authorized To Edit This Comment! You Are Not The Author', 'danger')
        return redirect(url_for('bugs_details', id = bug.id, form = form))
    
    return render_template('Edit Comment.html', id = bug.id, form = form, bug = bug)

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
