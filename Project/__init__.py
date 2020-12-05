from flask import Flask
from Project.models import db, migrate
from Project.routes import index_routes, sign_routes, main_routes


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///netflix.sqlite3'
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = "Random"

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(index_routes.index_routes)
    app.register_blueprint(main_routes.main_routes)
    app.register_blueprint(sign_routes.sign_routes)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)