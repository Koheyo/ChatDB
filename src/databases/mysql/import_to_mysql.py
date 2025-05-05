import json
from datetime import datetime

import mysql.connector

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="Movie",
    ssl_disabled=True  # Disable SSL
)
cursor = conn.cursor()

# Import director data
with open("merged_directors.json", encoding="utf-8") as f:
    directors = json.load(f)

name_to_director_id = {}
for d in directors:
    cursor.execute("""
        INSERT IGNORE INTO directors (name, birthname, birthdate, birthplace)
        VALUES (%s, %s, %s, %s)
    """, (
        d.get("name"),
        d.get("birthname"),
        d.get("birthdate"),
        d.get("birthplace")
    ))
conn.commit()

# Map director names to their IDs
cursor.execute("SELECT director_id, name FROM directors")
for row in cursor.fetchall():
    name_to_director_id[row[1]] = row[0]

# Import actor data
with open("merged_actors.json", encoding="utf-8") as f:
    actors = json.load(f)

for a in actors:
    cursor.execute("""
        INSERT IGNORE INTO actors (name, birthname, birthdate, birthplace)
        VALUES (%s, %s, %s, %s)
    """, (
        a.get("name"),
        a.get("birthname"),
        a.get("birthdate"),
        a.get("birthplace")
    ))
conn.commit()

# Import movie data
with open("merged_movies.json", encoding="utf-8") as f:
    movies = json.load(f)

for m in movies:
    try:
        rdate = m.get("release-date", None)
        release_date = datetime.strptime(rdate, "%Y-%m-%d").date() if rdate else None

        director_name = m.get("director")
        if isinstance(director_name, list):
            director_name = director_name[0] 

        director_id = name_to_director_id.get(director_name)

        actors_json = json.dumps(m.get("actors", []), ensure_ascii=False)

        cursor.execute("""
            INSERT INTO movies (name, year, runtime, release_date, director_id, actors_json, storyline)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            m.get("name"),
            m.get("year"),
            m.get("runtime"),
            release_date,
            director_id,
            actors_json,
            m.get("storyline") or m.get("description")
        ))

    except Exception as e:
        print("Skipped erroneous movie:", m.get("name"), e)

conn.commit()
cursor.close()
conn.close()
print("MySQL data import complete!")
