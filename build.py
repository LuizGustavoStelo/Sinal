import os
import re
import shutil
import subprocess
import sys
from importlib import import_module, util
from pathlib import Path


DRIVE_FOLDER_ID = "1qUpWNd2fvUAQrq9ZumfvzaxzsuyRK12Y"
VERSION_FILE_NAME = "versao.txt"
EXECUTABLE_NAME = "Sinal.exe"
APP_FILE = "app_ui.py"
DIST_DIR = Path("dist")

_MEDIA_FILE_UPLOAD = None


_MODULE_TO_PACKAGE = {
    "google.oauth2.service_account": "google-auth",
    "googleapiclient.discovery": "google-api-python-client",
    "googleapiclient.http": "google-api-python-client",
}


def _find_missing_modules(modules):
    missing = []
    for name in modules:
        try:
            spec = util.find_spec(name)
        except ModuleNotFoundError:
            spec = None
        if spec is None:
            missing.append(name)
    return missing


def _attempt_install_missing(packages):
    if not packages:
        return False

    print("Dependências do Google Drive ausentes. Tentando instalar automaticamente:")
    for package in sorted(packages):
        print(f" - {package}")

    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *sorted(packages)]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(
            "Não foi possível instalar automaticamente as dependências do Google Drive."
        )
        return False

    print("Dependências do Google Drive instaladas com sucesso.")
    return True


def _load_drive_modules():
    required_modules = {
        "google.oauth2.service_account": None,
        "googleapiclient.discovery": None,
        "googleapiclient.http": None,
    }

    missing = _find_missing_modules(required_modules)
    if missing:
        packages = {
            _MODULE_TO_PACKAGE[name]
            for name in missing
            if name in _MODULE_TO_PACKAGE
        }
        installed = _attempt_install_missing(packages)
        if installed:
            missing = _find_missing_modules(required_modules)

    if missing:
        print("As dependências do Google Drive continuam ausentes:")
        for name in missing:
            print(f" - {name}")
        print("Envio automático para o Google Drive será ignorado.")
        return None

    for name in required_modules:
        required_modules[name] = import_module(name)

    return required_modules


def _prompt_for_credentials():
    print(
        "Arquivo de credenciais do Google Drive não encontrado."\
        "\nCole o caminho completo do JSON da conta de serviço ou pressione Enter para"\
        " continuar sem enviar para o Drive."
    )
    user_input = input("Caminho do arquivo de credenciais: ").strip()
    if not user_input:
        return None

    candidate = Path(user_input.strip('"'))
    candidate = candidate.expanduser().resolve(strict=False)
    if not candidate.exists():
        print(
            "O caminho informado não existe. Envio automático será ignorado nesta compilação."
        )
        return None

    target = Path("service_account.json")
    try:
        shutil.copy2(candidate, target)
        print(f"Credenciais copiadas para {target.resolve()}")
    except OSError as exc:
        print(f"Não foi possível copiar o arquivo de credenciais: {exc}")
        return None

    return str(target.resolve())


def get_credentials_path():
    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and os.path.exists(env_path):
        return env_path

    default_path = Path("service_account.json")
    if default_path.exists():
        return str(default_path.resolve())

    return _prompt_for_credentials()


def create_drive_service():
    modules = _load_drive_modules()
    if not modules:
        return None

    Credentials = modules["google.oauth2.service_account"].Credentials
    build_service = modules["googleapiclient.discovery"].build
    global _MEDIA_FILE_UPLOAD
    _MEDIA_FILE_UPLOAD = modules["googleapiclient.http"].MediaFileUpload

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
    return build_service("drive", "v3", credentials=creds, cache_discovery=False)


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
    if _MEDIA_FILE_UPLOAD is None:
        print("Upload não inicializado por falta do módulo MediaFileUpload.")
        return
    media = _MEDIA_FILE_UPLOAD(file_path, resumable=True)
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
