from pathlib import Path

from environs import Env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_APP_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BASE_APP_DIR.parent

env = Env()
env.read_env()  # read .env file, if it exists


# Get the API key from the .env file
class Config:
    OPENAI_API_KEY: str = env("OPENAI_API_KEY")
    GITHUB_TOKEN: str = env("GITHUB_TOKEN")
    RECREATE_CHROMA_DB: bool = env.bool("RECREATE_CHROMA_DB", default=False)
    # values possible: qa, memory_chat
    CHAT_TYPE: str = env("CHAT_TYPE", default="qa")
    COHERE_API_KEY: str = env("COHERE_API_KEY", default=None)
    MICROSERVICES_PATH: str = env("MICROSERVICES_PATH", default=None)
