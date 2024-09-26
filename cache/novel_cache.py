"""
novel_cache.py

This module provides caching functionality for the NovelDownloader.
It uses SQLite to store novel information and chapter content.
"""

import sqlite3
import os

class NovelCache:
    def __init__(self, novel_title):
        cache_dir = os.path.join(os.path.dirname(__file__), 'db')
        os.makedirs(cache_dir, exist_ok=True)
        self.db_name = os.path.join(cache_dir, f"{novel_title}.db".replace(" ", "_"))
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()
        self._init_tables()

    def _init_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS novel_info
            (key TEXT PRIMARY KEY, value TEXT)
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters
            (chapter_number INTEGER PRIMARY KEY, title TEXT, content TEXT)
        ''')
        
        self.connection.commit()

    def cache_novel_info(self, novel_info):
        for key, value in novel_info.items():
            self.cursor.execute(
                "INSERT OR REPLACE INTO novel_info (key, value) VALUES (?, ?)",
                (key, str(value))
            )
        self.connection.commit()

    def get_novel_info(self):
        self.cursor.execute("SELECT key, value FROM novel_info")
        return dict(self.cursor.fetchall())

    def cache_chapter(self, chapter_number, title, content):
        self.cursor.execute(
            "INSERT OR REPLACE INTO chapters (chapter_number, title, content) VALUES (?, ?, ?)",
            (chapter_number, title, content)
        )
        self.connection.commit()

    def get_cached_chapter(self, chapter_number):
        self.cursor.execute(
            "SELECT title, content FROM chapters WHERE chapter_number = ?",
            (chapter_number,)
        )
        return self.cursor.fetchone()

    def get_all_cached_chapters(self):
        self.cursor.execute("SELECT chapter_number, title, content FROM chapters ORDER BY chapter_number")
        return self.cursor.fetchall()

    def close(self):
        self.connection.close()