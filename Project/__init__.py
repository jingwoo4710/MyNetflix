import os 
import numpy as np
import pandas as pd
from flask import Flask
from flask import request
from flask import redirect   
from flask import render_template
from flask import session
from flask.helpers import url_for
from Project.models import Lists, db
from Project.models import Users, Movies, get_recommend_movie_list
import requests
import json, csv
from embedding_as_service_client import EmbeddingClient
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle


en = EmbeddingClient(host='54.180.124.154', port=8989)


def create_app():
    app = Flask(__name__)


    app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://tozjixhlxhsivp:e89e984f6706c772da62c15bec81ae724b49c17bbd75ec36f4809b4285bc0d1e@ec2-3-220-98-137.compute-1.amazonaws.com:5432/d386rtfhlf291s"
    #'sqlite:///netflix.sqlite3'   

    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.test_request_context():
        db.create_all()
        


    @app.route('/signup', methods=['GET','POST'])  
    def register():
        if request.method == "POST":
            result = request.form
            print(dict(result))
            user = Users.query.get(result['email']) or Users(id = result['email'])
            user.password = result['password']
            user.movie = result['movie']
            db.session.add(user)  
            db.session.commit()  

        return render_template('signup.html')


    @app.route('/login', methods=['GET','POST'])  
    def login():
        if request.method == "POST":
            result = request.form
            print(dict(result))

            email = Users.query.with_entities(Users.id).filter(Users.id == result['email']).first()
            password = Users.query.with_entities(Users.password).filter(Users.id == result['email']).first()        
            print(email, password)

            if (email[0] == result['email']) & (password[0] == result['password']):
                print('Login Success')

                return redirect(url_for('main',  email = email[0]))

        return render_template('login.html')

        
    @app.route('/')
    def index():
        return render_template('index.html')


    @app.route('/main/')
    def main():
        print(request.args.get('email'))
        email = request.args.get('email')
        movie = Users.query.with_entities(Users.movie).filter(Users.id == email).first()
        print(movie[0])
        baseurl = 'http://www.omdbapi.com/?i=tt3896198&apikey=d5202ac' #Enter your API key here
        params_diction = {}
        params_diction['s'] = movie[0]
        params_diction['r'] = 'json'
        response = requests.get(baseurl, params=params_diction)
        data = json.loads(response.text)
        data = data['Search'][0]
        title = data['Title']

        model = pickle.load(open('model.pkl', 'rb'))
        prediction = model.predict(en.encode(texts =[title]))[0]
        params_diction = {}
        params_diction['s'] = prediction
        params_diction['r'] = 'json'
        response = requests.get(baseurl, params=params_diction)
        data = json.loads(response.text)
        data = data['Search'][0]
        pred_title = []
        pred_poster = []
        pred_title.append(data['Title'])
        pred_poster.append(data['Poster'])
        print('Prediction Success!')


        df = pd.read_csv('movie.csv')
        count_vector = CountVectorizer(ngram_range=(1, 3))
        df = df.dropna()
        c_vector_genres = count_vector.fit_transform(df['genres'])
        print(c_vector_genres.shape)
        gerne_c_sim = cosine_similarity(c_vector_genres, c_vector_genres).argsort()[:, ::-1]

        
        df2 = get_recommend_movie_list(df, movie_title=movie[0], gerne_c_sim=gerne_c_sim)
        rec_titles = df2.title.to_list()[:5]
        print("Recommend Success!")

        for title in rec_titles:
            params_diction = {}
            params_diction['s'] = title
            params_diction['r'] = 'json'
            response = requests.get(baseurl, params=params_diction)
            data = json.loads(response.text)
            data = data['Search'][0]
            pred_title.append(data['Title'])
            pred_poster.append(data['Poster'])
            list = Lists()
            list.user = email
            list.movie = data['Title']

            db.session.add(list)
            db.session.commit()


        return render_template('main.html', image1 = pred_poster[0], image2 = pred_poster[1], image3 = pred_poster[2], image4 = pred_poster[3], image5 = pred_poster[4])


    @app.route('/data/')
    def data():
        db.drop_all()

        db.create_all()

        with open('Project/movie.csv', 'r') as f:
            reader = csv.reader(f)
            next(reader) 
            for data in reader:
                new = Movies()
                new.id = data[0]
                new.title = data[1]
                new.genres = data[2]
                new.embedding = en.encode(texts = [data[2]])
                new.release_date = data[3]
                new.runtime = data[4]
                new.runtime = data[5]
                db.session.add(new)  
                db.session.commit() 

        genre = []
        title = []
        movies = Movies.query.with_entities(Movies.title, Movies.embedding).all()
        for movie in movies:
            genre.append(movie.embedding)
            title.append(movie.title)

        genre = np.array(genre)

        nsamples, nx, ny = genre.shape

        genre_2d = genre.reshape(nsamples, nx * ny)

        model = LogisticRegression()

        model.fit(genre_2d, title)

        pickle.dump(model, open('model.pkl', 'wb'))

        return render_template('login.html')

    @app.route('/update/')
    def update():
        if request.method == "POST":
            result = request.form
            print(dict(result))

            db.session.query(Users).filter(Users.id == result['email']).update({'movie': result['movie']})
            db.session.commit()

        return render_template('update.html')

    return app



if __name__ == "__main__":
    app = create_app()
    breakpoint()
    app.run(debug=True)