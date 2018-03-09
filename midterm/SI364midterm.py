###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import Required, Length
from flask_sqlalchemy import SQLAlchemy
from apiclient.discovery import build
import requests, json

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app.config['SECRET_KEY'] = 'eahfpfoheqwfij'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:icedout@localhost:5432/364"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)

######################################
######## HELPER FXNS (If any) ########
######################################
url = "https://api.themoviedb.org/3/search/person?api_key=a55c954f4c5cb767bed20229fc253426&query="

def get_or_create_movie(title, release_date, description):
    movie = db.session.query(Movie).filter_by(title=title).first()
    if movie:
        print(movie)
    else:
        movie = Movie(title=title, release_date=release_date, description=description)
        db.session.add(movie)
        db.session.commit()
        print(movie)


def get_or_create_actor(name, popularity, movie_title):
    actor = db.session.query(Actor).filter_by(name=name).first()
    if actor:
        print(actor)
    else:
        actor = Actor(name=name, popularity=popularity)
        top_movie_id = db.session.query(Movie).filter_by(title=movie_title).first().id
        actor.top_movie_id = top_movie_id
        db.session.add(actor)
        db.session.commit()
        print(actor)

##################
##### MODELS #####
##################
class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class Movie(db.Model):
    __tablename__ = "movies"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    release_date = db.Column(db.String(10))
    description = db.Column(db.String(2000))
    rel = db.relationship('Actor', backref='Movies')
    def __repr__(self):
        return "Movie: {0} \nReleased: {1} \nDescription: {2} \n\n".format(self.title, self.release_date, self.description)

class Actor(db.Model):
    __tablename__ = "actors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    popularity = db.Column(db.Integer)
    top_movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'))
    def __repr__(self):
        return "Actor: {0}, {1}, {2}".format(self.name, self.popularity, self.top_movie_id)

class Stats(db.Model):
    __tablename__ = "stats"
    id = db.Column(db.Integer, primary_key=True)
    #will finish this model later


###################
###### FORMS ######
###################
class NameForm(FlaskForm):
    name = StringField("Please enter your name. ", validators=[Required(), Length(min=1, max=64)])
    submit = SubmitField()

class MovieForm(FlaskForm):
    actor = StringField("Enter your favorite actor! ", validators=[Required(), Length(min=1, max=64)])
    submit = SubmitField()

    def validate_actor(self, field):
        if len(field.data.split(' ')) > 2:
            raise ValidationError('Enter only an actors first and last name as query.')

class StatsForm(FlaskForm):
    submit = SubmitField()
    #will finish this form later

#######################
###### VIEW FXNS ######
#######################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    return render_template("base.html", form=form)

@app.route('/names', methods=["GET"])
def all_names():
    if request.args:
        name = request.args['name']
        n = Name(name=name)
        db.session.add(n)
        db.session.commit()
    return render_template('name_example.html', names=Name.query.all())

@app.route('/movies', methods=['GET', 'POST'])
def all_movies():
    form = MovieForm()
    if request.method == "POST" and form.validate_on_submit():
        query = requests.get(url + form.actor.data.replace(" ", "+")).json()
        if query['total_results'] == 0 or query['results'][0]['known_for'] == []:
            return render_template("500.html"), 500

        query = query['results'][0]
        movie_info = query['known_for'][0]
        get_or_create_movie(movie_info['title'], movie_info['release_date'], movie_info['overview'])
        get_or_create_actor(query['name'], query['popularity'], movie_info['title'])
    return render_template('movies.html', form=form, movies=Movie.query.all())

@app.route('/stats')
def stats():
    return render_template('stats.html', actors=Actor.query.all())


## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True, debug=True)
