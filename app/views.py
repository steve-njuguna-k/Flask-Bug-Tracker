import datetime
from telnetlib import DO

from sqlalchemy import desc
from app import app
from flask import render_template, flash, redirect, request, url_for
from .token import confirm_token, generate_confirmation_token
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_user, logout_user, login_required
from .email import send_email
from .forms import AddCommentsForm, EditCommentsForm, EditProfileForm, LoginForm, RegisterForm, CreatePostForm, UpdatePostForm
from .models import db, User, Bugs, Comments, CommentUpvote, CommentDownvote, Tags, PostUpvote, PostDownvote
import ast

from app import models

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
    comment = Comments.query.filter_by(id = id).first()

    return render_template('Bug Details.html', form = form, bug = bug, bugs = bugs, comments = comments, comment = comment)

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
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    bugs = Bugs.query.filter_by(author = current_user._get_current_object().id).all()
    return render_template('Dashboard.html', bugs = bugs)

@app.route('/profile')
@login_required
def profile():
    bugs = Bugs.query.filter_by(author = current_user._get_current_object().id).all()
    user = current_user._get_current_object()
    return render_template('Profile.html', bugs = bugs, user = user)

@app.route('/author/<int:id>')
@login_required
def author(id):
    user = User.query.get(id)
    bugs = Bugs.query.filter_by(author = user.id).all()
    return render_template('Profile.html', user = user, bugs = bugs)

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

@app.route('/bug/<int:id>/comment/<int:comment_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_comment(id, comment_id):
    comment = Comments.query.filter_by(id = comment_id).first()
    bug = Bugs.query.get_or_404(id)

    if not bug:
        flash('⚠️ Comment Does Not Exist!', 'danger')
        return redirect(url_for('bug_details', id = bug.id))

    elif current_user.id != comment.author and current_user.id != comment.bug_id:
        flash('⚠️ You Are Not Authorized To Delete This Comment! You Are Not The Post Author or Comment Author.', 'danger')
        return redirect(url_for('bug_details', id = bug.id))
    
    else:
        db.session.delete(comment)
        db.session.commit()
        flash ('✅ The Comment Has Been Successfully Deleted!', 'success')
        
    return render_template('Bug Details.html', id = bug.id, bug = bug)

# upvote comment
@app.route('/bug/<int:id>/comment/<int:comment_id>/like')
@login_required
def like_comment(id, comment_id):
    bug = Bugs.query.get(id)
    comments = Comments.query.filter_by(bug_id = id).order_by(desc(Comments.date_published)).all()

    if not bug:
        return "post not found"

    else:
        like = CommentUpvote.query.filter_by(user_id=current_user.id, bug_id = bug.id, comment_id=comment_id).first()

        if like:
            flash('⚠️ You Can Only Like Once!', 'danger')
            return render_template('Bug Details.html', bug = bug, comments = comments)

        else:
            like = CommentUpvote(
                user_id=current_user.id,
                bug_id = bug.id,
                comment_id = comment_id
            )

            db.session.add(like)
            db.session.commit()

            flash ('✅ You Have Liked That Comment!', 'success')
            return render_template('Bug Details.html', bug = bug, comments = comments)

# downvote comment
@app.route('/bug/<int:id>/comment/<int:comment_id>/dislike')
@login_required
def dislike_comment(id, comment_id):
    bug = Bugs.query.get(id)
    comments = Comments.query.filter_by(bug_id = id).order_by(desc(Comments.date_published)).all()

    if not bug:
        return "post not found"

    else:
        like = CommentDownvote.query.filter_by(user_id=current_user.id, bug_id = bug.id, comment_id=comment_id).first()

        if like:
            flash('⚠️ You Can Only Dislike Once!', 'danger')
            return render_template('Bug Details.html', bug = bug, comments = comments, bug_id = id, comment_id = comment_id)

        else:
            like = CommentDownvote(
                user_id=current_user.id,
                bug_id = bug.id,
                comment_id = comment_id
            )

            db.session.add(like)
            db.session.commit()

            flash ('✅ You Have Disliked That Comment!', 'success')
            return render_template('Bug Details.html', bug = bug, comments = comments, bug_id = id, comment_id = comment_id)

@app.route('/bug/<int:id>/like')
@login_required
def like_post(id):
    bug = Bugs.query.get(id)
    comments = Comments.query.filter_by(bug_id = id).order_by(desc(Comments.date_published)).all()

    if not bug:
        return "post not found"

    else:
        like = PostUpvote.query.filter_by(user_id=current_user.id, bug_id = bug.id).first()

        if like:
            flash('⚠️ You Can Only Like Once!', 'danger')
            return render_template('Bug Details.html', bug = bug, comments = comments)

        else:
            like = PostUpvote(
                user_id=current_user.id,
                bug_id = bug.id
            )

            db.session.add(like)
            db.session.commit()

            flash ('✅ You Have Liked That Post!', 'success')
            return render_template('Bug Details.html', bug = bug, comments = comments)

# downvote comment
@app.route('/bug/<int:id>/dislike')
@login_required
def dislike_post(id):
    bug = Bugs.query.get(id)
    comments = Comments.query.filter_by(bug_id = id).order_by(desc(Comments.date_published)).all()

    if not bug:
        return "post not found"

    else:
        like = PostDownvote.query.filter_by(user_id=current_user.id, bug_id = bug.id).first()

        if like:
            flash('⚠️ You Can Only Dislike Once!', 'danger')
            return render_template('Bug Details.html', bug = bug, comments = comments, bug_id = id)

        else:
            like = PostDownvote(
                user_id=current_user.id,
                bug_id = bug.id
            )

            db.session.add(like)
            db.session.commit()

            flash ('✅ You Have Disliked That Post!', 'success')
            return render_template('Bug Details.html', bug = bug, comments = comments, bug_id = id)

@app.route('/update/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    user = current_user._get_current_object()

    if form.validate_on_submit():        
        user.username = form.username.data
        user.email = form.email.data
        user.bio = form.bio.data
        user.profession = form.profession.data
        user.country = form.country.data
        user.website_link = form.website_link.data
        user.github_link = form.github_link.data
        user.twitter_link = form.twitter_link.data
        user.linkedin_link = form.linkedin_link.data
        user.facebook_link = form.facebook_link.data
        user.codewars_link = form.codewars_link.data

        db.session.add(user)
        db.session.commit()

        flash ('✅ Your Profile Info Has Been Successfully Updated!', 'success')
        return redirect(url_for('edit_profile', user = user, form = form))
    
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.bio.data = user.bio
        form.profession.data = user.profession
        form.country.data = user.country
        form.website_link.data = user.website_link
        form.github_link.data = user.github_link
        form.twitter_link.data = user.twitter_link
        form.linkedin_link.data = user.linkedin_link
        form.facebook_link.data = user.facebook_link
        form.codewars_link.data = user.codewars_link

    return render_template('Edit Profile.html', user = user, form = form)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')

@app.errorhandler(500)
def not_found(e):
    return render_template('500.html')