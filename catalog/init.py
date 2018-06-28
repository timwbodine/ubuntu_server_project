from models import Base, Cuisine, Recipe, User, Ingredient
from flask import Flask, jsonify, get_flashed_messages, request
from flask import redirect, url_for, flash, make_response, render_template
from flask import session as login_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import random
import string
from google.oauth2 import id_token
from google.auth.transport import requests as googleRequests
import sys
import codecs
import httplib2
import json
import requests
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
# use PoolListener to enforce foreign key constraints in sqlite
from sqlalchemy.interfaces import PoolListener
import time


class ForeignKeysListener(PoolListener):
    def connect(self, dbapi_con, con_record):
        db_cursor = dbapi_con.execute('pragma foreign_keys=ON')


sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)
# get google client id from client_secrets file
CLIENT_ID = json.loads(open('/var/www/catalog/catalog/client_secrets.json', 'r').read())[
    'web']['client_id']
# connect app to database
engine = create_engine(
    'sqlite:///recipes.db',
    listeners=[
        ForeignKeysListener()])
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


@app.route('/googledisconnect')
def googleDisconnect():
    # revoke google access token and purge login_session
    requests.post('https://accounts.google.com/o/oauth2/revoke',
                  params={'token': login_session['access_token']},
                  headers={'content-type':
                           'application/x-www-form-urlencoded'})
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['state']
    flash('You have been successfully logged out!', 'message')
    return redirect(url_for('all_recipes_handler'))


