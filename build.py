import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


APP_FILE = "app_ui.py"
DIST_DIR = Path("dist")
EXECUTABLE_NAME = "Sinal.exe"
SOURCE_EXECUTABLE_NAME = "app_ui.exe"
VERSION_FILE_NAME = "versao.txt"
RELEASE_CONFIG_PATH = Path(".github_release_config.json")
UPDATE_CONFIG_NAME = "update_config.json"
USER_AGENT = "Sinal-Build-Script"


def _normalize_version(version: Optional[str]) -> str:
    if not version:
        return ""
    cleaned = version.strip()
    if cleaned.lower().startswith("v"):
        cleaned = cleaned[1:]
    return cleaned


def _parse_version_tuple(version: str) -> Tuple[int, ...]:
    normalized = _normalize_version(version)
    parts = [part for part in normalized.split(".") if part]
    if not parts:
        raise ValueError("Versão vazia")
    try:
        return tuple(int(part) for part in parts)
    except ValueError as exc:
        raise ValueError(f"Versão inválida: {version}") from exc


def increment_version(version_str: str) -> str:
    try:
        parts = list(_parse_version_tuple(version_str))
    except ValueError:
        return version_str
    parts[-1] += 1
    return ".".join(str(part) for part in parts)


def _format_version_tuple(parts: Sequence[int]) -> str:
    return ".".join(str(part) for part in parts)


def update_version_in_file(
    file_path: str, baseline_version: Optional[str] = None
) -> Optional[str]:
    with open(file_path, "r", encoding="utf-8") as file_handle:
        content = file_handle.read()

    pattern = r'APP_VERSION\s*=\s*"(\d+\.\d+\.\d+)"'
    match = re.search(pattern, content)
    if not match:
        print("Versão não encontrada no arquivo de aplicação.")
        return None

    old_version = match.group(1)

    comparison_base = old_version
    if baseline_version:
        try:
            remote_tuple = _parse_version_tuple(baseline_version)
            local_tuple = _parse_version_tuple(old_version)
        except ValueError:
            remote_tuple = None
            local_tuple = None
        if remote_tuple and local_tuple and remote_tuple >= local_tuple:
            comparison_base = _format_version_tuple(remote_tuple)

    new_version = increment_version(comparison_base)
    new_content = content.replace(
        f'APP_VERSION = "{old_version}"', f'APP_VERSION = "{new_version}"'
    )

    with open(file_path, "w", encoding="utf-8") as file_handle:
        file_handle.write(new_content)

    if comparison_base != old_version:
        print(
            "Versão local ajustada para acompanhar a release mais recente disponível "
            f"({baseline_version})."
        )
    print(f"Versão atualizada de {old_version} para {new_version}")
    return new_version


def _parse_repo_slug(slug: str) -> Tuple[str, str]:
    parts = [part.strip() for part in slug.split("/") if part.strip()]
    if len(parts) != 2:
        raise ValueError("Informe o repositório no formato dono/repositorio.")
    return parts[0], parts[1]


