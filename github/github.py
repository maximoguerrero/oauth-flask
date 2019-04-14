from flask import Flask, render_template, request, redirect, url_for, session

import uuid
import json
import requests

app = Flask(__name__)


@app.route('/')
def home():
    # Show homepage if authenticated, otherwise redirect to login page
    if 'login' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('showLogin'))


@app.route('/login/')
def showLogin():
    return render_template('login.html')


@app.route('/logout/')
def logout():
    del session['login']
    return redirect(url_for('showLogin'))


@app.route('/githubconnect/')
def githubConnect():
    state = request.args.get('state')
    client_id = ''  # CLIENT ID
    redirect_uri = ''  # REDIRECT URL
    if state != session['state']:
        # Redirect to Github to get code
        state = uuid.uuid4()
        session['state'] = unicode(str(state), 'utf-8')
        scope = 'read:user,user:email'
        url = 'https://github.com/login/oauth/authorize?client_id=%s&redirect_uri=%s&scope=%s&state=%s' % (
            client_id, redirect_uri, scope, state)
        return redirect(url)

    if 'code' in request.args:
        client_secret = ''  # CLIENT SECRET
        code = request.args.get('code')
        url = 'https://github.com/login/oauth/access_token'
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'state': state
        }
        headers = {'Accept': 'application/json'}
        r = requests.post(url, params=payload, headers=headers)
        response = r.json()
        if 'access_token' in response:
            access_token = response['access_token']
            session['access_token'] = access_token

            url = 'https://api.github.com/user?access_token={}'
            r = requests.get(url.format(access_token))
            userData = r.json()
            if 'login' in userData:
                session['login'] = userData['login']
                # Use commented code below to view data to store in DB
                # app.logger.debug(userData)

                # Get primary email address on account
                url = 'https://api.github.com/user/emails?access_token={}'
                r = requests.get(url.format(access_token))
                emails = r.json()
                for email in emails:
                    if email['primary']:
                        # store primary email address
                        app.logger.debug(email['email'])
            else:
                # Error in request for user info
                app.logger.debug(userData)
            return redirect(url_for('home'))

    return redirect(url_for('showLogin'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
