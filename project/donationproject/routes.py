import secrets
import os
from PIL import Image
from flask import render_template,flash,redirect,url_for,request,abort
from donationproject import app,db,bcrypt,mail
from donationproject.form import RegisterForm,LoginForm,UpdateAccountForm,EventForm,RequestResetForm,ResetPasswordForm
from donationproject.models import user,donation,event
from flask_login import login_user,current_user,logout_user,login_required
from flask_mail import Message

@app.route("/")
def home():
    page=request.args.get('page',1,type=int)
    events=event.query.order_by(event.creation_date.desc()).paginate(page=page,per_page=3)
    return render_template("homepage.html",events=events)

@app.route("/register", methods=['POST', 'GET'])

def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        print("Form validation successful!")  # Add a print statement to check if form validation is successful
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        userdata = user(username=form.username.data, email=form.email.data, password=hashed)
        db.session.add(userdata)
        db.session.commit()
        flash("Your account is created and you can login now!", 'success')
        return redirect(url_for('login'))  # This is where the redirection should happen
    else:
        print("Form validation failed!")  # Add a print statement to check if form validation fails
    return render_template("register.html", title="Register", form=form)


@app.route("/login",methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
         return redirect(url_for('home'))
    form=LoginForm()
    if form.validate_on_submit():
            userdata=user.query.filter_by(email=form.email.data).first()
            if(userdata and bcrypt.check_password_hash(userdata.password,form.password.data)):
                 login_user(userdata,remember=form.remember.data)
                 next_page=request.args.get('next')
                 return redirect(next_page) if next_page else  redirect(url_for("home"))
            else:     
                flash('check email and password',"danger")
    return render_template("login.html",title="Login",form=form)

@app.route("/logout")
def logout():
     logout_user()
     return redirect(url_for("home"))


def save_picture(form_picture):
    random_hex=secrets.token_hex(8)
    _,f_ext=os.path.splitext(form_picture.filename)
    picture_fn=random_hex+f_ext
    picture_path=os.path.join(app.root_path,'static/pictures',picture_fn)
    output_size=(125,125)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

@app.route("/account",methods=['POST','GET'])
@login_required
def account():
    form =UpdateAccountForm()
    if form.validate_on_submit():
          if form.picture.data:
               picture_file=save_picture(form.picture.data)
               current_user.image_file=picture_file
               
          current_user.username=form.username.data
          current_user.email=form.email.data
          db.session.commit()
          flash("your account is updated :","success")
          return redirect(url_for('account'))
    elif request.method =='GET':
         form.username.data=current_user.username
         form.email.data=current_user.email

    image_file=url_for("static",filename="pictures/"+current_user.image_file)
    return render_template("account.html",form=form,image_file=image_file)


@app.route("/events",methods=['POST','GET'])
@login_required
def new_event():
    
    form=EventForm()
    if current_user.username=="zerobear" or current_user.username=="zara":
        if form.validate_on_submit():
            New_event=event(title=form.title.data,author=current_user.username,organization=form.orgname.data,description=form.description.data, user_id=current_user.id)
            db.session.add(New_event)
            db.session.commit()
            flash('your event is created','success')
            return redirect(url_for('home'))
        return render_template('create_event.html',form=form)
    else:
        # Redirect to the events section of the page
        return redirect(url_for('home', _anchor='event'))
         


@app.route("/events/<int:event_id>", methods=['POST', 'GET'])
@login_required 
def event_page(event_id):
    page = request.args.get('page', 1, type=int)
    event_data = event.query.get_or_404(event_id)
    events = event.query.paginate(page=page, per_page=3)  # Assuming 5 events per page
    return render_template("event.html", event=event_data, events=events)



@app.route("/events/<int:event_id>/update",methods=['POST','GET'])
@login_required
def update_event(event_id):
    event_data = event.query.get_or_404(event_id)
    if event_data.author != current_user.username:
         abort(403)
    form= EventForm()
    if form.validate_on_submit():
         event_data.title=form.title.data
         event_data.orgname=form.orgname.data
         event_data.description=form.description.data
         db.session.commit()
         flash ("your post is updated ","success")
         return redirect(url_for('event_page',event_id=event_data.id))
    elif request.method =='GET':
        form.title.data=event_data.title
        form.orgname.data =event_data.organization
        form.description.data =event_data.description
    
    return render_template('create_event.html',form=form)


@app.route("/events/<int:event_id>/delete", methods=['POST'])
@login_required
def delete_event(event_id):
    event_data = event.query.get_or_404(event_id)
    if current_user.username != event_data.author:
        abort(403)
    db.session.delete(event_data)
    db.session.commit()
    flash("Your post is Deleted", "success")
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_events(username):
    page = request.args.get('page', 1, type=int)
    user_data = user.query.filter_by(username=username).first_or_404()
    event_data = event.query.filter_by(author=user_data.username)\
        .order_by(event.creation_date.desc())\
        .paginate(page=page, per_page=3)
    return render_template('user_events.html', events=event_data, user=user_data)

def send_reset_email(user):
    token=user.get_reset_token()
    msg=Message('Password Reset Request',sender="saboorabdul627@gmail.com",recipients=[user.email])
    msg.body=f''' to Rese your password visit the following link :
http://127.0.0.1:5000/{url_for('reset_token',token=token,external=True)}   
if you did not request reset then ignore this email'''
    mail.send(msg)


@app.route("/reset_password",methods=['POST','GET'])
def reset_request():
    if current_user.is_authenticated:
         return redirect(url_for('home'))
    form=RequestResetForm()
    if form.validate_on_submit():
        user_data=user.query.filter_by(email=form.email.data).first()
        send_reset_email(user_data)
        flash("check your email to reset password !","info")
        return redirect(url_for('login'))
    return render_template('reset_request.html',form=form)

@app.route("/reset_password/<token>",methods=['POST','GET'])
def reset_token(token):
    if current_user.is_authenticated:
         return redirect(url_for('home'))
    user_data=user.verify_reset_token(token)
    if user_data is None:
        flash("That is an Inavalid token the link is Expired ",'warning')
        return redirect(url_for('reset_request'))
    form=ResetPasswordForm()
    if form.validate_on_submit():
        print("Form validation successful!")  # Add a print statement to check if form validation is successful
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user_data.password=hashed
        db.session.commit()
        flash("Your Password is reset !", 'success')
        return redirect(url_for('login')) 
    return render_template('reset_token.html',form=form)





