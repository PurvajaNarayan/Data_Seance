from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_DIR / 'data'

def load_env_vars():
    from dotenv import load_dotenv
    dotenv_path = str(Path(__file__).parent.parent.parent.resolve() / '.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    
