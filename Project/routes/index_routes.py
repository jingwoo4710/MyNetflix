import numpy as np
from flask import Blueprint, render_template
from Project.models import db
from Project.models import Movies
import csv
from embedding_as_service_client import EmbeddingClient
from sklearn.linear_model import LogisticRegression
import pickle


index_routes = Blueprint('index_routes', __name__)

# Encoder
en = EmbeddingClient(host='54.180.124.154', port=8989)


# '/'
@index_routes.route('/')
def index():
    return render_template('index.html')


@index_routes.route('/data/')
def data():
    # 데이터베이스 초기화
    db.drop_all()
    db.create_all()

    # CSV파일 불러오고, 데이터 베이스에 저장
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


    # 장르를 통해서 유사한 영화제목을 예측
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

    # 모델 저장
    pickle.dump(model, open('model.pkl', 'wb'))

    return render_template('index.html')