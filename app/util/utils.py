from pathlib import Path

import jsonlines
import yaml
from config.settings import BASE_APP_DIR, BASE_DIR, Config
from langchain.schema import Document


class DocsJSONLLoader:
    """
    Cargador de documentos de documentaciones en formato JSONL.

    Args:
        file_path (Path): Ruta al archivo JSONL a cargar.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load(self):
        """
        Carga los documentos de la ruta del archivo especificada durante la inicialización.

        Returns:
            Una lista de objetos Document.
        """
        with jsonlines.open(self.file_path) as reader:
            documents = []
            for obj in reader:
                page_content = obj.get("text", "")
                metadata = {
                    "title": obj.get("title", ""),
                    "repo_owner": obj.get("repo_owner", ""),
                    "repo_name": obj.get("repo_name", ""),
                    "module": obj.get("module", ""),
                }
                documents.append(Document(page_content=page_content, metadata=metadata))
        return documents


def load_config():
    """
    Carga la configuración de la aplicación desde el archivo 'config.yaml'.

    Returns:
        Un diccionario con la configuración de la aplicación.
    """
    with open(BASE_APP_DIR / "config" / "config.yaml") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ValueError(exc)


def get_openai_api_key() -> str:
    """
    Obtiene la clave API de OpenAI del entorno. Si no está disponible, detiene la ejecución del programa.

    Returns:
        La clave API de OpenAI.
    """
    openai_api_key = Config.OPENAI_API_KEY
    if not openai_api_key:
        raise ValueError("Por favor crea una variable de ambiente OPENAI_API_KEY.")
    return openai_api_key


def get_cohere_api_key() -> str:
    """
    Obtiene la clave API de Cohere del entorno. Si no está disponible, solicita al usuario que la ingrese.

    Returns:
        La clave API de Cohere.
    """
    cohere_api_key = Config.COHERE_API_KEY
    if not cohere_api_key:
        raise ValueError("Por favor ingresa tu COHERE_API_KEY: ")
    return cohere_api_key


def get_file_path() -> Path:
    """
    Obtiene la ruta al archivo de base de datos JSONL especificado en la configuración de la aplicación.

    Returns:
        La ruta al archivo de base de datos JSONL.
    """
    config = load_config()
    # return BASE_DIR / config["jsonl_database_path"]
    return Path(Config.MICROSERVICES_PATH)


def get_query_from_user() -> str:
    """
    Solicita una consulta al usuario.

    Returns:
        La consulta ingresada por el usuario.
    """
    try:
        query = input()
        return query
    except EOFError:
        print("Error: Input no esperado. Por favor intenta de nuevo.")
        return get_query_from_user()


def create_dir(path: Path) -> None:
    """
    Crea un directorio si no existe.

    Args:
        path (str): Ruta del directorio a crear.
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def remove_existing_file(file_path: Path) -> None:
    """
    Elimina un archivo si existe.

    Args:
        file_path (str): Ruta del archivo a eliminar.
    """
    if file_path.exists():
        file_path.unlink()
