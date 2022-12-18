import hashlib
from datetime import datetime
import pyotp
from flask import url_for, render_template, request, redirect, send_from_directory, flash, session
from __init__ import app
import forms
from repo import *

repo = Repo(host=app.config['HOST'], user=app.config['USER'], password=app.config['PASSWORD'], db=app.config['DB'])


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(error)


@app.route("/")
def index():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    return render_template('index.html', title="Главная")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if session.get('loggedin'):
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = repo.login_user_safe(form.login.data, hashlib.md5(form.password.data.encode('utf-8')).hexdigest())
        if user:
            if user[6]:
                if pyotp.TOTP(user[7]).verify(form.otp.data):
                    flash('Вы авторизовались!')
                    session['loggedin'] = True
                    session['id'] = user[0]
                    session['username'] = user[1]
                    session['role'] = user[4]
                else:
                    flash('Неправильный OTP')
            else:
                flash('Вы авторизовались!')
                session['loggedin'] = True
                session['id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[4]
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль!')
    return render_template('login.html', title='Авторизация', form=form)


@app.route("/2fa", methods=['GET', 'POST'])
def fa():
    if session.get('loggedin'):
        form = forms.FaForm()
        user = repo.get_user(session.get('username'))

        if form.validate_on_submit():
            if pyotp.TOTP(user[7]).verify(form.otp.data):
                if repo.toggle_2fa(user[0]):
                    flash('Двойная аутентификация включена')
                else:
                    flash('Двойная аутентификация выключена')
            else:
                flash('Неправильный OTP')
            return redirect(url_for('fa'))
        return render_template("2fa.html", title='Двухфакторная аутентификация', enable=user[6], secret=user[7], form=form, url=pyotp.totp.TOTP(user[7]).provisioning_uri(name=session.get('username'), issuer_name='Маникюрный салон'))
    else:
        flash('Требуется аутентификация')
        return redirect(url_for('index'))


@app.route('/2fa/generate')
def generate():
    if session.get('loggedin'):
        if repo.add_secret_key_to_user(session.get('username'), pyotp.random_base32()):
            flash('Ключ сгенерирован')
        else:
            flash('Ключ уже имеется')
        return redirect(url_for('fa'))
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))


@app.route("/users", methods=['GET', 'POST'])
def users():
    form = forms.UserForm()
    form.role.choices = repo.get_roles()
    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            if not repo.add_user(form.username.data, hashlib.md5(form.password.data.encode('utf-8')).hexdigest(), form.fio.data, form.role.data):
                flash('Пользователь уже существует')
            else:
                app.logger.warning(f'User {form.username.data} with role id {form.role.data} was added by {session.get("username")}')
            return redirect(url_for('users'))
    return render_template('users.html', title='Пользователи', us=repo.get_all_users(), form=form)


@app.route("/users/rm/<int:id>")
def rm_user(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.hide_user_with_orders(id)
    return redirect(url_for('users'))


@app.route("/services", methods=['GET', 'POST'])
def services():
    form = forms.ServiceForm()
    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            repo.add_service(form.name.data, form.price.data, form.duration.data)
            return redirect(url_for('services'))
    return render_template('services.html', title="Услуги", ss=repo.get_services(), form=form)


@app.route("/services/rm/<int:id>")
def rm_service(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.remove_service(id)
    return redirect(url_for("services"))


@app.route("/services/hide/<int:id>")
def hide_service(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.hide_service(id)
    return redirect(url_for("services"))


@app.route("/clients", methods=['GET', 'POST'])
def clients():
    form = forms.ClientForm()
    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            if not repo.add_client_check(form.first_name.data, form.number.data):
                flash('Клиент уже существует')
            return redirect(url_for('clients'))

    return render_template('clients.html', title="Клиенты", clients=repo.get_clients(), form=form)


@app.route("/clients/rm/<int:id>")
def rm_client(id):
    if session.get('role') >= repo.ROLE_ADMINISTRATOR:
        if id:
            repo.remove_client(id)
    return redirect(url_for("orders"))


@app.route("/orders", methods=['GET', 'POST'])
def orders():
    form = forms.OrderForm()
    form.user.choices = repo.select_users()
    form.client.choices = repo.select_clients()
    form.services.choices = repo.select_services()

    filter_form = forms.FilterOrderForm()
    filter_form.user.choices = [("", "---")] + repo.select_users()
    filter_form.client.choices = [("", "---")] + repo.select_clients()

    if filter_form.validate_on_submit():
        return render_template('orders.html', title="Заказы", orders=repo.get_orders_sorted(filter_form.user.data, filter_form.client.data, filter_form.date1.data, filter_form.date2.data), form=form, filter_form=filter_form)

    return render_template('orders.html', title="Заказы", orders=repo.get_orders(), form=form, filter_form=filter_form)


@app.route('/orders/add', methods=['POST'])
def orders_add():
    form = forms.OrderForm()
    form.user.choices = repo.select_users()
    form.client.choices = repo.select_clients()
    form.services.choices = repo.select_services()
    if form.validate_on_submit() and session.get('role') == repo.ROLE_ADMINISTRATOR:
        if not repo.add_order_check(form.date.data, form.user.data, form.client.data, form.services.data):
            flash('Время занято')
    return redirect(url_for("orders"))


@app.route("/orders/rm/<int:id>")
def rm_order(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.remove_order(id)
    return redirect(url_for("orders"))


@app.route('/orders/<int:id>', methods=['GET', 'POST'])
def order(id):
    form = forms.StatusForm()
    form.status.choices = repo.select_statuses()
    if form.validate_on_submit():
        repo.change_order_status(id, form.status.data)
    if session.get('role') >= repo.ROLE_MASTER:
        return render_template('order.html', title='Заказ', o=repo.get_order(id)[0], services=repo.get_services_of_order(id), form=form)


@app.route('/schedule')
def schedule():
    return render_template('schedule.html', title='Расписание', orders=repo.get_user_orders(session.get('id')))


@app.route('/turnover')
def turnover():
    return repo.get_turnover()


@app.route('/robots.txt')
@app.route('/sitemap.xml')
@app.route('/favicon.ico')
@app.route('/style.css')
@app.route('/script.js')
@app.route('/qrcode.js')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
