from flask_sqlalchemy import SQLAlchemy
import csv


db = SQLAlchemy()           

class Users(db.Model): 
    __tablename__ = 'Users'   
    id = db.Column(db.String, primary_key = True)  
    password = db.Column(db.String(64))     
    movie = db.Column(db.String)

    def __repr__(self):
        return "< ID : {} --- PWD : {} >".format(self.id, self.password)


class Movies(db.Model):
    __tablename__ = 'Movies'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String)
    genres = db.Column(db.String)
    embedding = db.Column(db.PickleType) 
    release_date = db.Column(db.String)
    runtime = db.Column(db.Float)
    score = db.Column(db.Float)

    def __repr__(self):
        return "< Movie Name : {} >".format(self.lastname)


class Lists(db.Model):
    __tablename__ = "Lists"
    id = db.Column(db.Integer, primary_key = True)
    user = db.Column(db.String, db.ForeignKey("Users.id"))
    movie = db.Column(db.String, db.ForeignKey("Movies.title"))

    users = db.relationship("Users", foreign_keys=user)
    movies = db.relationship("Movies", foreign_keys=movie)

    def __repr__(self):
        return "< id : {} -- Movie : {} >".format(self.lastname, self.movie)



    

def get_recommend_movie_list(df, movie_title, gerne_c_sim, top=30):
    # 특정 영화와 비슷한 영화를 추천해야 하기 때문에 '특정 영화' 정보를 뽑아낸다.
    target_movie_index = df[df['title'] == movie_title].index.values
    
    #코사인 유사도 중 비슷한 코사인 유사도를 가진 정보를 뽑아낸다.
    sim_index = gerne_c_sim[target_movie_index, :top].reshape(-1)
    #본인을 제외
    sim_index = sim_index[sim_index != target_movie_index]

    #data frame으로 만들고 vote_count으로 정렬한 뒤 return
    result = df.iloc[sim_index].sort_values('score', ascending=False)[:10]
    
    return result