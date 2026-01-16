from flask import Flask, request, session, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_cors import CORS

# Import the db instance from models
from models import db, User, Recipe

app = Flask(__name__)
app.secret_key = b'\x15\x16\x1a\xde\x94\x97\xda\x7f\xc0\xc1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

# 1. Initialize extensions with the app
CORS(app)
db.init_app(app) # <--- THIS FIXES THE RUNTIMERREOR
migrate = Migrate(app, db)
api = Api(app)

# --- RESOURCES ---

class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            new_user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            new_user.password_hash = data.get('password')
            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id
            return make_response(new_user.to_dict(), 201)
        except Exception:
            return make_response({"errors": ["validation errors"]}, 422)

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return make_response(user.to_dict(), 200)
        return make_response({"error": "Unauthorized"}, 401)

class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter(User.username == data.get('username')).first()

        if user and user.authenticate(data.get('password')):
            session['user_id'] = user.id
            return make_response(user.to_dict(), 200)
        return make_response({"error": "Invalid username or password"}, 401)

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session['user_id'] = None
            return make_response({}, 204)
        return make_response({"error": "Unauthorized"}, 401)

class RecipeIndex(Resource):
    def get(self):
        if not session.get('user_id'):
            return make_response({"error": "Unauthorized"}, 401)
        recipes = [r.to_dict() for r in Recipe.query.all()]
        return make_response(recipes, 200)

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return make_response({"error": "Unauthorized"}, 401)

        data = request.get_json()
        try:
            new_recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id
            )
            db.session.add(new_recipe)
            db.session.commit()
            return make_response(new_recipe.to_dict(), 201)
        except Exception:
            return make_response({"errors": ["validation errors"]}, 422)

# --- ROUTES ---
api.add_resource(Signup, '/signup')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(RecipeIndex, '/recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)