@app.route('/googletokenconnect', methods=['POST'])
def googleTokenConnect():
    try:
        # Verify state variable is valid.
        if request.args.get('state') != login_session['state']:
            response = make_response(
                json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        # grab idtoken from google response
        token = request.form['idtoken']
        # verify that token is valid for app, and retrieve id info:
        try:
            idinfo = id_token.verify_oauth2_token(
                token, googleRequests.Request(), CLIENT_ID)
        except ValueError as e:
            print(e)
            response = make_response(json.dumps(e), 500)
        print("step 1...")
        print(idinfo)
        if idinfo['iss'] not in [
            'accounts.google.com',
                'https://accounts.google.com']:
            print('wrong issuer!')
            raise ValueError('Wrong issuer.')
        # ID token is valid. Get the user's Google Account ID from the decoded
        # token.
        gplus_id = idinfo['sub']
        print("step 2...")
        stored_gplus_id = login_session.get('gplus_id')
        if login_session.get(
                'access_token') is not None and gplus_id == stored_gplus_id:
            print('step 3')
            response = make_response(
                json.dumps('user is already connected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            login_session['access_token'] = token
            return response
        # store decoded access token and unique google id in login_session
        # variable.
        login_session['access_token'] = token
        login_session['gplus_id'] = gplus_id
        # check if user_id exists in database already.  If so, retrieve
        # application-facing user data.
        user_id = getUserId(idinfo['email'])
        if user_id is not None:
            user = getUserInfo(user_id)
            print("fetching user data from database...")
            login_session['username'] = user.name
            login_session['email'] = user.email
            login_session['picture'] = user.picture
            login_session['id'] = user.id
            # otherwise, retrieve relevant information from google idinfo and
            # then call createUser to add to database.
        else:
            login_session['username'] = idinfo['name']
            login_session['picture'] = idinfo['picture']
            login_session['email'] = idinfo['email']
            login_session['id'] = createUser(login_session)
            # user is now logged in.
        output = ''
        output += '<h1>Welcome, '
        output += login_session['username']
        output += '!</h1>'
        output += '<img src="'
        print("TYPES %s %s") % (str(
            login_session['picture']),
            login_session['username'])
        output += login_session['picture']
        output += ' " style = "width: 300px; height: 300px;border-radius: '\
            '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;> '
        print("you are now logged in as %s" % login_session['username'])
        print ("done!")

        flash("You are now logged in as %s" % login_session['username'])
        return output
    except ValueError:
        # Invalid token
        print('INVALID!!!')
        pass


@app.route('/login')
def showLogin():
    # create anti-forgery token at login to prevent cross site request forgery
    # attacks.
    state = generateAntiForgeryToken()
    print(state)
    return render_template('newLogin.html', STATE=state)


@app.route('/createrecipe', methods=['GET', 'POST'])
def createRecipe():
    # GET route delivers a form to create a new recipe, seeding it with state
    # variable
    if request.method == 'GET':
        if 'username' not in login_session:
            return redirect(url_for('showLogin'))
        state = login_session['state']
        print(get_flashed_messages())
        return render_template(
            'newrecipe.html',
            username=login_session['username'],
            STATE=login_session['state'])
    # POST route checks that state variable received from that form is
    # correct, creates recipe in database and redirects to create ingredient
    # page
    if request.method == 'POST':
        if request.form['state'] != login_session['state']:
            response = make_response(
                json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        newRecipe = Recipe(
            name=request.form['name'],
            description=request.form['description'],
            difficulty=request.form['difficulty'],
            cuisine_id=request.form['cuisine'],
            user_id=getUserId(
                login_session['email']))
        session.add(newRecipe)
        session.commit()
        flash("recipe successfully created!")
        return redirect(
            url_for(
                'create_ingredient',
                cuisine_id=newRecipe.cuisine_id,
                recipe_id=newRecipe.id))
# JSON endpoints for recipes


@app.route('/allrecipes/json')
def all_recipes_handler_json():
    if request.method == 'GET':
        cuisines = session.query(Cuisine).all()
        recipes = session.query(Recipe).all()
        return jsonify(recipes=[i.serialize for i in recipes])


@app.route('/cuisines/<string:cuisine_id>/recipes/json', methods=['GET'])
def cuisine_recipes_handler_json(cuisine_id):
    if request.method == 'GET':
        cuisines = session.query(Cuisine).all()
        recipes = session.query(Recipe).filter_by(cuisine_id=cuisine_id).all()
        return jsonify(recipes=[i.serialize for i in recipes])


@app.route('/allrecipes')
def all_recipes_handler():
    # renders main recipe page.  If currently logged in, sends state
    if request.method == 'GET':
        cuisines = session.query(Cuisine).all()
        recipes = []
        for recipe in session.query(Recipe).all():
            recipes.append(
                (recipe, session.query(User).filter_by(
                    id=recipe.user_id).one()))
        if 'username' not in login_session:
            user_id = None
            username = None
            state = None
            userpicture = ""
        else:
            user_id = getUserId(login_session['email'])
            username = login_session['username']
            userpicture = login_session['picture']
            state = login_session['state']
        return render_template(
            'allrecipes.html',
            picture=userpicture,
            username=username,
            recipes=recipes,
            cuisines=cuisines,
            user_id=user_id,
            STATE=state)
        return jsonify(recipes=[i.serialize for i in recipes])


@app.route('/cuisines/<string:cuisine_id>/recipes/', methods=['GET'])
def cuisine_recipes_handler(cuisine_id):
    # renders page for a particular cuisine, verifies state if logged in
    if request.method == 'GET':
        if 'username' not in login_session:
            state = None
            user_id = None
            username = None
            userpicture = ""
        else:
            user_id = getUserId(login_session['email'])
            username = login_session['username']
            state = login_session['state']
            userpicture = login_session['picture']
        cuisines = session.query(Cuisine).all()
        recipes = []
        for recipe in session.query(Recipe).filter_by(
                cuisine_id=cuisine_id).all():
            recipes.append(
                (recipe, session.query(User).filter_by(
                    id=recipe.user_id).one()))
        print(recipes)
        return render_template(
            "cuisinerecipes.html",
            cuisines=cuisines,
            picture=userpicture,
            username=username,
            recipes=recipes,
            cuisine=cuisine_id,
            STATE=state,
            user_id=user_id)
        return jsonify(recipes=[i.serialize for i in recipes])


@app.route(
    '/cuisines/<string:cuisine_id>/recipes/<int:id>',
    methods=[
        'GET',
        'PUT',
        'DELETE'])
# route handles GET,PUT and DELETE requests for any particular recipe
def recipe_handler(id, cuisine_id):
    recipe = session.query(Recipe).filter_by(
        id=id, cuisine_id=cuisine_id).one()
    ingredients = session.query(Ingredient).filter_by(recipe_id=id).all()
    creator = getUserInfo(recipe.user_id)
    if request.method == 'GET':
        if 'username' not in login_session:
            state = None
            return render_template(
                "recipe.html",
                creator=creator,
                username=None,
                cuisine_id=cuisine_id,
                user_id=None,
                recipe=recipe,
                userpicture="",
                ingredients=ingredients)
        else:
            state = login_session['state']
            user_id = getUserId(login_session['email'])
            userpicture = login_session['picture']
            print("user id is...%s" % user_id)
            return render_template(
                "recipe.html",
                creator=creator,
                STATE=login_session['state'],
                username=login_session['username'],
                cuisine_id=cuisine_id,
                picture=userpicture,
                user_id=user_id,
                recipe=recipe,
                ingredients=ingredients)
        return jsonify(RecipeAttributes=recipe.serialize)
    if request.method == 'PUT':
        if request.form['state'] != login_session['state']:
            response = make_response(
                json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            flash('invalid state parameter', 'error')
            return redirect(
                url_for(
                    'recipe_handler',
                    id=id,
                    cuisine_id=cuisine_id))

        if 'username' not in login_session or\
           creator.id != login_session['id']:
            return redirect(url_for("showLogin"))
        print(request.form['name'])
        print(
            recipe.name +
            recipe.description +
            recipe.difficulty +
            recipe.cuisine_id)
        print(session.query(Recipe).filter_by(
            id=id, cuisine_id=cuisine_id).one())
        recipe.name = request.form['name']
        recipe.description = request.form['description']
        recipe.difficulty = request.form['difficulty']
        recipe.cuisine_id = request.form['cuisine_id']
        flash('recipe successfully updated!')
        session.commit()
        return recipe.cuisine_id

    if request.method == 'DELETE':

        if request.args.get('state') != login_session['state']:
            response = make_response(
                json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            flash(
                'Invalid state parameter!  Authorities have been notified.',
                'error')
            return redirect(url_for('all_recipes_handler'))
        if 'username' not in login_session\
           or creator.id != login_session['id']:
            flash('You have not got the right to delete that!', 'error')
            return redirect(url_for("showLogin"))
        for ingredient in ingredients:
            session.delete(ingredient)
        session.delete(recipe)
        session.commit()
        flash("Recipe successfully deleted!")
        return "Recipe Deleted."


@app.route(
    '/cuisines/<string:cuisine_id>/recipes/<int:recipe_id>/newIngredient',
    methods=[
        'GET',
        'POST'])
# handles creation of ingredients related to particular recipes. Both GET
# and POST reserved for logged in creator
def create_ingredient(cuisine_id, recipe_id):
    recipe = session.query(Recipe).filter_by(id=recipe_id).one()
    print(recipe.user_id)
    creator = getUserInfo(recipe.user_id)
    if 'username' not in login_session or creator.id != login_session['id']:
        return redirect(url_for("showLogin"))
    if request.method == 'GET':
        state = generateAntiForgeryToken()
        userpicture = login_session['picture']
        return render_template(
            'createIngredient.html',
            STATE=login_session['state'],
            username=login_session['username'],
            recipe_id=recipe_id,
            picture=userpicture,
            cuisine_id=cuisine_id)
    if request.method == 'POST':
        print (request.form['state'])
        if request.form['state'] != login_session['state']:
            response = make_response(
                json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            flash('Invalid state parameter')
            return response
        ingredient = Ingredient(
            recipe_id=recipe_id,
            user_id=getUserId(
                login_session['email']),
            name=request.form['name'],
            amount=request.form['amount'],
            unit=request.form['unit'])
        session.add(ingredient)
        session.commit()
        flash('Ingredient added to recipe!')
        return redirect(
            url_for(
                'recipe_handler',
                cuisine_id=cuisine_id,
                id=recipe_id),
            303)


@app.route(
           '/cuisines/<string:cuisine_id>/recipes'
           '/<int:recipe_id>/ingredients/<int:id>',
           methods=['GET', 'PUT', 'DELETE'])
# handles editing and deleting ingredients related to particular recipes.
# All routes restricted to logged in creator of ingredient.
def ingredient_handler(id, cuisine_id, recipe_id):
    ingredient = session.query(Ingredient).filter_by(id=id).one()
    cuisine_id = cuisine_id
    recipe_id = recipe_id
    creator = getUserInfo(ingredient.user_id)
    if 'username' not in login_session or creator.id != login_session['id']:
        return redirect(url_for("showLogin"))
    user_id = getUserId(login_session['email'])
    if request.method == 'GET':
        state = login_session['state']
        userpicture = login_session['picture']
        return render_template(
            "editIngredient.html",
            username=login_session['username'],
            STATE=login_session['state'],
            user_id=user_id,
            recipe_id=recipe_id,
            cuisine_id=cuisine_id,
            picture=userpicture,
            ingredient=ingredient)
    if request.method == 'PUT':
        if request.form['state'] != login_session['state']:
            response = make_response(
                json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            flash('Invalid state token!')
            return response
        editedIngredient = ingredient
        editedIngredient.name = request.form['name']
        editedIngredient.amount = request.form['amount']
        editedIngredient.unit = request.form['unit']
        session.add(editedIngredient)
        session.commit()
        flash('Ingredient successfully updated!')
        return(url_for('all_recipes_handler'))
    if request.method == 'DELETE':
        if request.args.get('state') != login_session['state']:
            response = make_response(
                json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        deletedIngredient = ingredient
        session.delete(deletedIngredient)
        session.commit()
        flash('ingredient successfully deleted!')
        return(url_for('all_recipes_handler'))

    # create a new user from a login_session


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id
# grab user object from database


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user
# retrieve userid from database using unique email


def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None
# create a random number to use as a state token to prevent cross site
# request forgery attacks.


def generateAntiForgeryToken():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return state


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run()
