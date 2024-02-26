from flask import Flask, redirect, url_for, session, request
from flask_oauthlib.client import OAuth

app = Flask(__name__)
app.secret_key = 'your_secret_key'

oauth = OAuth(app)

# Replace these values with your own OAuth provider's credentials
google = oauth.remote_app(
    'google',
    consumer_key='your_google_client_id',
    consumer_secret='your_google_client_secret',
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)


@app.route('/')
def index():
    return 'Welcome! <a href="/login">Login with Google</a>'


@app.route('/login')
def login():
    return google.authorize(callback=url_for('authorized', _external=True))


@app.route('/logout')
def logout():
    session.pop('google_token', None)
    return redirect(url_for('index'))


@app.route('/login/authorized')
def authorized():
    response = google.authorized_response()
    if response is None or response.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )
    
    session['google_token'] = (response['access_token'], response['refresh_token'])
    user_info = google.get('userinfo')
    # Here you can store user information in your database or session as required.
    return 'Logged in as: ' + user_info.data['email']


@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')


@app.route('/refresh')
def refresh():
    refresh_token = session.get('google_token')[1]
    if refresh_token:
        data = {
            'refresh_token': refresh_token,
            'client_id': google.consumer_key,
            'client_secret': google.consumer_secret,
            'grant_type': 'refresh_token'
        }
        response = google.authorized_response(
            method='POST',
            data=data,
            url=google.access_token_url
        )
        if response and 'access_token' in response:
            session['google_token'] = (response['access_token'], refresh_token)
            return 'Token refreshed successfully!'
    return 'Unable to refresh token. Please reauthorize.'


if __name__ == '__main__':
    app.run(debug=True)
