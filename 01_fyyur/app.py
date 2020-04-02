#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.ext.hybrid import hybrid_property
import datetime
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class VenueArea(db.Model):
    __tablename__ = 'VenueArea'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    venues = db.relationship('Venue', backref='area', lazy=True)

    def __repr__(self):
        return f"<{self.id}, {self.state}, {self.city}>"


class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    area_id = db.Column(db.Integer, db.ForeignKey(
        'VenueArea.id'), nullable=False)
    genres = db.Column(db.ARRAY(db.String()))

    @hybrid_property
    def upcoming_shows(self):
        return list(filter(lambda show: parse_datetime(show.start_time) >= datetime.datetime.now(), self.shows))

    @hybrid_property
    def past_shows(self):
        return list(filter(lambda show: parse_datetime(show.start_time) < datetime.datetime.now(), self.shows))

    @hybrid_property
    def upcoming_shows_count(self):
        return len(self.upcoming_shows)

    @hybrid_property
    def past_shows_count(self):
        return len(self.past_shows)

    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
        return f"<{self.id}, {self.name}>"


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    genres = db.Column(db.ARRAY(db.String()))

    @hybrid_property
    def upcoming_shows(self):
        return list(filter(lambda show: parse_datetime(show.start_time) >= datetime.datetime.now(), self.shows))

    @hybrid_property
    def past_shows(self):
        return list(filter(lambda show: parse_datetime(show.start_time) < datetime.datetime.now(), self.shows))

    @hybrid_property
    def upcoming_shows_count(self):
        return len(self.upcoming_shows)

    @hybrid_property
    def past_shows_count(self):
        return len(self.past_shows)

    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f"<{self.id}, {self.name}>"


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)

    def __repr__(self):
        return f"<{self.id}, {self.venue_id}, {self.artist_id}, {self.start_time}>"


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)



#----------------------------------------------------------------------------#
# Parsers.

def parse_datetime(value):
    return datetime.datetime.strptime(value,'%Y-%m-%d %H:%M:%S')
#----------------------------------------------------------------------------#


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # num_shows should be aggregated based on number of upcoming shows per venue.
    data = VenueArea.query.all()
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form['search_term']
    venues = Venue.query.filter(Venue.name.ilike('%'+search_term+'%')).all()
    response = {
        "count": len(venues),
        "data": venues
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    data = Venue.query.filter_by(id=venue_id).first()
    if data is None:
        abort(404)
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        address = request.form.get('address')
        phone = request.form.get('phone')
        facebook_link = request.form.get('facebook_link')
        genres = request.form.getlist('genres')
        area = VenueArea.query.filter_by(state=state, city=city).one_or_none()
        if area is None:
            area = VenueArea(state=state, city=city)

        venue = Venue(name=name, phone=phone, facebook_link=facebook_link,
                      address=address, area=area, genres=genres)
        db.session.add(area)
        db.session.commit()

    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        # on unsuccessful db insert, flash error
        flash('An error occurred. Venue ' + name +
              ' could not be listed.', 'error')
    else:
        # on successful db insert, flash success
        flash('Venue ' + name + ' was successfully listed!')
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form['search_term']
    artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%')).all()
    response = {
        "count": len(artists),
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    data = Artist.query.filter_by(id=artist_id).first()
    if data is None:
        abort(404)
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()
    if artist is None:
        abort(404)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.filter_by(id=artist_id).first()
    if artist is None:
        abort(404)
    try:
        artist.city = request.form.get('city')
        artist.state = request.form.get('state')
        artist.phone = request.form.get('phone')
        artist.facebook_link = request.form.get('facebook_link')
        artist.genres = request.form.getlist('genres')
        db.session.commit()

    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()
    if venue is None:
        abort(404)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.filter_by(id=venue_id).first()
    if venue is None:
        abort(404)
    try:
        city = request.form.get('city')
        state = request.form.get('state')
        venue.name = request.form.get('name')
        venue.address = request.form.get('address')
        venue.phone = request.form.get('phone')
        venue.facebook_link = request.form.get('facebook_link')
        venue.genres = request.form.getlist('genres')
        area = VenueArea.query.filter_by(state=state, city=city).one_or_none()
        if area is None:
            area = VenueArea(state=state, city=city)
            db.session.add(area)
        venue.area_list = area.id
        db.session.commit()

    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # on successful db insert, flash success
    error = False
    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        phone = request.form.get('phone')
        facebook_link = request.form.get('facebook_link')
        genres = request.form.getlist('genres')
        artist = Artist(name=name, city=city, state=state, phone=phone,
                        facebook_link=facebook_link, genres=genres)
        db.session.add(artist)
        db.session.commit()

    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        # on unsuccessful db insert, flash error
        flash('An error occurred. Artist ' + name +
              ' could not be listed.', 'error')
    else:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # num_shows should be aggregated based on number of upcoming shows per venue.
    data = Show.query.all()
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    error = False
    try:
        artist_id = int(request.form.get('artist_id'))
        venue_id = int(request.form.get('venue_id'))
        start_time = request.form.get('start_time')
        show = Show(artist_id=artist_id, venue_id=venue_id,
                    start_time=start_time)
        db.session.add(show)
        db.session.commit()

    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        # on unsuccessful db insert, flash error
        flash('An error occurred. Show could not be listed ', 'error')
    else:
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
