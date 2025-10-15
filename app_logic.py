import sqlite3

class MusicAppLogic:
    def __init__(self, arquivo_dados):
        self.arquivo_dados = arquivo_dados
        self.criar_tabelas()

    def criar_tabelas(self):
        try:
            conn = sqlite3.connect(self.arquivo_dados)
            cursor = conn.cursor()

            for dia in ["segunda", "terça", "quarta", "quinta", "sexta"]:
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {dia} (hora TEXT, nome TEXT, musica TEXT)")

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao criar tabelas: {str(e)}")

    def executar_query(self, query, params=()):
        try:
            conn = sqlite3.connect(self.arquivo_dados)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao executar query: {str(e)}")

    def selecionar_query(self, query, params=()):
        try:
            conn = sqlite3.connect(self.arquivo_dados)
            cursor = conn.cursor()
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            conn.close()
            return resultados
        except Exception as e:
            print(f"Erro ao executar query de seleção: {str(e)}")
            return []

    def get_musicas_por_dia(self, dia):
        return self.selecionar_query(f"SELECT hora, nome, musica FROM {dia.lower()}")

    def adicionar_musica(self, dia, hora, nome, musica):
        self.executar_query(f"INSERT INTO {dia.lower()} (hora, nome, musica) VALUES (?, ?, ?)", (hora, nome, musica))
        print("Nova música adicionada com sucesso!")

    def deletar_musica(self, dia, hora, nome):
        self.executar_query(f"DELETE FROM {dia.lower()} WHERE hora=? AND nome=?", (hora, nome))
        print("Música deletada com sucesso!")

    def editar_musica(self, dia, hora, nome, campo, nova_informacao=None):
        query = f"UPDATE {dia.lower()} SET {campo}=? WHERE hora=? AND nome=?"
        self.executar_query(query, (nova_informacao, hora, nome) if nova_informacao else (None, hora, nome))
        print(f"Informação editada com sucesso para o campo {campo}!")
