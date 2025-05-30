from flask import Flask
from flask_restx import Api
from .auth.views import auth_namespace
from .receipt.views import receipt_namespace
from .config.config import config_dict

# this is import of db instant, then models for recipt_files,recipt and user will create.
from .utils import db
from .models.receipt import Receipt
from .models.receipt_file import ReceiptFile
from .models.users import User
# this is for migrate all models to sqllite db
from flask_migrate import Migrate
# JWT authorization
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import NotFound,MethodNotAllowed

# object access globally.
jwt = JWTManager()
migrate = Migrate()
def create_app(config = config_dict['dev']):
    app = Flask(__name__)
    app.config.from_object(config)
    # configuring database with flask app
    db.init_app(app)
    migrate.init_app(app,db)
    # create JWT authorisation token.
    jwt.init_app(app)
    # authorization variable holding value of authorization header for jwt access token
    authorizations ={
        "Bearer Auth":{
            'type':"apiKey",
            'in': "header",
            'name':"Authorization",
            'description':"Add a JWT with ** Bearer &lt;JWT&gt; to authorize, create the login request it will generate access token put it  here in value OR First sign in and then login"
        }
    }
    api = Api(app,
              title="OCR Conversion Api",
              description="A REST API for Receipt OCR data Extraction",
              authorizations=authorizations,
              security="Bearer Auth")
    
    api.add_namespace(receipt_namespace)
    api.add_namespace(auth_namespace,path='/auth')

    @api.errorhandler(NotFound)
    def not_found(error):
        return {"error":"Not Found"}, 404

    @api.errorhandler(MethodNotAllowed)
    def method_not_allowed(error):
        return {"error": "Method Not Allowed"},405

    # make flask shell context.
    @app.shell_context_processor
    def make_shell_context():
        return{
            'db':db,
            'User':User,
            'Receipt':Receipt,
            'ReceiptFile':ReceiptFile
        }

    return app

