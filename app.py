#!/usr/bin/env python2
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from base import Base, Category, SportItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Best sport items"

# Connect to Database and create database session
engine = create_engine('sqlite:///fakecatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
 google_id = credentials.id_token['sub']
   if result['user_id'] != google_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        Response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['google_id'] = google_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()


    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:' \
              '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id)
    return user
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    Access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Sport items Information
@app.route('/category/<int:category_id>/sport_item/JSON')
def categoryJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(SportItem).filter_by(category_id=category_id).all()
    return jsonify(SportItem=[i.serialize for i in items])


@app.route('/category/<int:category_id>/sport_item/<int:sport_item_id>/JSON')
def sportItemJSON(category_id, sport_item_id):
    Sport_Item = session.query(SportItem).filter_by(id=sport_item_id).one()
    return jsonify(Sport_Item=Sport_Item.serialize)


@app.route('/category/JSON')
def categorysJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])


# Show all category
@app.route('/')
@app.route('/category/')
def showCategory():
    category = session.query(Category).all()
    items = session.query(SportItem).order_by(SportItem.id.desc())
 if 'username' not in login_session:
        return render_template('catalog.html', category=category)
    else:
        return render_template('catalog.html', category=category)


# create a new catalog

@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategory'))
    else:
        return render_template('newcategory.html')


# Edit a Category


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCategory.user_id != login_session['user_id']:
        return '<script>function myFunction()' \
               ' {alert(\'Unable to authorize sign in.\');}</script><body onload=\'myFunction()\'\'>'
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showCategory'))
    else:
        return render_template('editcategory.html', category=editedCategory)


# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('Unable to authorize sign in.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('deletecategory.html', category=categoryToDelete)


# Show a category menu


@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/sport_item/', methods=['GET', 'POST'])
def showSportItem(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(Category.user_id)
    items = session.query(SportItem).all()
    if 'username' not in login_session:
        return render_template('catalog.html', items=items, category=category, creator=creator)
 else:
        return render_template('sportitem.html', items=items, category=category, creator=creator)


# Create a new sport item
@app.route('/category/<int:category_id>/sport_item/new/', methods=['GET', 'POST'])
def newSportItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction()" \
               "{alert('Unable to authorize sign in.');}</script><body onload='myFunction()''> "
    if request.method == 'POST':
        newItem = SportItem(name=request.form['name'], description=request.form['description'], price=request.form[
            'price'], category_id=category_id, user_id=category.user_id)
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % newItem.name)
        return redirect(url_for('showSportItem', category_id=category_id))
    else:
        return render_template('newsport_item.html', category_id=category_id)


# Edit a sport item


@app.route('/category/<int:category_id>/sport_item/edit', methods=['GET', 'POST'])
def editSportItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem=session.query(SportItem).filter_by(id=category_id).first()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['category']:
            editedItem.category = request.form['category']
        session.add(editedItem)
        session.commit()
        flash('Sport Item Successfully Edited')
        return redirect(url_for('showSportItem.html', category_id=category_id))
    else:
        return render_template('editsportitem.html', category_id=category_id, i=editedItem)

# Delete a sport item
@app.route('/category/<int:category_id>/sport_item/delete', methods=['GET', 'POST'])
def deleteSportItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(SportItem).filter_by(id=category_id).all()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction()" \
               "{alert('Unable to authorize delete.');}</script><body onload='myFunction()''> "
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Sport Item Successfully Deleted')
        return redirect(url_for('showSportItem', category_id=category_id))
    else:
         return render_template('deletesportItem.html', i=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)                                                                                                                                                             
