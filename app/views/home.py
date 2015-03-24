from flask import Blueprint,request, redirect,url_for,render_template,flash, abort
from flask.ext.login import login_user, login_required, current_user, logout_user
from app.models import User, RevokedToken as RT
from app.forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
from app.utils import ts, send_confirm_mail, send_reset_password_mail

home = Blueprint('home',__name__)

@home.route('/')
def index():
    return redirect(url_for('course.index'))

@home.route('/signin/',methods=['POST','GET'])
def signin():
    if current_user.is_authenticated():
        return redirect(request.args.get('next') or url_for('home.index'))
    form = LoginForm()
    error = ''
    if form.validate_on_submit():
        user,status = User.authenticate(form['username'].data,form['password'].data)
        remember = form['remember'].data
        print(remember)
        if user and status:
            #validate uesr
            login_user(user, remember=remember)
            flash('Logged in')
            return redirect(request.args.get('next') or url_for('home.index'))
        elif not user.confirmed:
            '''没有确认邮箱的用户'''
            return 'Please confirm your email!<a href=%s>resend email</a>'%url_for('.confirm_email',
                    email=user.email,
                    action='send')
            '''需要一个发送确认邮件的页面'''
            return render_template('require-confirm.html')
        error = '用户名或密码错误'
    print(form.errors)
    return render_template('signin.html',form=form, error=error)


@home.route('/signup/',methods=['GET','POST'])
def signup():
    if current_user.is_authenticated():
        return redirect(request.args.get('next') or url_for('home.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user = User(username=username, email=email,password=password)
        send_confirm_mail(user.email)
        user.save()
        flash('registered')
        #login_user(user)
        '''注册完毕后显示一个需要激活的页面'''
        return 'Please confirm your email address in your email.'
    if form.errors:
        print(form.errors)
    return render_template('signup.html',form=form)


@home.route('/confirm-email/')
def confirm_email():
    if current_user.is_authenticated():
        return redirect(request.args.get('next') or url_for('home.index'))
    action = request.args.get('action')
    if action == 'confirm':
        token = request.args.get('token')
        try:
            email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        except:
            abort(404)

        user = User.query.filter_by(email=email).first_or_404()
        user.confirm()
        flash('Your email has been confirmed')
        login_user(user)
        return redirect(url_for('home.index'))
    elif action == 'send':
        email = request.args.get('email')
        user = User.query.filter_by(email=email).first_or_404()
        if not user.confirmed:
            send_confirm_mail(email)
        return 'Confirm url sent'
    else:
        return 404


@home.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.index'))


@home.route('/reset-password/', methods=['GET','POST'])
def forgot_password():
    ''' 忘记密码'''
    if current_user.is_authenticated():
        return redirect(request.args.get('next') or url_for('home.index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form['email'].data
        user = User.query.filter_by(email=email).first()
        if not user:
            return 'Email %s has not been registered'%email
        send_reset_password_mail(email)
        return 'Reset password mail sent.'
    return render_template('forgot-password.html')

@home.route('/reset-password/<string:token>/', methods=['GET','POST'])
def reset_password(token):
    '''重设密码'''
    if current_user.is_authenticated():
        return redirect(request.args.get('next') or url_for('home.index'))
    if RT.query.get(token):
        return 'Token has been used'
    form = ResetPasswordForm()
    if form.validate_on_submit():
        RT.add(token)
        try:
            email = ts.loads(token, salt="password-reset-key", max_age=86400)
        except:
            return 'Your token has expired.'
        user = User.query.filter_by(email=email).first_or_404()
        password = form['password'].data
        user.set_password(password)
        flash('Password Changed')
        return redirect(url_for('home.signin'))
    return render_template('reset-password.html',form=form)



@home.route('/report-bug/')
def report_bug():
    ''' 报bug表单 '''

    return render_template('report-bug.html')
