# encoding:utf-8
from flask import Flask, url_for, render_template, flash
from flask import request, redirect, session
from functools import wraps
from wtforms import StringField, Form, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '312624'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.secret_key = '123456'

mysql = MySQL(app)


def is_logged_in(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('尚未登陆，请登陆', 'danger')
            return redirect(url_for('login'))
    return wrapped


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/blogs')
@is_logged_in
def blogs():
    cur = mysql.connection.cursor()
    result = cur.execute("select * from articles")
    blogs = cur.fetchall()

    if result:
        return render_template('blog.html', blogs=blogs)
    else:
        msg = '没有文章'
        return render_template('blog.html', msg=msg)


@app.route('/blog/<string:id>')
@is_logged_in
def blog(id):
    cur = mysql.connection.cursor()
    result = cur.execute("select * from articles where id = %s", [id])
    blog = cur.fetchone()
    return render_template('blogs.html', id=id, blog=blog)


class RegisterForm(Form):
    name = StringField('姓名', [validators.Length(min=1, max=50)])
    username = StringField('用户名', [validators.Length(min=4, max=25)])
    email = StringField('电子邮箱', [validators.Length(min=6, max=50)])
    password = PasswordField('登录密码', [validators.DataRequired(), validators.EqualTo('confirm', message='Password not match!')])
    confirm = PasswordField('确认登录密码')


class ArticleForm(Form):
    title = StringField('标题', [validators.Length(min=1, max=50)])
    body = TextAreaField('文章内容', [validators.Length(min=1)])


@app.route('/add_blog', methods=['GET', 'POST'])
@is_logged_in
def add_blog():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.title.data

        cur = mysql.connection.cursor()
        cur.execute("insert into articles(title, body, author) values(%s, %s, %s)", (title, body, session['username']))
        mysql.connection.commit()
        cur.close()

        flash('文章创建成功', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_blog.html', form=form)


@app.route('/edit_blog/<string:id>', methods=['POST', 'GET'])
@is_logged_in
def edit_blog(id):
    cur = mysql.connection.cursor()
    result = cur.execute("select * from articles where id = %s", [id])
    blog = cur.fetchone()
    cur.close()
    form = ArticleForm(request.form)
    form.title.data = blog['title']
    form.body.data = blog['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        cur = mysql.connection.cursor()
        app.logger.info(title)
        cur.execute("update articles set title=%s, body=%s where id=%s", (title, body, id))
        mysql.connection.commit()
        cur.close()

        flash("文章已更新", 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_blog.html', form=form)


@app.route('/delete_blog/<string:id>', methods=['POST'])
@is_logged_in
def delete_blog(id):
    cur = mysql.connection.cursor()
    cur.execute("delete from articles where id=%s", [id])
    mysql.connection.commit()
    cur.close()

    flash('文章已经删除', 'success')
    return redirect(url_for('dashboard'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()
        cur.execute("insert into users(name, email, username, password) values (%s, %s, %s, %s)", (name, email, username, password))
        mysql.connection.commit()
        cur.close()
        flash('你已经成功注册', 'success')
        redirect(url_for('register'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()
        result = cur.execute("select * from users where username = %s ", [username])

        if result:
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(password_candidate, password):
                app.logger.info('密码正确')
                session['logged_in'] = True
                session['username'] = username
                flash('你已经成功登陆', 'success')
                return redirect(url_for('dashboard'))

            else:
                app.logger.info('密码不正确')
                error = '登陆失败，密码不正确'
                return render_template('login.html', error=error)

        else:
            app.logger.info('账号不存在')
            error = '账号不存在'
            return render_template('login.html', error=error)

        cur.close()

    return render_template('login.html')


@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("select * from articles")
    articles = cur.fetchall()

    if result:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = '没有文章'
        return render_template('dashboard.html', msg=msg)
    cur.close()


@app.route('/logout')
def logout():
    session.clear()
    flash('您已经成功注销', 'success')
    return redirect(url_for('hello_world'))


if __name__ == '__main__':
    app.run(debug=True)

