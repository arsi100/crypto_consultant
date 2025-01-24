import logging
from models import init_db
from database import db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_db_connection():
    """Test the database connection by executing a simple query"""
    try:
        with db.get_session() as session:
            # Use SQLAlchemy's text() for raw SQL
            session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False

def main():
    try:
        logger.info("Initializing database...")

        # Initialize database and create tables
        engine = init_db()
        logger.info("Database tables created successfully!")

        # Test connection
        if test_db_connection():
            logger.info("Database connection test successful!")
        else:
            logger.error("Database connection test failed!")

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    main()