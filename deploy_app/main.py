import os
from flask import Flask

# Initialize the Flask application
app = Flask(__name__)

@app.route('/')
def hello():
    # This logic returns the specific message required by the assignment 
    return "Hello from Cloud Run! System check complete."

if __name__ == "__main__":
    # We use the PORT environment variable if provided by Cloud Run, 
    # otherwise we default to 8080.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)