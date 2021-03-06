from flask import Flask
from flask_mysqldb import MySQL
import os

def create_app(): 
    # ENVIRONMENT
    if 'FLASK_ENV' in os.environ:
        environment = os.environ['FLASK_ENV']
    else: 
        environment = None
    
    app = Flask(__name__, static_folder ='static')

    # DATABASE CONFIGURATION
    if environment == 'development':
        app.config['MYSQL_HOST'] = 'localhost' 
        app.config['MYSQL_USER'] = 'root'
        app.config['MYSQL_PASSWORD'] = ''
        app.config['MYSQL_DB'] = 'streaming_system'
        app.secret_key = 'mysecretkey'
    else:
        app.config['MYSQL_HOST'] = 'vicoweb.mysql.pythonanywhere-services.com'
        app.config['MYSQL_USER'] = 'vicoweb'
        app.config['MYSQL_PASSWORD'] = 'micontrase;a18'
        app.config['MYSQL_DB'] = 'vicoweb$default'
        app.secret_key = 'mysecretkey'

    mysql = MySQL(app)
    
    return app, mysql, environment