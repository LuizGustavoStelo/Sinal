import os
import re
import shutil
import subprocess
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


DRIVE_FOLDER_ID = "1qUpWNd2fvUAQrq9ZumfvzaxzsuyRK12Y"
VERSION_FILE_NAME = "versao.txt"
EXECUTABLE_NAME = "Sinal.exe"
APP_FILE = "app_ui.py"
DIST_DIR = Path("dist")


def get_credentials_path():
    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and os.path.exists(env_path):
        return env_path

    default_path = Path("service_account.json")
    if default_path.exists():
        return str(default_path)

    return None


def create_drive_service():
    credentials_path = get_credentials_path()
    if not credentials_path:
        print(
            "Credenciais do Google Drive não encontradas. Pule o envio automático."
        )
        return None

    creds = Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_file(service, file_path, file_name):
    if not service:
        return

    query = (
        f"'{DRIVE_FOLDER_ID}' in parents and name='{file_name}' and trashed=false"
    )
    existing_files = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id)", pageSize=10)
        .execute()
        .get("files", [])
    )

    for file_data in existing_files:
        service.files().delete(fileId=file_data["id"]).execute()

    metadata = {"name": file_name, "parents": [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, resumable=True)
    service.files().create(body=metadata, media_body=media, fields="id").execute()


def increment_version(version_str):
    # Assume formato x.y.z
    parts = version_str.split('.')
    if len(parts) == 3:
        parts[2] = str(int(parts[2]) + 1)
        return '.'.join(parts)
    return version_str


def update_version_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Encontra a constante APP_VERSION = "x.y.z"
    pattern = r'APP_VERSION\s*=\s*"(\d+\.\d+\.\d+)"'
    match = re.search(pattern, content)
    if match:
        old_version = match.group(1)
        new_version = increment_version(old_version)
        new_content = content.replace(
            f'APP_VERSION = "{old_version}"', f'APP_VERSION = "{new_version}"'
        )
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Versão atualizada de {old_version} para {new_version}')
        return new_version
    else:
        print('Versão não encontrada no arquivo.')
        return None


if __name__ == '__main__':
    new_version = update_version_in_file(APP_FILE)
    # Agora compila
    subprocess.run(
        ['pyinstaller', '--onefile', '--noconsole', '--icon=assets/icon.ico', APP_FILE],
        check=True,
    )

    source_executable = DIST_DIR / 'app_ui.exe'
    if source_executable.exists():
        target_executable = DIST_DIR / EXECUTABLE_NAME
        shutil.copy2(source_executable, target_executable)
        print(f'Executável copiado para {target_executable}')

        if new_version:
            version_file = DIST_DIR / VERSION_FILE_NAME
            version_file.write_text(new_version, encoding='utf-8')
            print(f'Arquivo de versão atualizado em {version_file}')

        drive_service = create_drive_service()
        upload_file(drive_service, str(target_executable), EXECUTABLE_NAME)
        if new_version:
            upload_file(drive_service, str(version_file), VERSION_FILE_NAME)
    else:
        print('Executável gerado não encontrado. Certifique-se de que o PyInstaller concluiu a compilação com sucesso.')
