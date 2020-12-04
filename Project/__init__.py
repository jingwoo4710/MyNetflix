from flask import Flask
from Project.models import db, migrate
from Project.routes import index_routes, sign_routes, main_routes
from embedding_as_service_client import EmbeddingClient
from random import *


en = EmbeddingClient(host='54.180.124.154', port=8989)


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://jzldammovjblxe:3786b05155a588f1097c298f227121cbb08740f95e6dca5df61498e7f9138d86@ec2-75-101-212-64.compute-1.amazonaws.com:5432/d55tm2dunhdufa'
    # "postgres://jzldammovjblxe:3786b05155a588f1097c298f227121cbb08740f95e6dca5df61498e7f9138d86@ec2-75-101-212-64.compute-1.amazonaws.com:5432/d55tm2dunhdufa"
    # "sqlite:///netflix.sqlite3"
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