def _load_config_from_env() -> Optional[dict]:
    token = (
        os.environ.get("SINAL_GITHUB_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
    )
    repository = (
        os.environ.get("SINAL_GITHUB_REPOSITORY")
        or os.environ.get("GITHUB_REPOSITORY")
    )
    owner = (
        os.environ.get("SINAL_GITHUB_OWNER")
        or os.environ.get("GITHUB_OWNER")
    )
    repo_name = (
        os.environ.get("SINAL_GITHUB_REPO")
        or os.environ.get("GITHUB_REPO")
    )

    try:
        if repository:
            owner, repo_name = _parse_repo_slug(repository)
        elif owner and repo_name:
            owner, repo_name = owner, repo_name
        else:
            return None
    except ValueError:
        return None

    if not token:
        return {"owner": owner, "repo": repo_name}

    return {"owner": owner, "repo": repo_name, "token": token}


def _load_config_from_file() -> Optional[dict]:
    if not RELEASE_CONFIG_PATH.exists():
        return None

    try:
        with open(RELEASE_CONFIG_PATH, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Não foi possível ler {RELEASE_CONFIG_PATH}: {exc}")
        return None

    owner = data.get("owner")
    repo = data.get("repo")
    token = data.get("token")
    if not owner or not repo:
        print("Configuração do GitHub Releases incompleta no arquivo salvo.")
        return None

    config = {"owner": owner, "repo": repo}
    if token:
        config["token"] = token
    return config


def load_release_config() -> Optional[dict]:
    env_config = _load_config_from_env()
    file_config = _load_config_from_file()
    prioritized = [
        config
        for config in (env_config, file_config)
        if config and config.get("token")
    ]
    if prioritized:
        return prioritized[0]

    fallback = env_config or file_config
    if fallback:
        return fallback

    print(
        "Configuração do GitHub Releases não encontrada. Configure variáveis de ambiente ou o arquivo .github_release_config.json para habilitar o upload automático."
    )
    return None


def resolve_repository_coordinates(config: Optional[dict]) -> Tuple[Optional[str], Optional[str]]:
    if config and config.get("owner") and config.get("repo"):
        return config["owner"], config["repo"]

    fallback = _load_config_from_env() or _load_config_from_file()
    if fallback and fallback.get("owner") and fallback.get("repo"):
        return fallback["owner"], fallback["repo"]

    return None, None


def fetch_remote_latest_version(
    owner: Optional[str], repo: Optional[str], token: Optional[str]
) -> Optional[str]:
    if not owner or not repo:
        return None

    url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=20"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(request) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        print(
            "Não foi possível consultar as releases existentes no GitHub "
            f"({exc.code} {exc.reason}). Continuando com a versão local."
        )
        return None
    except urllib.error.URLError as exc:
        print(
            "Não foi possível conectar ao GitHub para verificar a versão atual: "
            f"{exc}"
        )
        return None

    if not isinstance(payload, list):
        return None

    latest: Optional[Tuple[Tuple[int, ...], str]] = None
    for release in payload:
        if not isinstance(release, dict):
            continue
        if release.get("draft") or release.get("prerelease"):
            continue
        tag = release.get("tag_name") or ""
        normalized = _normalize_version(str(tag))
        try:
            version_tuple = _parse_version_tuple(normalized)
        except ValueError:
            continue
        if latest is None or version_tuple > latest[0]:
            latest = (version_tuple, _format_version_tuple(version_tuple))

    if latest:
        return latest[1]
    return None


def _format_github_error(payload: object) -> str:
    if isinstance(payload, dict):
        message = payload.get("message")
        details: List[str] = []
        errors = payload.get("errors")
        if isinstance(errors, list):
            for error in errors:
                if isinstance(error, dict):
                    parts: List[str] = []
                    resource = error.get("resource")
                    field = error.get("field")
                    code = error.get("code")
                    err_message = error.get("message")
                    if resource:
                        parts.append(str(resource))
                    if field:
                        parts.append(str(field))
                    if code:
                        parts.append(str(code))
                    if err_message and err_message not in parts:
                        parts.append(str(err_message))
                    if parts:
                        details.append("/".join(parts))
                elif error:
                    details.append(str(error))
        detail_text = "; ".join(details)
        if message and detail_text:
            return f"{message} ({detail_text})"
        if message:
            return str(message)
        if detail_text:
            return detail_text
        return json.dumps(payload, ensure_ascii=False)
    return str(payload)


class GithubReleasePublisher:
    def __init__(self, owner: str, repo: str, token: str):
        self.owner = owner
        self.repo = repo
        self.token = token

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[bytes] = None,
        base: str = "https://api.github.com",
        content_type: Optional[str] = "application/json",
    ) -> Tuple[int, object]:
        url = f"{base}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "Authorization": f"Bearer {self.token}",
        }

        payload = data
        if data is not None and content_type == "application/json":
            payload = json.dumps(data).encode("utf-8")
        if payload is not None and content_type:
            headers["Content-Type"] = content_type

        request = urllib.request.Request(url, data=payload, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request) as response:
                raw_body = response.read()
                content = response.headers.get("Content-Type", "")
                if "application/json" in content:
                    if raw_body:
                        return response.status, json.loads(raw_body.decode("utf-8"))
                    return response.status, {}
                return response.status, raw_body
        except urllib.error.HTTPError as exc:
            body = exc.read()
            try:
                payload = json.loads(body.decode("utf-8")) if body else {"message": exc.reason}
            except json.JSONDecodeError:
                payload = {"message": body.decode("utf-8", errors="ignore")}
            return exc.code, payload

    def _get_repository_details(self) -> dict:
        status, data = self._request(
            "GET",
            f"/repos/{self.owner}/{self.repo}",
        )
        if status == 200 and isinstance(data, dict):
            return data
        message = _format_github_error(data)
        raise RuntimeError(
            "Não foi possível carregar metadados do repositório para publicar a release: "
            f"{message}"
        )

    def ensure_release(self, version: str) -> dict:
        tag_name = f"v{version}"
        status, data = self._request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/releases/tags/{tag_name}",
        )

        if status == 200:
            return data
        if status != 404:
            message = _format_github_error(data)
            raise RuntimeError(f"Falha ao localizar release existente: {message}")

        target_commitish: Optional[str] = None
        try:
            repo_details = self._get_repository_details()
            target_commitish = repo_details.get("default_branch")
            if not target_commitish:
                print(
                    "Repositório sem branch padrão detectado. Certifique-se de que o repositório de releases possui pelo menos um commit."
                )
        except RuntimeError as exc:
            print(exc)

        release_payload = {
            "tag_name": tag_name,
            "name": f"Versão {version}",
            "body": f"Build gerada automaticamente em {datetime.now():%Y-%m-%d %H:%M}",
            "draft": False,
            "prerelease": False,
        }
        if target_commitish:
            release_payload["target_commitish"] = target_commitish
        status, data = self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/releases",
            data=release_payload,
        )
        if status not in (200, 201):
            message = _format_github_error(data)
            raise RuntimeError(f"Não foi possível criar a release: {message}")
        return data

    def _delete_asset(self, asset_id: int) -> None:
        status, data = self._request(
            "DELETE",
            f"/repos/{self.owner}/{self.repo}/releases/assets/{asset_id}",
            content_type=None,
        )
        if status not in (200, 204, 404):
            message = _format_github_error(data)
            raise RuntimeError(f"Não foi possível remover o asset antigo: {message}")

    def upload_asset(self, release: dict, file_path: Path) -> None:
        asset_name = file_path.name
        existing_assets = {asset.get("name"): asset for asset in release.get("assets", [])}
        if asset_name in existing_assets:
            asset_id = existing_assets[asset_name].get("id")
            if asset_id is not None:
                self._delete_asset(asset_id)

        upload_path = f"/repos/{self.owner}/{self.repo}/releases/{release['id']}/assets?{urllib.parse.urlencode({'name': asset_name})}"
        with open(file_path, "rb") as file_handle:
            binary = file_handle.read()

        status, data = self._request(
            "POST",
            upload_path,
            data=binary,
            base="https://uploads.github.com",
            content_type="application/octet-stream",
        )
        if status not in (200, 201):
            message = _format_github_error(data)
            raise RuntimeError(f"Falha ao enviar '{asset_name}' para a release: {message}")

        print(f"Asset '{asset_name}' enviado com sucesso para a release.")


