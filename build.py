import re
import subprocess

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

    # Encontra a linha com "Versão x.y.z"
    pattern = r'Versão (\d+\.\d+\.\d+)'
    match = re.search(pattern, content)
    if match:
        old_version = match.group(1)
        new_version = increment_version(old_version)
        new_content = content.replace(f'Versão {old_version}', f'Versão {new_version}')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Versão atualizada de {old_version} para {new_version}')
    else:
        print('Versão não encontrada no arquivo.')

if __name__ == '__main__':
    update_version_in_file('app_ui.py')
    # Agora compila
    subprocess.run(['pyinstaller', '--onefile', '--noconsole', '--icon=assets/icon.ico', 'app_ui.py'])