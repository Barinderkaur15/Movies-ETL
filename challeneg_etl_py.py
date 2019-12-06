import json
import pandas as pd
import numpy as np
#importing built in Regualr expression file 
import re
import sqlalchemy as db
from sqlalchemy import create_engine
from sqlalchemy import delete
import psycopg2
from config import db_password
import time
#Funtion will assign_varaiable()
def assign_varaiable():
    file_dir='C:/Users/kaurb/OneDrive/Desktop/class Folder/Movies-ETL'
    try:
        with open(f'{file_dir}/wikipedia-movies.json', mode='r') as file:
            wiki_movies_raw = json.load(file)
        kaggle_metadata = pd.read_csv(f'{file_dir}/movies_metadata.csv',low_memory=False)
        ratings = pd.read_csv(f'{file_dir}/ratings.csv')
    except IOError:
        print('Error')
 #Will retun three varaible        
    return(wiki_movies_raw,kaggle_metadata,ratings)
#assign_varaiable()
#Funtion for transforming the data 

def Transform_data(wiki,kaggle,rating):
 #converting wiki raw into dataframe 
    wiki_movies_df = pd.DataFrame(wiki)   
    wiki_movies = [movie for movie in wiki
                   if ('Director' in movie or 'Directed by' in movie)
                       and 'imdb_link' in movie
                       and 'No. of episodes' not in movie]
    def clean_movie(movie):
    # adding Constructor to create copy of movies 
        movie = dict(movie) #create a non-destructive copy
        alt_titles={}
        for key in ['Also known as','Arabic','Cantonese','Chinese','French',
                'Hangul','Hebrew','Hepburn','Japanese','Literally',
                'Mandarin','McCune–Reischauer','Original title','Polish',
                'Revised Romanization','Romanized','Russian',
                'Simplified','Traditional','Yiddish']:
            if key in movie:    # Pop Funtion to remove the key value pair
                alt_titles[key] = movie[key]
                movie.pop(key)
        if len(alt_titles) > 0:
             movie['alt_titles'] = alt_titles
        def change_column_name(old_name, new_name):
            if old_name in movie:
               movie[new_name] = movie.pop(old_name)
        change_column_name('Adaptation by', 'Writer(s)')
        change_column_name('Country of origin', 'Country')
        change_column_name('Directed by', 'Director')
        change_column_name('Distributed by', 'Distributor')
        change_column_name('Edited by', 'Editor(s)')
        change_column_name('Length', 'Running time')
        change_column_name('Original release', 'Release date')
        change_column_name('Music by', 'Composer(s)')
        change_column_name('Produced by', 'Producer(s)')
        change_column_name('Producer', 'Producer(s)')
        change_column_name('Productioncompanies ', 'Production company(s)')
        change_column_name('Productioncompany ', 'Production company(s)')
        change_column_name('Released', 'Release Date')
        change_column_name('Release Date', 'Release date')
        change_column_name('Screen story by', 'Writer(s)')
        change_column_name('Screenplay by', 'Writer(s)')
        change_column_name('Story by', 'Writer(s)')
        change_column_name('Theme music composer', 'Composer(s)')
        change_column_name('Written by', 'Writer(s)')
        return movie
    #Adding Clean Movie inlist 
    clean_movies = [clean_movie(movie) for movie in wiki_movies]
    wiki_movies_df = pd.DataFrame(clean_movies)
    sorted(wiki_movies_df.columns.tolist())
    # addig regular expression 
    wiki_movies_df['imdb_id'] = wiki_movies_df['imdb_link'].str.extract(r'(tt\d{7})')
    #Using subset function to consider only imdb
    wiki_movies_df.drop_duplicates(subset='imdb_id', inplace=True)
    [[column,wiki_movies_df[column].isnull().sum()] for column in wiki_movies_df.columns]
    [column for column in wiki_movies_df.columns if wiki_movies_df[column].isnull().sum() < len(wiki_movies_df) * 0.9]
    wiki_columns_to_keep = [column for column in wiki_movies_df.columns if wiki_movies_df[column].isnull().sum() < len(wiki_movies_df) * 0.9]
    wiki_movies_df = wiki_movies_df[wiki_columns_to_keep]
    #Cleaning data type : 
    #step1 : Remove NA values from the column 
    box_office = wiki_movies_df['Box office'].dropna() 
    box_office[box_office.map(lambda x: type(x) != str)]
    #Joing the data 
    box_office = box_office.apply(lambda x: ' '.join(x) if type(x) == list else x)
    
    def parse_dollars(s):
    # if s is not a string, return NaN
     if type(s) != str:
        return np.nan
    # if input is of the form $###.# million
     if re.match(r'\$\s*\d+\.?\d*\s*milli?on', s, flags=re.IGNORECASE):
        # remove dollar sign and " million"
        s = re.sub('\$|\s|[a-zA-Z]','', s)
        # convert to float and multiply by a million
        value = float(s) * 10**6
        # return value
        return value

    # if input is of the form $###.# billion
     elif re.match(r'\$\s*\d+\.?\d*\s*billi?on', s, flags=re.IGNORECASE):
        # remove dollar sign and " billion"
        s = re.sub('\$|\s|[a-zA-Z]','', s)
        # convert to float and multiply by a billion
        value = float(s) * 10**9
        # return value
        return value

    # if input is of the form $###,###,###
     elif re.match(r'\$\s*\d{1,3}(?:[,\.]\d{3})+(?!\s[mb]illion)',s,flags=re.IGNORECASE):
        # remove dollar sign and commas
        s = re.sub('\$|,','', s)
        # convert to float
        value = float(s)
        # return value
        return value
    # otherwise, return NaN
     else:
        return np.nan
    form_one = r'\$\s*\d+\.?\d*\s*[mb]illion'
    form_two = r'\$\s*\d{1,3}(?:,\d{3})+'
    wiki_movies_df['box_office'] = box_office.str.extract(f'({form_one}|{form_two})', flags=re.IGNORECASE)[0].apply(parse_dollars)
    wiki_movies_df.drop('Box office', axis=1, inplace=True)
    budget = wiki_movies_df['Budget'].dropna()
    budget = budget.map(lambda x: ' '.join(x) if type(x) == list else x)
    budget = budget.str.replace(r'\$.*[-—–](?![a-z])', '$', regex=True)
    budget = budget.str.replace(r'\[\d+\]\s*', '')
    #Practice 
    matches_form_one = budget.str.contains(form_one, flags=re.IGNORECASE)
    matches_form_two = budget.str.contains(form_two, flags=re.IGNORECASE)
    budget[~matches_form_one & ~matches_form_two]
    budget[~matches_form_one & ~matches_form_two]
    wiki_movies_df['budget'] = budget.str.extract(f'({form_one}|{form_two})', flags=re.IGNORECASE)[0].apply(parse_dollars)
    wiki_movies_df.drop('Budget', axis=1, inplace=True)
    release_date = wiki_movies_df['Release date'].dropna().apply(lambda x: ' '.join(x) if type(x)== list else x)
    date_form_one = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s[123]\d,\s\d{4}'
    date_form_two = r'\d{4}.[01]\d.[123]\d'
    date_form_three = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}'
    date_form_four = r'\d{4}'
    release_date.str.extract(f'({date_form_one}|{date_form_two}|{date_form_three}|{date_form_four})', flags=re.IGNORECASE)
    wiki_movies_df['release_date'] = pd.to_datetime(release_date.str.extract(f'({date_form_one}|{date_form_two}|{date_form_three}|{date_form_four})')[0], infer_datetime_format=True)
    running_time = wiki_movies_df['Running time'].dropna().apply(lambda x: ' '.join(x) if type(x) == list else x)
    running_time[running_time.str.contains(r'^\d*\s*m', flags=re.IGNORECASE) != True]
    running_time_extract = running_time.str.extract(r'(\d+)\s*ho?u?r?s?\s*(\d*)|(\d+)\s*m')
    running_time_extract = running_time_extract.apply(lambda col: pd.to_numeric(col, errors='coerce')).fillna(0)
    wiki_movies_df['running_time'] = running_time_extract.apply(lambda row: row[0]*60 + row[1] if row[2] == 0 else row[2], axis=1)
    wiki_movies_df.drop('Running time', axis=1, inplace=True)
    #Checking if DF is working 
    #df=wiki_movies_df
    #Working with kaggle data , not taking the adult film
    kaggle[~kaggle['adult'].isin(['True','False'])]
    kaggle = kaggle[kaggle['adult'] == 'False'].drop('adult',axis='columns')
    kaggle['video'] = kaggle['video'] == 'True'
    kaggle['budget'] = kaggle['budget'].astype(int)
    kaggle['id'] = pd.to_numeric(kaggle['id'], errors='raise')
    kaggle['popularity'] = pd.to_numeric(kaggle['popularity'], errors='raise')
    kaggle['release_date'] = pd.to_datetime(kaggle['release_date'])
    pd.to_datetime(rating['timestamp'], unit='s')
    ratings['timestamp'] = pd.to_datetime(ratings['timestamp'], unit='s')
    movies_df = pd.merge(wiki_movies_df, kaggle, on='imdb_id', suffixes=['_wiki','_kaggle'])
    #checking part 2 
    movies_df[movies_df['title_wiki'] != movies_df['title_kaggle']][['title_wiki','title_kaggle']]
    movies_df[(movies_df['title_kaggle'] == '') | (movies_df['title_kaggle'].isnull())]
    movies_df[(movies_df['release_date_wiki'] > '1996-01-01') & (movies_df['release_date_kaggle'] < '1965-01-01')]
    movies_df[(movies_df['release_date_wiki'] > '1996-01-01') & (movies_df['release_date_kaggle'] < '1965-01-01')].index
    movies_df = movies_df.drop(movies_df[(movies_df['release_date_wiki'] > '1996-01-01') & (movies_df['release_date_kaggle'] < '1965-01-01')].index)
    movies_df[movies_df['release_date_wiki'].isnull()]
    def fill_missing_kaggle_data(df, kaggle_column, wiki_column):
        df[kaggle_column] = df.apply(
        lambda row: row[wiki_column] if row[kaggle_column] == 0 else row[kaggle_column]
        , axis=1)
        df.drop(columns=wiki_column, inplace=True)
    fill_missing_kaggle_data(movies_df, 'runtime', 'running_time')
    fill_missing_kaggle_data(movies_df, 'budget_kaggle', 'budget_wiki')
    fill_missing_kaggle_data(movies_df, 'revenue', 'box_office')
    movies_df = movies_df[['imdb_id','id','title_kaggle','original_title','tagline','belongs_to_collection','url','imdb_link',
                       'runtime','budget_kaggle','revenue','release_date_kaggle','popularity','vote_average','vote_count',
                       'genres','original_language','overview','spoken_languages','Country',
                       'production_companies','production_countries','Distributor',
                       'Producer(s)','Director','Starring','Cinematography','Editor(s)','Writer(s)','Composer(s)','Based on'
                      ]]
    movies_df.rename({'id':'kaggle_id',
                  'title_kaggle':'title',
                  'url':'wikipedia_url',
                  'budget_kaggle':'budget',
                  'release_date_kaggle':'release_date',
                  'Country':'country',
                  'Distributor':'distributor',
                  'Producer(s)':'producers',
                  'Director':'director',
                  'Starring':'starring',
                  'Cinematography':'cinematography',
                  'Editor(s)':'editors',
                  'Writer(s)':'writers',
                  'Composer(s)':'composers',
                  'Based on':'based_on'
                 }, axis='columns', inplace=True)
    
    #df=movies_df
    #Transforming the rating data and merging data  
    rating_counts = rating.groupby(['movieId','rating'], as_index=False).count() \
                .rename({'userId':'count'}, axis=1)
    rating_counts.columns = ['rating_' + str(col) for col in rating_counts.columns]
    movies_with_ratings_df = pd.merge(movies_df, rating_counts, left_on='kaggle_id', right_index=True, how='left')
    movies_with_ratings_df[rating_counts.columns] = movies_with_ratings_df[rating_counts.columns].fillna(0)
    df=movies_df
    return df
