from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_DIR / 'data'

def load_env_vars(dotenv_path: str=str(PROJECT_DIR / 'assets' / 'env' / '.env')):
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=dotenv_path)
    
    
