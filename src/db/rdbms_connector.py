# Handles MySQL/PostgreSQL database connection
import pymysql


def connect_to_rdbms():
    """Establishes a connection to an RDBMS."""
    return pymysql.connect(host="localhost", user="root", password="Dsci-551", database="dsci551")