def write_update_config(
    owner: Optional[str], repo: Optional[str], token: Optional[str] = None
) -> None:
    if not owner or not repo:
        return

    config_path = DIST_DIR / UPDATE_CONFIG_NAME
    payload = {
        "owner": owner,
        "repo": repo,
        "executable": EXECUTABLE_NAME,
        "version_file": VERSION_FILE_NAME,
    }
    if token:
        payload["token"] = token
    try:
        with open(config_path, "w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, indent=2)
        print(f"Arquivo de configuração de atualização gerado em {config_path}.")
    except OSError as exc:
        print(f"Não foi possível escrever o arquivo de configuração de atualização: {exc}")


def update_repo_constants(app_file: str, owner: Optional[str], repo: Optional[str]) -> None:
    if not owner or not repo:
        return

    try:
        with open(app_file, "r", encoding="utf-8") as file_handle:
            content = file_handle.read()
    except OSError as exc:
        print(f"Não foi possível ler {app_file} para atualizar constantes do GitHub: {exc}")
        return

    new_content = re.sub(
        r'DEFAULT_GITHUB_OWNER\s*=\s*"[^"]*"',
        f'DEFAULT_GITHUB_OWNER = "{owner}"',
        content,
        count=1,
    )
    new_content = re.sub(
        r'DEFAULT_GITHUB_REPO\s*=\s*"[^"]*"',
        f'DEFAULT_GITHUB_REPO = "{repo}"',
        new_content,
        count=1,
    )

    try:
        with open(app_file, "w", encoding="utf-8") as file_handle:
            file_handle.write(new_content)
        print("Constantes de repositório padrão atualizadas no aplicativo.")
    except OSError as exc:
        print(f"Não foi possível atualizar {app_file} com os dados do repositório: {exc}")


def publish_to_github(version: str, assets: List[Path], config: dict) -> None:
    token = config.get("token")
    owner = config.get("owner")
    repo = config.get("repo")

    if not token:
        print("Token do GitHub não disponível. Upload da release ignorado.")
        return
    if not owner or not repo:
        print("Informações do repositório ausentes. Upload da release ignorado.")
        return

    publisher = GithubReleasePublisher(owner, repo, token)
    try:
        release = publisher.ensure_release(version)
        for asset in assets:
            publisher.upload_asset(release, asset)
        release_url = release.get("html_url")
        if release_url:
            print(f"Arquivos publicados em {release_url}")
        else:
            print("Upload para o GitHub concluído com sucesso.")
    except Exception as exc:
        message = str(exc)
        print(f"Falha ao publicar no GitHub Releases: {message}")
        if "personal access token" in message.lower():
            print(
                "Verifique se o token do GitHub tem permissão de escrita em releases. "
                "Para tokens clássicos, habilite o escopo 'repo'. Para tokens granulares, "
                "marque 'Contents: Read and write' e 'Metadata: Read-only' para o repositório "
                "de releases."
            )
        if "target_commitish" in message or "branch" in message.lower():
            print(
                "Confirme se o repositório de releases possui ao menos um commit e uma branch padrão ativa. "
                "Crie um commit inicial (por exemplo, adicionando um README) antes de tentar publicar a primeira release."
            )


def main() -> None:
    release_config = load_release_config()
    owner, repo = resolve_repository_coordinates(release_config)
    token = release_config.get("token") if release_config else None

    baseline_version = fetch_remote_latest_version(owner, repo, token)
    if baseline_version:
        print(f"Versão mais recente publicada no GitHub: {baseline_version}")

    new_version = update_version_in_file(APP_FILE, baseline_version)

    subprocess.run(
        [
            "pyinstaller",
            "--onefile",
            "--noconsole",
            "--icon=assets/icon.ico",
            APP_FILE,
        ],
        check=True,
    )

    source_executable = DIST_DIR / SOURCE_EXECUTABLE_NAME
    if not source_executable.exists():
        print(
            "Executável gerado não encontrado. Certifique-se de que o PyInstaller concluiu a compilação com sucesso."
        )
        sys.exit(1)

    target_executable = DIST_DIR / EXECUTABLE_NAME
    shutil.copy2(source_executable, target_executable)
    print(f"Executável copiado para {target_executable}")

    if new_version:
        version_file = DIST_DIR / VERSION_FILE_NAME
        version_file.write_text(new_version, encoding="utf-8")
        print(f"Arquivo de versão atualizado em {version_file}")
    else:
        version_file = None

    update_repo_constants(APP_FILE, owner, repo)

    write_update_config(owner, repo, token)

    assets = [target_executable]
    if version_file:
        assets.append(version_file)

    if release_config and new_version:
        publish_to_github(new_version, assets, release_config)
    elif release_config and not new_version:
        print("Não foi possível determinar a versão. Upload da release não será realizado.")
    else:
        print("Configuração do GitHub ausente. Upload da release não será realizado.")


if __name__ == "__main__":
    main()
