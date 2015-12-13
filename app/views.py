from app import app, github_auth, db
from flask import render_template, flash, redirect, request, g, session, url_for, jsonify
from app.github_task import GithubProvider, get_stats_for_day
from app.codeforces_task import CodeforcesProvider, get_stats_for_day as codeforces_stats
import datetime


@app.before_request
def before_request():
    g.user = None

@app.route('/')
@app.route('/index')
def index():
    if 'github_token' in session:
        return redirect(url_for('profile'))
    else:
        user = None
    return render_template('index.html',
                           title='Home',
                           user=user)

@app.route('/gh_callback')
def authorized():
    resp = github_auth.authorized_response()
    if resp is None:
        return 'Access denied'
    session['github_token'] = (resp['access_token'], '')
    user = github_auth.get('user')
    session['user'] = user.data
    print("Authorized GitHub, token is {}".format(resp['access_token']))
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    return render_template('profile.html',
                           title='Profile',
                           user=user,
                           scores=get_scores(user))


@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github_auth.authorize(
                callback=url_for('authorized', _external=True))
    else:
        return "Already logged in"


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@github_auth.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

@app.route('/stats')
def stats():
    token = get_github_oauth_token()[0]
    result = []
    now = datetime.date.today().toordinal()
    for x in range(7):
        dt = now - x
        stats = db.github.by_day.find_one({'dt': dt})
        if stats:
            stats = stats['stats']
        else:
            stats = {"msg": "IN PROGRESS"}
            get_stats_for_day.delay(token, datetime.datetime.fromordinal(dt))
        result.append(stats)
    return jsonify({'result': result})

@app.route('/cf_stats')
def cf_stats():
    result = []
    now = datetime.date.today().toordinal()
    for x in range(30):
        dt = now - x
        stats = db.codeforces.by_day.find_one({'dt': dt})
        if stats:
            stats = stats['stats']
        else:
            stats = {"msg": "IN PROGRESS"}
            codeforces_stats.delay(datetime.datetime.fromordinal(dt))
        result.append(stats)
    return jsonify({'result': result})

@app.route('/codeforces')
def codeforces():
    now = datetime.date.today()
    return jsonify(codeforces_stats(now))

def get_scores(user):
    return {
        'stars': 100,
        'additions': 200,
        'commits_count': 50,
    }
