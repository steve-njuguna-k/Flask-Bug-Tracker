from app import app, bcrypt
from flask import render_template, request, flash
from app.forms import RegisterForm, LoginForm, UpdateBug

@app.route('/')
def home():
    return render_template('Index.html')

@app.route('/bugs')
def posts():
    # query all bugs
    # format bugs in a JSON serializable format
    return render_template('posts.html')

@app.routes('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'POST':
        if form.validate_on_submit():
            first_name = form.first_name.data
            last_name = form.last_name.data
            username = form.username.data
            email = form.email.data
            password = form.password.data
            
            # encrypt the password
            hashed_password = bcrypt.generate_password_hash(password)

            # create a new user
            # store to db

            flash('registration successsful', 'success')

            return render_template('register.html')

        else:
            flash('registration not complete', 'danger')
            return render_template('register.html')

# login already created

# get full bugs details
@app.route('/post/<post_id>')
def get_full_post(post_id):
    post = 'Post.query.get(post_id)'
    if not post:
        # redirect to 404 page
        pass

    else:
        # format the post in JSON serializable format
        # return post
        return render_template('post.html', post='post')

@app.route('/update/post/<post_id>', methods=['GET', 'POST'])
# @login_required
def update_post(post_id):
    form = UpdateBug()
    '''
    post = Post.query.get(post_id)
    if post.author != current_logged_in_user:
        flash('unauthorized to complete action', 'danger')

    else:
        if request.method == 'GET':
            form.title.data = post.title
            form.description.data = post.description
            form.tags.data = ' '.join(ast.literal_eval(tags))

            return render_template('updatepost.html', form=form)

        elif request.method == 'POST':
            title = form.title.data
            description = form.description.data
            tags = str(form.tags.data.split(' '))

            db.session.commit()

            flash('post updated successfully', 'success')

            return render_template('updatepost.html')

    '''
    return ''

@app.route('/delete/post/<post_id>')
# @login_required
def delete_post():
    '''
    post = Post.query.get(post_id)
    if post.author != current_logged_in_user:
        flash('unauthorized to complete action', 'danger')
        return render_template('inde.html')

    else:
        flash('post deleted successfully')
        return redirect(url_for(get_user))
    '''
    return ''

@app.route('/change-status/post/<post_id>')
def change_post_status(post_id):
    '''
    post = Post.query.get(post_id)
    
    '''