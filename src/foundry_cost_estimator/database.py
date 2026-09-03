import sqlite3

class DB():
    def __init__(self, path: str):
        self.connection = sqlite3.connect(path)

    def _make_tables(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS skus (
                
            )
        """)
