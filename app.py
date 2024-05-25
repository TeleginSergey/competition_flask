from flask import Flask
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import request
from psycopg2.sql import SQL, Literal
from dotenv import load_dotenv
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
	WITH competitions_with_sports AS (
  SELECT
    c.id AS competition_id,
    c.title AS competition_title,
    c.date_of_start AS competition_start_date,
    c.date_of_end AS competition_end_date,
    cs.id AS competition_sport_id,
    s.id as sport_id,
    s.title AS sport_title,
    s.description AS sport_description
  FROM competition_schema.competitions c
  LEFT JOIN competition_schema.competition_sport cs ON c.id = cs.competition_id
  LEFT JOIN competition_schema.sports s ON cs.sport_id = s.id
),
competitions_with_stages AS (
  SELECT 
    cws.competition_id,
    cws.competition_title,
    cws.competition_start_date,
    cws.competition_end_date,
    cws.sport_id,
    cws.sport_title,
    cws.sport_description,
    coalesce(json_agg(json_build_object(
        'stage_title', st.title,
        'stage_date', st.date,
        'stage_place', st.place
    )) filter (where st.title is not null), '[]') AS stage_info
  FROM competitions_with_sports cws
  LEFT JOIN competition_schema.stages st ON cws.competition_sport_id = st.competition_sport_id
  GROUP BY competition_id, competition_title, competition_start_date, competition_end_date, sport_id, sport_title, sport_description
)
SELECT 
    competition_id, 
    competition_title, 
    competition_start_date, 
    competition_end_date,
    coalesce(json_agg(json_build_object(
        'sport_title', sport_title,
        'sport_description', sport_description, 
        'stages', stage_info
    )) filter (where sport_title is not null), '[]') AS sports
FROM competitions_with_stages
GROUP BY competition_id, competition_title, competition_start_date, competition_end_date;
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

    if date_of_start and date_of_end and date_of_end > date_of_start:
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
    deleteCompetition = SQL("delete from competition_schema.competitions where id = {id} returning id").format(
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
	WITH competitions_with_sports AS (
  SELECT
    c.id AS competition_id,
    c.title AS competition_title,
    c.date_of_start AS competition_start_date,
    c.date_of_end AS competition_end_date,
    cs.id AS competition_sport_id,
    s.id as sport_id,
    s.title AS sport_title,
    s.description AS sport_description
  FROM competition_schema.sports s
  LEFT JOIN competition_schema.competition_sport cs ON s.id = cs.sport_id
  LEFT JOIN competition_schema.competitions c ON cs.competition_id = c.id
),
sports_with_stages AS (
  SELECT 
    cws.competition_id,
    cws.competition_title,
    cws.competition_start_date,
    cws.competition_end_date,
    cws.sport_id,
    cws.sport_title,
    cws.sport_description,
    coalesce(json_agg(json_build_object(
        'stage_title', st.title,
        'stage_date', st.date,
        'stage_place', st.place
    )) filter (where st.title is not null), '[]') AS stage_info
  FROM competitions_with_sports cws
  LEFT JOIN competition_schema.stages st ON cws.competition_sport_id = st.competition_sport_id
  GROUP BY sport_id, sport_title, sport_description, competition_id, competition_title, competition_start_date, competition_end_date
)
SELECT 
    sport_id, 
    sport_title, 
    sport_description, 
    coalesce(json_agg(json_build_object(
        'competition_title', competition_title,
        'competition_start_date', competition_start_date,
        'competition_end_date', competition_end_date,
        'stages', stage_info
    )) filter (where competition_title is not null), '[]') AS competitions
FROM sports_with_stages
GROUP BY sport_id, sport_title, sport_description;
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
    deleteSport = SQL("delete from competition_schema.sports where id = {id} returning id").format(
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
            cs.id,
            cs.competition_id,
            cs.sport_id
        from competition_schema.competition_sport cs
        join competition_schema.stages s on s.competition_sport_id = cs.id
    ),
    competition_titles as (
        select
            cpi.id as comp_sport_id,
            c.title as comp_title
        from competition_schema.competitions c
        join comp_sport_ids cpi on c.id = cpi.competition_id
    ),
    sport_titles as (
        select
            cpi.id as comp_sport_id,
            s.title as sport_title
        from competition_schema.sports s
        join comp_sport_ids cpi on s.id = cpi.sport_id
    )
    select
        s.id,
        s.title,
        s.date,
        s.place,
        st.sport_title,
        ct.comp_title
    from competition_schema.stages s
    left join competition_titles ct on s.competition_sport_id = ct.comp_sport_id
    left join sport_titles st on s.competition_sport_id = st.comp_sport_id;
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    return result

@app.get("/competition_sport")
def get_competition_sport():
    query = SQL(
    """
    select
        cs.id,
        c.title as competition_title,
        s.title as sport_title
    from competition_schema.competition_sport cs
    join competition_schema.competitions c on c.id = cs.competition_id
    join competition_schema.sports s on s.id = cs.sport_id;
    """
    )
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

    query_for_create = SQL("""
    insert into competition_schema.stages(title, date, place, competition_sport_id)
    values ({title}, {date}, {place}, {competition_sport_id})
    returning id
    """).format(
        title=Literal(title),
        date=Literal(date),
        place=Literal(place),
        competition_sport_id=Literal(competition_sport_id),
    )

    with connection.cursor() as cursor:
        cursor.execute(query_for_create)
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
    update competition_schema.stages
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

    deleteStage = SQL("delete from competition_schema.stages where id = {id} returning id").format(
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
