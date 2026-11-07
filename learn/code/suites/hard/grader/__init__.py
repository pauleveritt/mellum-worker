"""Install SQLite observation before any application or lifespan imports."""
from grader_tests._database import install_sql_recording

install_sql_recording()
