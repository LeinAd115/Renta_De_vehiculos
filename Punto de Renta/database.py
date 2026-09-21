import mysql.connector
from contextlib import contextmanager

class DatabaseConnection:
    def __init__(self, host="localhost", user="root", password="Kimberly", database="sistema_rentas", port=3307):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port,
            'autocommit': False
        }

    @contextmanager
    def get_connection(self):
        conn = mysql.connector.connect(**self.config)
        try:
            yield conn
        finally:
            if conn.is_connected():
                conn.close()