"""Game Manager — entry point."""

import os
from db import GameDB
from ui import GameManagerApp

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'game_db.csv')

if __name__ == '__main__':
    db = GameDB(DB_PATH)
    db.load()
    app = GameManagerApp(db)
    app.run()
