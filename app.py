from flask import Flask
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import request
from psycopg2.sql import SQL, Literal
from dotenv import load_dotenv
from datetime import datetime, timezone
import os

load_dotenv()


app = Flask(__name__)
app.json.ensure_ascii = False

connection = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST') if os.getenv('DEBUG_MODE') == 'false' else 'localhost',
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    cursor_factory=RealDictCursor
)
connection.autocommit = True


@app.get("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.get("/competitions")
def get_competitions():
    query = """
	select
	  c.id,
	  c.title,
	  c.date_of_start,
	  c.date_of_end,
	  coalesce(jsonb_agg(jsonb_build_object(
	    'id', s.id, 'title', s.title, 'description', s.description))
	      filter (where s.id is not null), '[]') as sports
	from competition_schema.competitions c
	left join competition_schema.competition_sport cs on c.id = cs.competition_id
	left join competition_schema.sports s on s.id = cs.sport_id
	group by c.id
"""

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    return result


@app.post('/competitions/create')
def create_competition():
    body: dict = request.json

    title = body.get('title')

    if not title:
        return 'Field title is required', 400

    date_of_start = body.get('date_of_start')
    date_of_end = body.get('date_of_end')
    
    if date_of_start and date_of_end and date_of_end < date_of_start:
        return "Start date of competition can't be later than end date", 400

    query = SQL("""
    insert into competition_schema.competitions(title, date_of_start, date_of_end)
    values ({title}, {date_of_start}, {date_of_end})
    returning id
    """).format(
        title=Literal(title),
        date_of_start=Literal(date_of_start),
        date_of_end=Literal(date_of_end),
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchone()

    return result


@app.post('/competitions/update')
def update_competition():
    body: dict = request.json

    id = body.get('id')
    title = body.get('title')
    
    if not id or not title:
        return 'Fields id and title are required', 400

    date_of_start = body.get('date_of_start')
    date_of_end = body.get('date_of_end')

    if date_of_end > date_of_start:
        return "Start date of competition can't be later than end date", 400

    query = SQL("""
    update competition_schema.competitions
    set 
      title = {title}, 
      date_of_start = {date_of_start},
      date_of_end = {date_of_end}
    where id = {id}
    returning id
    """).format(
        title=Literal(title),
        date_of_start=Literal(date_of_start),
        date_of_end=Literal(date_of_end),
        id=Literal(id),
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    if len(result) == 0:
        return '', 404

    return '', 204


@app.delete('/competitions/delete')
def delete_competition():
    body: dict = request.json

    id = body.get('id')
    
    if not id:
        return 'Field id is required', 400

    deleteCompetitionLinks = SQL(
        "delete from competition_schema.competition_sport where competition_id = {id}").format(
            id=Literal(id),
    )
    deleteCompetition = SQL("delete from competition_sport.competitions where id = {id} returning id").format(
        id=Literal(id),
    )

    with connection.cursor() as cursor:
        cursor.execute(deleteCompetitionLinks)
        cursor.execute(deleteCompetition)
        result = cursor.fetchall()

    if len(result) == 0:
        return '', 404

    return '', 204





@app.get("/sports")
def get_sports():
    query = """
	select
	  s.id,
	  s.title,
	  s.description,
	  coalesce(jsonb_agg(jsonb_build_object(
	    'id', c.id, 'title', c.title, 'date_of_start', c.date_of_start, 'date_of_end', c.date_of_end))
	      filter (where s.id is not null), '[]') as competitions
	from competition_schema.sports s
	left join competition_schema.competition_sport cs on s.id = cs.sport_id
	left join competition_schema.competitions c on c.id = cs.competition_id
	group by s.id
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    return result


@app.post('/sports/create')
def create_sport():
    body: dict = request.json

    title = body.get('title')

    if not title:
        return 'Field title is required', 400

    description = body.get('description')

    query = SQL("""
    insert into competition_schema.sports(title, description)
    values ({title}, {description})
    returning id
    """).format(
        title=Literal(title),
        description=Literal(description),
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchone()

    return result


@app.post('/sports/update')
def update_sport():
    body: dict = request.json

    id = body.get('id')
    title = body.get('title')

    if not id or not title:
        return 'Fields id and title are required', 400

    description = body.get('description')

    query = SQL("""
    update competition_schema.sports
    set 
      title = {title}, 
      description = {description}
    where id = {id}
    returning id
    """).format(
        title=Literal(title),
        description=Literal(description),
        id=Literal(id),
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    if len(result) == 0:
        return '', 404

    return '', 204


@app.delete('/sports/delete')
def delete_sport():
    body: dict = request.json

    id = body.get('id')

    if not id:
        return 'Field id is required', 400

    deleteSportLinks = SQL(
        "delete from competition_schema.competition_sport where sport_id = {id}").format(
            id=Literal(id),
    )
    deleteSport = SQL("delete from competition_sport.sports where id = {id} returning id").format(
        id=Literal(id),
    )

    with connection.cursor() as cursor:
        cursor.execute(deleteSportLinks)
        cursor.execute(deleteSport)
        result = cursor.fetchall()

    if len(result) == 0:
        return '', 404

    return '', 204




@app.get("/stages")
def get_stages():
    query = """
    with comp_sport_ids as (
        select
            competition_id,
            sport_id
        from competition_sport cs
        join stages s on s.competition_sport_id = cs.id
    ),
    competition_title as (
        select
            title as comp_title
        from competitions c
        where c.id = comp_sport_ids.competition_id
    ),
    sport_title as (
        select
            title as sport_title
        from sports s
        where s.id = comp_sport_ids.sport_id
    )
	select
	    id,
	    title,
	    date,
        place,
        sport_title,
        competition_title
	from competition_schema.stages
	group by id
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    return result


@app.post('/stages/create')
def create_stage():
    body: dict = request.json

    title = body.get('title')

    if not title:
        return 'Field title is required', 400

    date = body.get('date')
    place = body.get('place')
    competition_sport_id = body.get('competition_sport_id')

    query = SQL("""
    insert into competition_schema.sports(title, date, place, competition_sport_id, created, modified)
    values ({title}, {date}, {place}, {competition_sport_id}, {created}, {modified})
    returning id
    """).format(
        title=Literal(title),
        date=Literal(date),
        place=Literal(place),
        competition_sport_id=Literal(competition_sport_id),
        created=datetime.now(timezone.utc),
        modified=datetime.now(timezone.utc),
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchone()

    return result


@app.post('/stages/update')
def update_stage():
    body: dict = request.json

    id = body.get('id')
    title = body.get('title')
    
    if not id or not title:
        return 'Fields id and title are required', 400

    date = body.get('date')
    place = body.get('place')
    competition_sport_id = body.get('competition_sport_id')

    query = SQL("""
    update competition_schema.sports
    set 
        title = {title}, 
        date = {date},
        place = {place},
        competition_sport_id = {competition_sport_id}
    where id = {id}
    returning id
    """).format(
        title=Literal(title),
        date=Literal(date),
        place=Literal(place),
        competition_sport_id=Literal(competition_sport_id),
        id=Literal(id),
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    if len(result) == 0:
        return '', 404

    return '', 204


@app.delete('/stages/delete')
def delete_stage():
    body: dict = request.json

    id = body.get('id')
    if not id:
        return 'Field id is required', 400

    deleteStage = SQL("delete from competition_sport.stages where id = {id} returning id").format(
        id=Literal(id)
    )

    with connection.cursor() as cursor:
        cursor.execute(deleteStage)
        result = cursor.fetchall()

    if len(result) == 0:
        return '', 404

    return '', 204

if __name__ == '__main__':
    app.run(port=os.getenv('FLASK_PORT'))