#function to create SQL engine 
def load_SQl(movie_dataset):
    db_string = f"postgres://postgres:{db_password}@127.0.0.1:5432/movie_data"
    engine = create_engine(db_string)  
    return(engine) 
#chacking if function is loading properly
load_SQl(movie_dataset)
# Automating the complete process and using Try and Except .
#This function will call all the function and in order to make a sequential form ,
#various try and except statement are used and results from one block is used as input for other 
def Automate_the_process():
    try:
        wiki_movies_raw,kaggle_metadata,ratings=assign_varaiable()
    except EOFError as ex:
        print("Caught the EOF error.")
        raise ex
    except IOError as e:
        print("Caught the I/O error.")
        raise ex 
    try:
        movie_dataset=Transform_data(wiki=wiki_movies_raw,kaggle=kaggle_metadata, rating=ratings)
    except EOFError as ex:
        print("Caught the EOF error.")
        raise ex
    except IOError as e:
        print("Caught the I/O error.")
        raise ex
    try:
        engine=load_SQl(movie_dataset)
        connection = engine.connect()
        metadata = db.MetaData()
        users=db.Table('movies',metadata, autoload=True, autoload_with=engine)
        #Executing delete query as we only want to delete data and keep the table structure
        query=db.delete(users)
        connection.execute(query)
        movie_dataset.to_sql(name='movies',con=engine,if_exists='append')
        users_2=db.Table('ratings',metadata, autoload=True, autoload_with=engine)
        query_2=db.delete(users_2)
        connection.execute(query_2)
        for data in pd.read_csv('C:/Users/kaurb/OneDrive/Desktop/class Folder/Movies-ETL/ratings.csv', chunksize=1000):
            data.to_sql(name='ratings', con=engine, if_exists='append')
    except OperationalError:
        print("OperationalError: Unable to connect to MySQL database.")
        raise 
    return movie_dataset