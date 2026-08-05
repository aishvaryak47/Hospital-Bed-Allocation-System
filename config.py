import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hospital-discrete-math-secret-key-2026'
    
    # DB URI support: SQLite by default for zero-config run, or MySQL if specified
    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite') # 'sqlite' or 'mysql'
    
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'hospital_bed_db')

    if DB_TYPE == 'mysql':
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    else:
        # SQLite absolute/relative path in workspace
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'hospital.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
