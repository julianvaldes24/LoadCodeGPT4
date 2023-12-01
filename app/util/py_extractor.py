import datetime
import json
import re
from http import HTTPStatus
from pathlib import Path
from typing import Dict

import emoji
import requests
from config.settings import BASE_DIR, Config
from termcolor import colored
from util.utils import create_dir, load_config, remove_existing_file


def preprocess_text(text: str) -> str:
    """
    Preprocesa el texto eliminando ciertos patrones y caracteres.

    Args:
        text (str): Texto a preprocesar.

    Returns:
        El texto preprocesado.
    """
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"http\S+|www.\S+", "", text)
    text = re.sub(r"Copyright.*", "", text)
    text = text.replace("\n", " ")
    text = emoji.demojize(text)
    text = re.sub(r":[a-z_&+-]+:", "", text)
    return text


def download_file_to_jsonl(url: str, repo_info: dict, jsonl_file_name: str) -> None:
    """
    Descarga un archivo desde una URL y lo guarda en un archivo JSONL.

    Args:
        url (str): URL desde donde se descarga el archivo.
        repo_info (dict): Información sobre el repositorio desde donde se descarga el archivo.
        jsonl_file_name (str): Nombre del archivo JSONL donde se guarda el archivo descargado.
    """
    response = requests.get(url)
    filename = url.split("/")[-1]
    text = response.text

    if text is not None and isinstance(text, str):
        text = preprocess_text(text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        file_dict = {
            "title": filename,
            "repo_owner": repo_info["owner"],
            "repo_name": repo_info["repo"],
            "module": str(repo_info["module"]).replace("/", "."),
            "text": text,
        }

        with open(jsonl_file_name, "a") as jsonl_file:
            jsonl_file.write(json.dumps(file_dict) + "\n")
    else:
        print(f"Texto no esperado: {text}")


def file_to_jsonl(path: Path, jsonl_file_name: str) -> None:
    """
    Convierte un archivo a un archivo JSONL.

    Args:
        path (Path): Ruta del archivo a convertir.
        jsonl_file_name (str): Nombre del archivo JSONL donde se guarda el archivo descargado.
    """
    with open(path, "r") as file:
        text = file.read()
        text = preprocess_text(text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        file_dict = {
            "title": path.name,
            "text": text,
        }

        with open(jsonl_file_name, "a") as jsonl_file:
            jsonl_file.write(json.dumps(file_dict) + "\n")


def download_file_to_py(url: str, repo_info: dict, jsonl_file_name: str) -> None:
    """
    Descarga un archivo desde una URL y lo guarda en un archivo JSONL.

    Args:
        url (str): URL desde donde se descarga el archivo.
        repo_info (dict): Información sobre el repositorio desde donde se descarga el archivo.
        jsonl_file_name (str): Nombre del archivo JSONL donde se guarda el archivo descargado.
    """
    response = requests.get(url)
    filename = url.split("/")[-1]
    text = response.text
    module: Path = repo_info["module"]
    if not (folder := (BASE_DIR / "dbdata" / module)).exists():
        folder.mkdir(parents=True, exist_ok=True)

    if text is not None and isinstance(text, str):
        with open(folder / filename, "w") as file:
            file.write(text)
    else:
        print(f"Texto no esperado: {text}")


def process_directory(path: Path, repo_info: Dict, headers: Dict, jsonl_file_name: str, file_types: list) -> None:
    """
    Procesa un directorio de un repositorio de GitHub y descarga los archivos en él.

    Args:
        path (Path): Ruta del directorio a procesar.
        repo_info (Dict): Información sobre el repositorio que contiene el directorio.
        headers (Dict): Headers para la petición a la API de GitHub.
        jsonl_file_name (str): Nombre del archivo JSONL donde se guardarán los archivos descargados.
    """

    base_url = f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/contents/"
    print(colored(f"Procesando directorio: {path} del repo: {repo_info['repo']}", "blue"))
    response = requests.get(base_url + path, headers=headers)

    if response.status_code == HTTPStatus.OK:
        files = response.json()
        for file in files:
            if file["type"] == "file" and Path(file["name"]).suffix in file_types:
                print(colored(f"Descargando documento: {file['name']}", "green"))
                print(colored(f"Descarga URL: {file['download_url']}", "cyan"))
                repo_info["module"] = Path(file["path"]).parent
                download_file_to_py(
                    file["download_url"],
                    repo_info,
                    jsonl_file_name,
                )
            elif file["type"] == "dir":
                process_directory(
                    file["path"],
                    repo_info,
                    headers,
                    jsonl_file_name,
                    file_types,
                )
        print(colored("Exito en extracción de documentos del directorio.", "green"))
    else:
        print(
            colored(
                "No se pudieron recuperar los archivos. Verifique su token de GitHub y los detalles del repositorio.",
                "red",
            )
        )


def process_local_directory(path: Path, jsonl_file_name: str, file_types: list) -> None:
    """
    Procesa un directorio de un repositorio de GitHub y descarga los archivos en él.

    Args:
        path (Path): Ruta del directorio a procesar.
        jsonl_file_name (str): Nombre del archivo JSONL donde se guardarán los archivos descargados.
        file_types (list): Lista de tipos de archivo a procesar.
    """

    print(colored(f"Procesando directorio: {path}", "blue"))
    files = path.glob("**/*.md")
    for file in files:
        if file.is_file() and file.suffix in file_types:
            print(colored(f"Procesando documento: {file.name}", "green"))
            file_to_jsonl(
                file,
                jsonl_file_name,
            )
    print(colored("Exito en extracción de documentos del directorio.", "green"))


def main():
    """
    Función principal que se ejecuta cuando se inicia el script.
    """
    config = load_config()
    github_token = Config.GITHUB_TOKEN

    if github_token is None:
        raise ValueError("GITHUB_TOKEN no está configurado en las variables de entorno.")

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3.raw",
    }

    current_date = datetime.date.today().strftime("%Y_%m_%d")
    jsonl_file_name = BASE_DIR / "dbdata" / f"omni_library_{current_date}.jsonl"

    create_dir(BASE_DIR / "dbdata")
    remove_existing_file(jsonl_file_name)

    # for repo_info in config["github"]["repos"]:
    #     process_directory(
    #         repo_info["path"],
    #         repo_info,
    #         headers,
    #         jsonl_file_name,
    #         file_types=repo_info["file_types"],
    #     )

    process_local_directory(
        Path(Config.MICROSERVICES_PATH),
        jsonl_file_name,
        file_types=[".md"],
    )
