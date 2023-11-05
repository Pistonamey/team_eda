from flask import Flask
from check_approval import check_aprvl
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*", "https://sub.example.com"])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 


# Register blueprints
app.register_blueprint(check_aprvl)

if __name__ == '__main__':
    app.run()
