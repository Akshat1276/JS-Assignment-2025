import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import logging
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager with connection pooling"""
    
    def __init__(self):
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            # Get database connection parameters
            db_config = {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': os.getenv('POSTGRES_PORT', '5432'),
                'database': os.getenv('POSTGRES_DB', 'llm_chat_db'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', '')
            }
            
            # Alternative: use full connection URL if provided
            postgres_url = os.getenv('POSTGRES_URL')
            if postgres_url:
                self.pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=20,
                    dsn=postgres_url
                )
            else:
                self.pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=20,
                    **db_config
                )
            
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        connection = None
        try:
            connection = self.pool.getconn()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if connection:
                self.pool.putconn(connection)
    
    @contextmanager
    def get_cursor(self, commit=True):
        """Get a cursor with automatic transaction management"""
        with self.get_connection() as connection:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    connection.commit()
            except Exception as e:
                connection.rollback()
                logger.error(f"Database transaction failed: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a query and optionally fetch results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return cursor.rowcount
    
    def execute_query_one(self, query, params=None):
        """Execute a query and fetch one result"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def close_pool(self):
        """Close the connection pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
def get_db_connection():
    """Get a database connection (use with context manager)"""
    return db_manager.get_connection()

def get_db_cursor(commit=True):
    """Get a database cursor (use with context manager)"""
    return db_manager.get_cursor(commit=commit)

def execute_query(query, params=None, fetch=False):
    """Execute a query"""
    return db_manager.execute_query(query, params, fetch)

def execute_query_one(query, params=None):
    """Execute a query and fetch one result"""
    return db_manager.execute_query_one(query, params)

def test_connection():
    """Test database connection"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            logger.info(f"Database connection test successful: {result}")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def init_database():
    """Initialize database with schema"""
    try:
        # Read and execute schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with get_db_cursor() as cursor:
            cursor.execute(schema_sql)
        
        logger.info("Database schema initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        return False

if __name__ == "__main__":
    # Test the connection when run directly
    print("Testing database connection...")
    if test_connection():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
    
    # Initialize schema
    print("Initializing database schema...")
    if init_database():
        print("✅ Database schema initialized!")
    else:
        print("❌ Database schema initialization failed!")
