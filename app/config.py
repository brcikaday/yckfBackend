import os 

basedir = os.path.abspath(os.path.dirname(__file__))




class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True , 'pool_recycle': 280}
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    MAIL_SERVER = 'smtp.gmail.com'          
    MAIL_PORT = 465                      
    MAIL_USE_TLS = False                   
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('YCKF', MAIL_USERNAME)
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
    PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY')
    CERT_SIGNING_KEY = os.environ.get('CERT_SIGNING_KEY')
    BASE_URL = os.environ.get('BASE_URL', 'https://yckf-app.vercel.app')
    CERT_LOGO_PATH = os.environ.get('CERT_LOGO_PATH')