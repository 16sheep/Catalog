#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from modules import Base, Destination, Attraction, User, Address
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from flask.ext.httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Local Attraction Finder"


# Connect to Database and create database session
engine = create_engine('sqlite:///LAFDatabase.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
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
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
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
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is'
                                            'already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    print user_id
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['username'])
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).first()
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
    access_token = login_session.get('access_token')
    print login_session['username']
    print access_token
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print result['status']
    if result['status'] == 200:
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showDestinations'))
    else:
        response = make_response(json.dumps('Failed to revoke token for'
                                            'given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Destination Information
@app.route('/destination/<int:destination_id>/attractions/JSON')
def destinationAttractionsJSON(destination_id):
    destination = session.query(Destination).filter_by(id=destination_id).one()
    items = session.query(Attraction).filter_by(
        destination_id=destination_id).all()
    return jsonify(Attractions=[i.serialize for i in items])


@app.route('/destination/addresses/JSON')
def addressesJSON():
    addresses = session.query(Address).all()
    destinations = session.query(Destination).all()
    return jsonify(address=[r.serialize for r in addresses],
                   destination=[r.serialize for r in destinations])


@app.route('/destination/<int:destination_id>/address/JSON')
def destinationAddressJSON(destination_id):
    destination = session.query(Destination).filter_by(id=destination_id).one()
    items = session.query(Address).filter_by(
        destination_id=destination_id).all()
    return jsonify(Addresses=[i.serialize for i in items])


@app.route('/destination/<int:destination_id>/attractions/<int:attraction_id>/JSON')
def attractionItemJSON(destination_id, attraction_id):
    Attraction_Item = session.query(Attraction).filter_by(id=attraction_id).one()
    return jsonify(Attraction_Item=Attraction_Item.serialize)


@app.route('/destination/JSON')
def destinationsJSON():
    destinations = session.query(Destination).all()
    return jsonify(destinations=[r.serialize for r in destinations])


# Show all destinations
@app.route('/')
@app.route('/destination/')
def showDestinations():
    destinations = session.query(Destination).order_by(asc(Destination.name))
    return render_template('destinations.html', destinations=destinations)

# Show all users destinations


@app.route('/destination/mydestinations')
def showMyDestinations():
    destinations = session.query(Destination).filter_by(user_id=login_session['user_id'])
    if 'username' not in login_session:
        return render_template('login.html')
    else:
        return render_template('usersdestinations.html',
                               destinations=destinations)


# Create a new destination


@app.route('/destination/new/', methods=['GET', 'POST'])
def newDestination():
    newDestinationId = session.query(Destination).order_by(Destination.id.desc()).first()
    newDestinationId = newDestinationId.id + 1
    print login_session
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newDestination = Destination(name=request.form['name'],
                                     description=request.form['description'],
                                     image=request.form['image'],
                                     times=request.form['times'],
                                     phone=request.form['phone'],
                                     email=login_session['email'],
                                     user_id=login_session['user_id'])
        session.add(newDestination)
        session.commit()
        newAddress = Address(a_line_1=request.form['a_line_1'],
                             a_line_2=request.form['a_line_2'],
                             town=request.form['town'],
                             postcode=request.form['postcode'],
                             country=request.form['country'],
                             destination_id=newDestinationId)
        session.add(newAddress)
        session.commit()
        flash('New Destination %s Successfully Created' % newDestination.name)
        return redirect(url_for('showDestinations'))
    else:
        return render_template('newDestination.html')

# Edit a destination


@app.route('/destination/<int:destination_id>/edit/',
           methods=['GET', 'POST', 'DELETE'])
def editDestination(destination_id):
    editedDestination = session.query(Destination).filter_by(id=destination_id).first()
    currentAddress = session.query(Address).filter_by(destination_id=editedDestination.id).first()
    if 'username' not in login_session:
        return redirect('/login')
    if editedDestination.user_id != login_session['user_id']:
        return ("<script>function myFunction() {alert('You are not authorized to edit"
                "this destination. Please create your own destination in order"
                "to edit.');}</script><body onload='myFunction()'>")
    if request.method == 'POST':
        if request.form['name']:
            editedDestination.name = request.form['name']
        if request.form['description']:
            editedDestination.description = request.form['description']
        if request.form['image']:
            editedDestination.image = request.form['image']
        if request.form['times']:
            editedDestination.times = request.form['times']
        if request.form['phone']:
            editedDestination.phone = request.form['phone']
        session.add(editedDestination)
        session.commit()
        if request.form['a_line_1']:
            currentAddress.a_line_1 = request.form['a_line_1']
        if request.form['a_line_2']:
            currentAddress.a_line_2 = request.form['a_line_2']
        if request.form['town']:
            currentAddress.town = request.form['town']
        if request.form['postcode']:
            currentAddress.postcode = request.form['postcode']
        if request.form['country']:
            currentAddress.country = request.form['country']
        session.add(currentAddress)
        session.commit()
        flash('Destination Successfully Edited %s' % editedDestination.name)
        return redirect(url_for('showDestinations'))
    if request.method == 'DELETE':
        session.delete(currentAddress)
        session.delete(editedDestination)
        flash(' Successfully Deleted')
        session.commit()
        '''I tried to use return redirect(url_for('showDestinations')) but
        kept getting 405 Method not allowed error'''
        return "cat"
    else:
        return render_template('editDestination.html',
                               destination=editedDestination,
                               address=currentAddress)


# Show a destination info
@app.route('/destination/<int:destination_id>/')
@app.route('/destination/<int:destination_id>/attractions/')
def showDestinationInfo(destination_id):
    destination = session.query(Destination).filter_by(id=destination_id).one()
    creator = getUserInfo(destination.user_id)
    attractions = session.query(Attraction).filter_by(
        destination_id=destination_id).all()
    address = session.query(Address).filter_by(destination_id=destination.id).first()
    print address
    if 'username' not in login_session or destination.user_id != login_session['user_id']:
        return render_template('publicdestinationinfo.html',
                               attractions=attractions,
                               destination=destination,
                               creator=creator,
                               address=address)
    else:
        return render_template('destinationinfo.html',
                               attractions=attractions,
                               destination=destination,
                               creator=creator,
                               address=address)

# Show Attraction info


@app.route('/destination/<int:destination_id>/attractions/<int:attraction_id>')
def showAttractionInfo(destination_id, attraction_id):
    attraction = session.query(Attraction).filter_by(id=attraction_id).one()
    destination = session.query(Destination).filter_by(id=destination_id).one()
    creator = getUserInfo(destination.user_id)
    items = session.query(Attraction).filter_by(
        id=attraction_id).all()
    print items
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicattractioninfo.html',
                               items=items,
                               destination=destination,
                               creator=creator,
                               attraction=attraction)
    else:
        return render_template('attractioninfo.html',
                               items=items,
                               destination=destination,
                               creator=creator,
                               attraction=attraction)


# Create a new attraction
@app.route('/destination/<int:destination_id>/attractions/new/',
           methods=['GET', 'POST'])
def newAttraction(destination_id):
    if 'username' not in login_session:
        return redirect('/login')
    destination = session.query(Destination).filter_by(id=destination_id).one()
    if login_session['user_id'] != destination.user_id:
        return '''<script>function myFunction() {alert('You are not authorized
                to add attractions to this destination. Please create your
                own destination in order to add
                items.');}</script><body onload='myFunction()'>'''
    if request.method == 'POST':
        newItem = Attraction(name=request.form['name'],
                             description=request.form['description'],
                             price=request.form['price'],
                             destination_id=destination_id,
                             user_id=destination.user_id)
        session.add(newItem)
        session.commit()
        flash('New Attraction %s Successfully Created' % (newItem.name))
        return redirect(url_for('showDestinationInfo',
                        destination_id=destination_id))
    else:
        return render_template('newattraction.html',
                               destination_id=destination_id)

# Edit an Attraction


@app.route('/destination/<int:destination_id>/attractions/<int:attraction_id>/edit',
           methods=['GET', 'POST', 'DELETE'])
def editAttraction(destination_id, attraction_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Attraction).filter_by(id=attraction_id).one()
    destination = session.query(Destination).filter_by(id=destination_id).one()
    if login_session['user_id'] != destination.user_id:
        return '''<script>function myFunction() {alert('You are not authorized
                to edit attractions to this destination. Please create your own
                destination in order to edit
                items.');}</script><body onload='myFunction()'>'''
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        session.add(editedItem)
        session.commit()
        flash('Attraction Successfully Edited')
        return redirect(url_for('showAttractionInfo',
                        destination_id=destination_id,
                        attraction_id=attraction_id))
    if request.method == 'DELETE':
        session.delete(editedItem)
        session.commit()
        flash('Attraction Successfully Deleted')
        return "cat"
    else:
        return render_template('editAttraction.html',
                               destination_id=destination_id,
                               attraction_id=attraction_id,
                               item=editedItem)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)

