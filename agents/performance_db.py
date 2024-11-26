import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class PerformanceDB:
    """Database for tracking and learning from social media post performance"""
    
    def __init__(self, db_path: str = 'social_media_performance.db'):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Create necessary tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    post_id TEXT,
                    content_hash TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    subreddit TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    removal_reason TEXT,
                    performance_score FLOAT DEFAULT 0.0
                )
            ''')
            
            # Engagement metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS engagement_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER,
                    platform TEXT NOT NULL,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
            ''')
            
            # Content patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_content TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    avg_performance FLOAT DEFAULT 0.0,
                    last_used DATETIME,
                    cooldown_until DATETIME
                )
            ''')
            
            conn.commit()
    
    def add_post(self, platform: str, content: Dict, post_id: Optional[str] = None, subreddit: Optional[str] = None) -> int:
        """Add a new post to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            content_hash = hash(json.dumps(content, sort_keys=True))
            
            cursor.execute('''
                INSERT INTO posts (platform, post_id, content_hash, content_type, title, content, subreddit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                platform,
                post_id,
                str(content_hash),
                content.get('type', 'text'),
                content.get('title', ''),
                content.get('text', ''),
                subreddit
            ))
            
            return cursor.lastrowid
    
    def update_post_status(self, post_id: int, status: str, removal_reason: Optional[str] = None):
        """Update post status (active, removed, failed)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE posts 
                SET status = ?, removal_reason = ?
                WHERE id = ?
            ''', (status, removal_reason, post_id))
    
    def add_engagement_metrics(self, post_id: int, platform: str, metrics: Dict):
        """Record engagement metrics for a post"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO engagement_metrics (post_id, platform, likes, comments, shares, views)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                post_id,
                platform,
                metrics.get('likes', 0),
                metrics.get('comments', 0),
                metrics.get('shares', 0),
                metrics.get('views', 0)
            ))
    
    def update_pattern_performance(self, pattern_type: str, pattern_content: str, success: bool):
        """Update performance metrics for content patterns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get or create pattern
            cursor.execute('''
                INSERT OR IGNORE INTO content_patterns (pattern_type, pattern_content)
                VALUES (?, ?)
            ''', (pattern_type, pattern_content))
            
            # Update metrics
            if success:
                cursor.execute('''
                    UPDATE content_patterns
                    SET success_count = success_count + 1,
                        last_used = CURRENT_TIMESTAMP
                    WHERE pattern_type = ? AND pattern_content = ?
                ''', (pattern_type, pattern_content))
            else:
                cursor.execute('''
                    UPDATE content_patterns
                    SET failure_count = failure_count + 1,
                        last_used = CURRENT_TIMESTAMP
                    WHERE pattern_type = ? AND pattern_content = ?
                ''', (pattern_type, pattern_content))
    
    def get_best_performing_patterns(self, pattern_type: str, limit: int = 5) -> List[Dict]:
        """Get the best performing content patterns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pattern_content, success_count, failure_count, avg_performance
                FROM content_patterns
                WHERE pattern_type = ?
                AND (cooldown_until IS NULL OR cooldown_until < CURRENT_TIMESTAMP)
                ORDER BY avg_performance DESC
                LIMIT ?
            ''', (pattern_type, limit))
            
            return [
                {
                    'content': row[0],
                    'success_count': row[1],
                    'failure_count': row[2],
                    'avg_performance': row[3]
                }
                for row in cursor.fetchall()
            ]
    
    def get_post_performance(self, post_id: int) -> Dict:
        """Get comprehensive performance metrics for a post"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, 
                       e.likes, e.comments, e.shares, e.views
                FROM posts p
                LEFT JOIN engagement_metrics e ON p.id = e.post_id
                WHERE p.id = ?
                ORDER BY e.timestamp DESC
                LIMIT 1
            ''', (post_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'platform': row[1],
                    'status': row[4],
                    'performance_score': row[5],
                    'engagement': {
                        'likes': row[11],
                        'comments': row[12],
                        'shares': row[13],
                        'views': row[14]
                    }
                }
            return None
