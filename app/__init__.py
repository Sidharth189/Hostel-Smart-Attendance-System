from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=None):
    app = Flask(__name__,
                static_folder='../static',
                template_folder='templates')

    if config_class is None:
        from config import Config
        app.config.from_object(Config)
    else:
        app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ENCODINGS_FOLDER'], exist_ok=True)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.students import students_bp
    from app.routes.attendance import attendance_bp
    from app.routes.camera import camera_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(camera_bp, url_prefix='/camera')
    app.register_blueprint(reports_bp, url_prefix='/reports')

    with app.app_context():
        db.create_all()
        _run_migrations(db)

    return app


def _run_migrations(db):
    """Apply any pending schema migrations safely."""
    import sqlalchemy as sa
    try:
        with db.engine.connect() as conn:
            inspector = sa.inspect(db.engine)

            # Ensure departments table exists
            existing_tables = inspector.get_table_names()
            if 'departments' not in existing_tables:
                conn.execute(sa.text(
                    'CREATE TABLE IF NOT EXISTS departments '
                    '(id INTEGER PRIMARY KEY AUTOINCREMENT, '
                    'code VARCHAR(20) UNIQUE NOT NULL, '
                    'name VARCHAR(100) NOT NULL, '
                    'block VARCHAR(100), '
                    'warden VARCHAR(100), '
                    'created_at DATETIME DEFAULT CURRENT_TIMESTAMP)'
                ))
                conn.commit()
                print('[Migration] departments table created.')

            # Ensure department_id column exists in attendance
            cols = [c['name'] for c in inspector.get_columns('attendance')]
            if 'department_id' not in cols:
                conn.execute(sa.text(
                    'ALTER TABLE attendance ADD COLUMN department_id INTEGER REFERENCES departments(id)'
                ))
                conn.commit()
                print('[Migration] department_id column added to attendance.')
    except Exception as e:
        print(f'[Migration] Warning: {e}')
