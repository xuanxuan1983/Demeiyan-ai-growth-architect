import psycopg2
from psycopg2.extensions import connection
import os
from datetime import datetime
from typing import List, Dict, Optional
import time

class Database:
    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL")
        
    def get_connection(self, retries: int = 3) -> connection:
        """获取数据库连接，支持重试机制"""
        for attempt in range(retries):
            try:
                conn = psycopg2.connect(self.database_url)
                return conn
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                if attempt < retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # 递增延迟
                    continue
                else:
                    raise e
    
    def save_demand_analysis(self, keyword: str, data_source: str, analysis_result: str) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO demand_analysis (keyword, data_source, analysis_result) VALUES (%s, %s, %s) RETURNING id",
                (keyword, data_source, analysis_result)
            )
            result = cur.fetchone()
            analysis_id = result[0] if result else 0
            conn.commit()
            return analysis_id
        finally:
            cur.close()
            conn.close()
    
    def save_user_persona(self, user_text: str, persona_result: str) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO user_persona (user_text, persona_result) VALUES (%s, %s) RETURNING id",
                (user_text, persona_result)
            )
            result = cur.fetchone()
            persona_id = result[0] if result else 0
            conn.commit()
            return persona_id
        finally:
            cur.close()
            conn.close()
    
    def save_mvp_experiment(self, experiment_name: str, experiment_goal: str, 
                           metrics_data: str, compass_result: str) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO mvp_experiment (experiment_name, experiment_goal, metrics_data, compass_result) VALUES (%s, %s, %s, %s) RETURNING id",
                (experiment_name, experiment_goal, metrics_data, compass_result)
            )
            result = cur.fetchone()
            experiment_id = result[0] if result else 0
            conn.commit()
            return experiment_id
        finally:
            cur.close()
            conn.close()
    
    def get_demand_analyses(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, keyword, data_source, analysis_result, created_at FROM demand_analysis ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            results = []
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'keyword': row[1],
                    'data_source': row[2],
                    'analysis_result': row[3],
                    'created_at': row[4]
                })
            return results
        finally:
            cur.close()
            conn.close()
    
    def get_demand_analyses_count(self) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM demand_analysis")
            result = cur.fetchone()
            return result[0] if result else 0
        finally:
            cur.close()
            conn.close()
    
    def get_user_personas(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, user_text, persona_result, created_at FROM user_persona ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            results = []
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'user_text': row[1],
                    'persona_result': row[2],
                    'created_at': row[3]
                })
            return results
        finally:
            cur.close()
            conn.close()
    
    def get_user_personas_count(self) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM user_persona")
            result = cur.fetchone()
            return result[0] if result else 0
        finally:
            cur.close()
            conn.close()
    
    def get_mvp_experiments(self, limit: int = 20, offset: int = 0) -> List[Dict]:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, experiment_name, experiment_goal, metrics_data, compass_result, created_at FROM mvp_experiment ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            results = []
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'experiment_name': row[1],
                    'experiment_goal': row[2],
                    'metrics_data': row[3],
                    'compass_result': row[4],
                    'created_at': row[5]
                })
            return results
        finally:
            cur.close()
            conn.close()
    
    def get_mvp_experiments_count(self) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM mvp_experiment")
            result = cur.fetchone()
            return result[0] if result else 0
        finally:
            cur.close()
            conn.close()
    
    def get_demand_analysis_by_id(self, analysis_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, keyword, data_source, analysis_result, created_at FROM demand_analysis WHERE id = %s",
                (analysis_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'keyword': row[1],
                    'data_source': row[2],
                    'analysis_result': row[3],
                    'created_at': row[4]
                }
            return None
        finally:
            cur.close()
            conn.close()
    
    def get_experiment_by_id(self, experiment_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, experiment_name, experiment_goal, metrics_data, compass_result, created_at FROM mvp_experiment WHERE id = %s",
                (experiment_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'experiment_name': row[1],
                    'experiment_goal': row[2],
                    'metrics_data': row[3],
                    'compass_result': row[4],
                    'created_at': row[5]
                }
            return None
        finally:
            cur.close()
            conn.close()
    
    def get_experiment_stats(self) -> Dict:
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM mvp_experiment")
            result = cur.fetchone()
            total_experiments = result[0] if result else 0
            
            cur.execute("SELECT COUNT(*) FROM demand_analysis")
            result = cur.fetchone()
            total_analyses = result[0] if result else 0
            
            cur.execute("SELECT COUNT(*) FROM user_persona")
            result = cur.fetchone()
            total_personas = result[0] if result else 0
            
            return {
                'total_experiments': total_experiments,
                'total_analyses': total_analyses,
                'total_personas': total_personas
            }
        finally:
            cur.close()
            conn.close()
