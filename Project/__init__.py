import numpy as np
import pandas as pd
from flask import Flask
from flask import request
from flask import redirect   
from flask import render_template
from flask import session
from flask.helpers import url_for
from Project.models import Lists, db, migrate
from Project.models import Users, Movies, get_recommend_movie_list
import requests
import json, csv
from embedding_as_service_client import EmbeddingClient
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from random import *

en = EmbeddingClient(host='54.180.124.154', port=8989)


def create_app():
    app = Flask(__name__)


    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://jzldammovjblxe:3786b05155a588f1097c298f227121cbb08740f95e6dca5df61498e7f9138d86@ec2-75-101-212-64.compute-1.amazonaws.com:5432/d55tm2dunhdufa'   
    # "postgres://jzldammovjblxe:3786b05155a588f1097c298f227121cbb08740f95e6dca5df61498e7f9138d86@ec2-75-101-212-64.compute-1.amazonaws.com:5432/d55tm2dunhdufa"
    #'sqlite:///netflix.sqlite3'   
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = "Random"

    db.init_app(app)
    migrate.init_app(app, db)

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
            return redirect(url_for('login'))
        else:
            return render_template('signup.html')


    @app.route('/login', methods=['GET','POST'])  
    def login():
        session.pop('email', None)
        session.pop('password', None)
        if request.method == "POST":
            result = request.form
            print(dict(result))

            email = Users.query.with_entities(Users.id).filter(Users.id == result['email']).first()
            password = Users.query.with_entities(Users.password).filter(Users.id == result['email']).first()        
            print(email, password)

            if (email[0] == result['email']) & (password[0] == result['password']):
                session['email'] = result['email']
                session['password'] = result['password']

                return redirect(url_for('main'))

        return render_template('login.html')

        
    @app.route('/')
    def index():
        return render_template('index.html')

    
    @app.route('/trend/') 
    def trend():
        baseurl = "https://api.themoviedb.org/3/movie/popular?api_key=7d50009b07e23a75929271ef0133707b&language=en-EN&page=1"
        response = requests.get(baseurl)
        data = json.loads(response.text)
        data = data['results']
        original_title = []
        for movie in data:
            original_title.append(movie['original_title'])

        pred_title = []
        pred_poster = []

        baseurl2 = "http://www.omdbapi.com/?i=tt3896198&apikey=d5202ac"
        for title in original_title:
            params_diction = {}
            params_diction['t'] = title
            params_diction['r'] = 'json'
            response2 = requests.get(baseurl2, params=params_diction)
            res = json.loads(response2.text)
            if res['Response'] == 'True':
                pred_title.append(res['Title'])
                pred_poster.append(res['Poster'])

        rand = sample(range(len(pred_title)), 5)

        return render_template('trend.html', image1 = pred_poster[rand[0]], image2 = pred_poster[rand[1]], image3 = pred_poster[rand[2]], image4 = pred_poster[rand[3]], image5 = pred_poster[rand[4]])

        


    @app.route('/main/', methods=['GET','POST']) 
    def main():
        # 넘겨온 값 확인
        # print(request.args.get('email'))
        # session['email'] = request.args.get('email')
        
        # 데이터베이스에서 검색
        movie = Users.query.with_entities(Users.movie).filter(Users.id == session['email']).first()
        print(movie[0])

        # OMDB를 통해 영화정보 확인
        baseurl = 'http://www.omdbapi.com/?i=tt3896198&apikey=d5202ac' #Enter your API key here

        if Lists.query.filter(Lists.user == session['email']).first():
            params_diction = {}
            params_diction['t'] = Lists.query.filter(Lists.user == session['email']).order_by(Lists.id.desc()).first().movie
            params_diction['r'] = 'json'
            response = requests.get(baseurl, params=params_diction)
            data = json.loads(response.text)
            print('Lists updated')
            title = data['Title']
            genre = data['Genre']
        
        else:
            params_diction = {}
            params_diction['t'] = movie[0]
            params_diction['r'] = 'json'
            response = requests.get(baseurl, params=params_diction)
            data = json.loads(response.text)
            print('Normal updated')
            title = data['Title']
            genre = data['Genre']
        
        
        
        # 로지스틱 분석 모델
        model = pickle.load(open('model.pkl', 'rb'))
        prediction = model.predict(en.encode(texts =[genre]))[0]
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

        # moive.csv 파일 불러오기
        df = pd.read_csv('Project/movie.csv')

        # Str to Vec Instance
        count_vector = CountVectorizer(ngram_range=(1, 3))

        # 결측치 제거
        df = df.dropna()

        # Str to Vec
        c_vector_genres = count_vector.fit_transform(df['genres'])
        print(c_vector_genres.shape)
        gerne_c_sim = cosine_similarity(c_vector_genres, c_vector_genres).argsort()[:, ::-1]

        # Get Recommend movie list 5
        df2 = get_recommend_movie_list(df, movie_title=movie[0], gerne_c_sim=gerne_c_sim)
        rec_titles = df2.title.to_list()[:5]
        print("Recommend Success!")
        
        # List append and Save it in the Lists table
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
            list.user = session['email']
            list.movie = data['Title']

            # Commit
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

        return render_template('index.html')

    @app.route('/update/', methods=['GET','POST'])  
    def update():
        if request.method == "POST":
            result = request.form
            print(dict(result))       
        
            if session['password'] == result['password']:
                user = Users.query.get(session['email'])
                user.movie = result['movie']
                db.session.commit()
                return redirect(url_for('main'))

        return render_template('update.html')

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)