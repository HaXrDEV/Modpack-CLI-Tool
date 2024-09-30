import os
import requests
import webbrowser
import http.server
import socketserver
import threading

class GitHubAuthenticator:
    def __init__(self, redirect_uri):
        self.client_id = input('\nGITHUB_CLIENT_ID: ')  # Get from environment variable
        self.client_secret = input('\nGITHUB_CLIENT_SECRET: ')  # Get from environment variable
        self.redirect_uri = redirect_uri
        self.access_token = None

        if not self.client_id or not self.client_secret:
            raise ValueError("Please set the GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables.")

    def authenticate(self):
        # Step 1: Redirect user to GitHub for authentication
        auth_url = (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=repo"
        )
        webbrowser.open(auth_url)

        # Start the server to handle the callback
        self.start_server()

    def start_server(self):
        # Step 2: Start a simple HTTP server to listen for the callback
        class CallbackHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/callback"):
                    self.handle_callback()
                else:
                    self.send_response(404)
                    self.end_headers()

            def handle_callback(self):
                # Extract the code from the query parameters
                code = self.path.split("code=")[-1]
                if code:
                    # Step 3: Exchange the code for an access token
                    token_url = 'https://github.com/login/oauth/access_token'
                    payload = {
                        'client_id': self.server.authenticator.client_id,
                        'client_secret': self.server.authenticator.client_secret,
                        'code': code
                    }
                    headers = {'Accept': 'application/json'}
                    response = requests.post(token_url, data=payload, headers=headers)
                    self.send_response(200)
                    self.end_headers()
                    
                    if response.ok:
                        self.server.authenticator.access_token = response.json().get('access_token')
                        self.wfile.write(b'Success! You can close this window now.')
                    else:
                        self.wfile.write(b'Failed to retrieve access token.')
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'No code provided.')

        # Set up the HTTP server
        PORT = 5000
        handler = CallbackHandler
        handler.server.authenticator = self  # Pass the authenticator to the handler

        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print(f"Serving on port {PORT}...")
            threading.Thread(target=httpd.serve_forever).start()

if __name__ == '__main__':
    REDIRECT_URI = 'http://localhost:5000/callback'

    authenticator = GitHubAuthenticator(REDIRECT_URI)
    authenticator.authenticate()

    # Wait for the user to authenticate and the access token to be retrieved
    while authenticator.access_token is None:
        pass

    print(f"Access Token: {authenticator.access_token}")
