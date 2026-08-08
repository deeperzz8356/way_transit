import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

root = Path(__file__).resolve().parent.parent
env_path = root / '.env'
print('env exists=', env_path.exists())
load_dotenv(env_path)
url = os.getenv('DATABASE_URL')
print('DATABASE_URL=', url)
if not url:
    raise SystemExit('DATABASE_URL not found')
engine = create_engine(url, connect_args={'check_same_thread': False} if 'sqlite' in url else {})
try:
    with engine.connect() as conn:
        print('SELECT 1 =>', conn.execute(text('SELECT 1')).scalar())
except Exception as e:
    print('CONNECT ERROR:', repr(e))
    raise
