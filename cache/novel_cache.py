"""
novel_cache.py

This module provides caching functionality for the NovelDownloader.
It uses SQLite to store novel information and chapter content.
"""

import sqlite3
import os
import json
import base64

class NovelCache:
    def __init__(self, novel_title):
        cache_dir = os.path.join(os.path.dirname(__file__), 'db')
        os.makedirs(cache_dir, exist_ok=True)
        # Sanitize the novel title to create a valid filename
        sanitized_title = ''.join(c if c.isalnum() or c in (' ', '_') else '_' for c in novel_title)
        self.db_name = os.path.join(cache_dir, f"{sanitized_title}.db")
        print(f"Using database file: {self.db_name}")
        try:
            self.connection = sqlite3.connect(self.db_name)
        except sqlite3.Error as e:
            print(f"Error opening database file: {e}")
            raise
        self.cursor = self.connection.cursor()
        self._init_tables()

    def _init_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS novel_info
            (key TEXT PRIMARY KEY, value TEXT)
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters
            (url TEXT PRIMARY KEY, title TEXT, content TEXT)
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS images
            (url TEXT PRIMARY KEY, filename TEXT, data BLOB)
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

    def cache_chapter(self, url, title, content, images=None):
        """Cache chapter content and its images"""
        # Cache the chapter content
        self.cursor.execute(
            "INSERT OR REPLACE INTO chapters (url, title, content) VALUES (?, ?, ?)",
            (url, title, content)
        )
        
        # Cache the images if provided
        if images:
            for filename, img_data in images:
                self.cursor.execute(
                    "INSERT OR REPLACE INTO images (url, filename, data) VALUES (?, ?, ?)",
                    (filename, filename, img_data)
                )
        
        self.connection.commit()

    def get_cached_chapter(self, url):
        """Get cached chapter content and its images"""
        # Get chapter content
        self.cursor.execute(
            "SELECT title, content FROM chapters WHERE url = ?",
            (url,)
        )
        chapter = self.cursor.fetchone()
        if not chapter:
            return None
            
        title, content = chapter
        
        # Get all images referenced in the content
        images = []
        self.cursor.execute("SELECT filename, data FROM images")
        for filename, img_data in self.cursor.fetchall():
            if f"images/{filename}" in content:
                images.append((filename, img_data))
        
        return title, content, images

    def get_cached_image(self, url):
        """Get cached image by URL"""
        self.cursor.execute(
            "SELECT filename, data FROM images WHERE url = ?",
            (url,)
        )
        return self.cursor.fetchone()

    def cache_image(self, url, filename, img_data):
        """Cache a single image"""
        self.cursor.execute(
            "INSERT OR REPLACE INTO images (url, filename, data) VALUES (?, ?, ?)",
            (url, filename, img_data)
        )
        self.connection.commit()

    def get_all_cached_chapters(self):
        """Get all cached chapters with their images"""
        self.cursor.execute("SELECT url, title, content FROM chapters")
        chapters = []
        for url, title, content in self.cursor.fetchall():
            # Get images for this chapter
            images = []
            self.cursor.execute("SELECT filename, data FROM images")
            for filename, img_data in self.cursor.fetchall():
                if f"images/{filename}" in content:
                    images.append((filename, img_data))
            chapters.append((url, title, content, images))
        return chapters

    def close(self):
        self.connection.close()