# Sinal

Aplicativo desktop em PyQt5 para gerenciamento de toques musicais agendados. Ele permite registrar músicas para cada dia útil da semana, tocar manualmente e reproduzir automaticamente conforme os horários programados. O projeto usa SQLite para persistir a programação e PyInstaller para empacotamento.

## Funcionalidades principais

- Interface gráfica com tabelas e botões para segunda a sexta-feira.
- Cadastro de horário, nome e arquivo MP3 associado para cada sinal.
- Reprodução manual e automática utilizando `QMediaPlayer`.
- Edição e exclusão com verificação de conflitos entre dias.
- Janela de informações com dicas de uso e dados de versão.

## Estrutura do projeto

```text
Sinal/
├── app_ui.py          # Interface principal e caixas de diálogo PyQt5
├── app_logic.py       # Camada de acesso a dados SQLite reutilizável
├── assets/
│   ├── icon.ico
│   └── icon.png
├── Musicas/           # Exemplos de arquivos MP3 usados nos testes
├── build.py           # Script que incrementa a versão no app e executa o PyInstaller
├── app_ui.spec        # Arquivo de configuração gerado pelo PyInstaller
├── compilar.bat       # Atalho em Windows para executar o build
├── build/             # Artefatos intermediários do PyInstaller
├── dist/              # Binário gerado (`app_ui.exe`) e banco padrão
├── dados.db           # Banco de dados SQLite utilizado pela aplicação
├── data.db / database.db / musicas.db  # Bancos alternativos ou de testes
└── README.md
```

> Os arquivos `.db` armazenam as tabelas `segunda` a `sexta` com as colunas `hora`, `nome` e `musica`. A aplicação cria automaticamente as tabelas quando o arquivo ainda não existe.

## Executando a aplicação

1. Instale as dependências (Python 3.12+ recomendado):
   ```bash
   pip install PyQt5
   ```
2. Inicie a interface:
   ```bash
   python app_ui.py
   ```
   O aplicativo abrirá com o banco `dados.db` na raiz do projeto.

### Empacotando

O script `build.py` atualiza o número da versão exibido na janela de informações e chama o PyInstaller. Para gerar um executável:

```bash
python build.py
```

O resultado ficará em `dist/app_ui.exe`. Durante o build, garanta que as dependências do PyInstaller (incluindo `PyQt5` e `pyinstaller`) estejam instaladas no ambiente ativo.

## Observações

- Mantenha a pasta `Musicas/` ou o caminho para os MP3 acessível ao aplicativo para evitar erros de reprodução.
- O app bloqueia a maximização para preservar o layout pensado para telas pequenas.
- A verificação automática de músicas considera apenas dias úteis, disparando reproduções pontuais no horário exato (HH:mm).
- Para que a publicação automática das novas versões funcione, use um token de acesso pessoal do GitHub com permissão de escrita
  em releases. Tokens _clássicos_ precisam do escopo `repo`; tokens granulares devem liberar pelo menos "Contents: Read and write"
  (além de "Metadata: Read-only") para o repositório `LuizGustavoStelo/Sinal-releases`. Armazene o token na variável de ambiente
  `SINAL_GITHUB_TOKEN` (ou `GITHUB_TOKEN`) e mantenha o arquivo `.github_release_config.json` apontando para o repositório de
  releases. Ao executar `compilar.bat`, o build enviará `Sinal.exe` e `versao.txt` como assets da release mais recente.
- Inicialize o repositório de releases com pelo menos um commit (por exemplo, adicionando um `README.md`) antes de rodar o primeiro
  build automatizado. O GitHub exige uma branch padrão ativa para aceitar a criação das releases via API.
