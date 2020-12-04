from flask import Blueprint
from flask import request
from flask import redirect   
from flask import render_template
from flask import session
from flask.helpers import url_for
from Project.models import db
from Project.models import Users
from random import *


sign_routes = Blueprint('sign_routes', __name__)


# '/signup'
@sign_routes.route('/signup', methods=['GET','POST'])  
def register():
    if request.method == "POST":
        result = request.form
        print(dict(result))
        user = Users.query.get(result['email']) or Users(id = result['email'])
        user.password = result['password']
        user.movie = result['movie']
        db.session.add(user)  
        db.session.commit()
        return redirect(url_for('sign_routes.login'))
    else:
        return render_template('signup.html')


# '/login'
@sign_routes.route('/login', methods=['GET','POST'])  
def login():
    session.pop('email', None)
    session.pop('password', None)
    if request.method == "POST":
        result = request.form
        print(dict(result))

        email = Users.query.with_entities(Users.id).filter(Users.id == result['email']).first()
        password = Users.query.with_entities(Users.password).filter(Users.id == result['email']).first()        
        print(email, password)

        if (email[0] == result['email']) & (password[0] == result['password']):
            session['email'] = result['email']
            session['password'] = result['password']

            return redirect(url_for('main_routes.main'))

    return render_template('login.html')


# '/signout'
@sign_routes.route('/signout', methods=['GET','POST'])  
def register():
    if request.method == "POST":
        result = request.form
        print(dict(result))
        user = Users.query.get(result['email']) or Users(id = result['email'])
        user.password = result['password']
        user.movie = result['movie']
        db.session.add(user)  
        db.session.commit()
        return redirect(url_for('sign_routes.login'))
    else:
        return render_template('signup.html')