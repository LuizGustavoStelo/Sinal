import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QStyledItemDelegate, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QFileDialog, QInputDialog, QDialog, QDialogButtonBox, QCheckBox, QDesktopWidget, QTimeEdit, QLineEdit, QGraphicsDropShadowEffect, QFrame
from PyQt5.QtCore import Qt, QTimer, QTime, QUrl, QDate, QDateTime
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import sqlite3

def add_drop_shadow(widget, blur_radius=16, x_offset=0, y_offset=3, opacity=110):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur_radius)
    shadow.setOffset(x_offset, y_offset)
    shadow.setColor(QColor(0, 0, 0, opacity))
    widget.setGraphicsEffect(shadow)


class EditDialog(QDialog):
    def __init__(self, input_type="text", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Informação")
        self.setStyleSheet("background-color: white;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 20, 24, 20)
        self.layout.setSpacing(16)

        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)

        input_font = QFont()
        input_font.setPointSize(12)

        self.label = QLabel("Nova Informação:", self)
        self.label.setFont(label_font)
        self.layout.addWidget(self.label)

        if input_type == "time":
            self.input_widget = QTimeEdit(self)
            self.input_widget.setDisplayFormat("HH:mm")
            self.input_widget.setTime(QTime.currentTime())  # Define o tempo atual como padrão
        else:
            self.input_widget = QLineEdit(self)

        self.input_widget.setFont(input_font)
        self.layout.addWidget(self.input_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        for button in self.button_box.buttons():
            button.setFixedSize(90, 40)
            button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
            add_drop_shadow(button)

    def get_input(self):
        if isinstance(self.input_widget, QTimeEdit):
            return self.input_widget.time().toString("HH:mm")
        else:
            return self.input_widget.text()
        
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

class HoraInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecione a Hora")
        self.setModal(True)
        self.setStyleSheet("background-color: white;")

        self.layout = QVBoxLayout(self)

        self.time_edit = QTimeEdit(self)
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())  # Define o tempo atual como padrão
        self.layout.addWidget(self.time_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        # Padronizar botões
        for button in self.button_box.buttons():
            button.setFixedSize(90, 40)
            button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
            add_drop_shadow(button)

    def get_selected_time(self):
        return self.time_edit.time().toString("HH:mm")
    
class MusicAppUI(QMainWindow):
    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.setWindowTitle("Sinal")
        self.setWindowIcon(QIcon('assets/icon.png'))
        self.setFixedSize(450, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.central_widget.setLayout(self.layout)
        self.setStyleSheet("")
        self.central_widget.setStyleSheet("background-color: #003b71;")

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 0)
        self.content_layout.setSpacing(10)
        self.content_widget.setLayout(self.content_layout)
        self.layout.addWidget(self.content_widget)

        self.relogio_label = QLabel()
        fonte_relogio = QFont()
        fonte_relogio.setPointSize(14)
        fonte_relogio.setBold(False)
        self.relogio_label.setFont(fonte_relogio)
        self.relogio_label.setStyleSheet("color: white; background-color: transparent;")
        self.content_layout.addWidget(self.relogio_label)

        self.status_label = QLabel("Status: Aguardando")
        fonte_status = QFont()
        fonte_status.setPointSize(12)
        fonte_status.setBold(False)
        self.status_label.setFont(fonte_status)
        self.status_label.setStyleSheet("color: white; background-color: transparent;")
        self.content_layout.addWidget(self.status_label)

        self.day_buttons_layout = QHBoxLayout()
        self.content_layout.addLayout(self.day_buttons_layout)

        self.buttons = {}
        fonte_dias = QFont()
        fonte_dias.setPointSize(10)
        days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
        for day in days:
            button = QPushButton(day)
            button.setCheckable(True)
            button.setFixedSize(80, 35)
            button.setFont(fonte_dias)
            button.setStyleSheet("QPushButton { background-color: white; color: black; border-radius: 5px; border: 1px solid black; } QPushButton:checked { background-color: #f1c50e; }")
            button.clicked.connect(self.on_day_button_clicked)
            self.day_buttons_layout.addWidget(button)
            add_drop_shadow(button)
            self.buttons[day.lower()] = button

        self.setup_table_widget()

        self.content_layout.addWidget(self.table_widget)
        self.content_layout.setStretch(3, 1)

        self.bottom_widget = QWidget()
        self.bottom_widget.setStyleSheet("background-color: #f1c50e;")
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(10, 10, 10, 10)
        self.bottom_layout.setSpacing(10)
        self.bottom_widget.setLayout(self.bottom_layout)
        self.layout.addWidget(self.bottom_widget)
        self.layout.setStretch(0, 1)

        self.novo_button = QPushButton("Novo")
        self.novo_button.setFixedSize(90, 40)
        font = self.novo_button.font()
        font.setPointSize(14)
        self.novo_button.setFont(font)
        self.novo_button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
        self.novo_button.setToolTip("Criar novo sinal")
        self.novo_button.clicked.connect(self.adicionar_nova_musica)
        self.bottom_layout.addWidget(self.novo_button)
        add_drop_shadow(self.novo_button)

        self.play_button = QPushButton("Play")
        self.play_button.setFixedSize(90, 40)
        font = self.play_button.font()
        font.setPointSize(14)
        self.play_button.setFont(font)
        self.play_button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
        self.play_button.setToolTip("Toca a musica selecionada")
        self.play_button.clicked.connect(self.play_selected_music)
        self.bottom_layout.addWidget(self.play_button)
        add_drop_shadow(self.play_button)

        self.stop_button = QPushButton("Parar")
        self.stop_button.setFixedSize(90, 40)
        font = self.stop_button.font()
        font.setPointSize(14)
        self.stop_button.setFont(font)
        self.stop_button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
        self.stop_button.setToolTip("Para de tocar imediatamente")
        self.stop_button.clicked.connect(self.stop_playing_music)
        self.bottom_layout.addWidget(self.stop_button)
        add_drop_shadow(self.stop_button)

        self.deletar_button = QPushButton("Deletar")
        self.deletar_button.setFixedSize(90, 40)
        font = self.deletar_button.font()
        font.setPointSize(14)
        self.deletar_button.setFont(font)
        self.deletar_button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
        self.deletar_button.setToolTip("Deleta as musicas selecionadas")
        self.deletar_button.clicked.connect(self.deletar_musicas_selecionadas)
        self.bottom_layout.addWidget(self.deletar_button)
        add_drop_shadow(self.deletar_button)
        
        self.info_button = QPushButton("?")
        self.info_button.setFixedSize(40, 40)
        font = self.info_button.font()
        font.setPointSize(14)
        self.info_button.setFont(font)
        self.info_button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
        self.info_button.setToolTip("Informações")
        self.info_button.clicked.connect(self.show_info_dialog)
        self.bottom_layout.addWidget(self.info_button)
        add_drop_shadow(self.info_button)

        self.atualizar_relogio()  

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_relogio)
        self.timer.start(1000)  

        self.selected_day = None
        self.player = QMediaPlayer()
        self.player.stateChanged.connect(self.on_player_state_changed)
        self.music_played = False
        QTimer.singleShot(1000, self.select_current_day_button)
        self.day_check_timer = QTimer(self)
        self.day_check_timer.timeout.connect(self.verificar_dia_atual)
        self.day_check_timer.start(4 * 60 * 60 * 1000)  # 4 horas em milissegundos

    def show_info_dialog(self):
        info_dialog = InfoDialog(self)
        info_dialog.exec_()

    def setup_table_widget(self):
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)  # Ajuste o número de colunas para 3
        self.table_widget.setHorizontalHeaderLabels(["Hora", "Nome", "Música"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.horizontalHeader().setVisible(True)
        self.table_widget.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: lightgray; }")
        self.table_widget.setStyleSheet("QTableWidget { background-color: rgba(3, 119, 175, 0.5); color: white; border: 1px solid lightgray; gridline-color: lightgray; }")
        self.table_widget.itemDoubleClicked.connect(self.editar_musica)

    def verificar_dia_atual(self):
        current_day = QDate.currentDate().dayOfWeek()
        if current_day <= 5:  # Apenas dias úteis (segunda a sexta)
            current_day_str = ["segunda", "terça", "quarta", "quinta", "sexta"][current_day - 1]
            self.set_selected_day(current_day_str)
            self.show_musicas()
        # No fim de semana, não alterar o dia selecionado

    def set_selected_day(self, day):
        for button_day, button in self.buttons.items():
            button.setChecked(button_day == day)
        self.selected_day = day

    def atualizar_relogio(self):
        hora_atual = QTime.currentTime()
        self.relogio_label.setText(hora_atual.toString('HH:mm:ss'))
        dia_semana_atual = QDate.currentDate().dayOfWeek()
        if dia_semana_atual in [1, 2, 3, 4, 5]:
            dia_atual_db = ["segunda", "terça", "quarta", "quinta", "sexta"][dia_semana_atual - 1]
            self.verificar_musicas_automaticas(dia_atual_db, hora_atual)

    def verificar_itens_similares(self, hora, nome, musica):
        dias_similares = []
        dias = ["segunda", "terça", "quarta", "quinta", "sexta"]
        for dia in dias:
            if dia == self.selected_day:
                continue
            musicas_dia = self.logic.get_musicas_por_dia(dia)
            for h, n, m in musicas_dia:
                if h == hora and n == nome and m == musica:
                    dias_similares.append(dia)
                    break  # Encontrou no dia, não precisa verificar mais
        return dias_similares

    def verificar_musicas_automaticas(self, dia, hora_atual):
        musicas = self.logic.get_musicas_por_dia(dia)
        current_time_str = hora_atual.toString("HH:mm")

        for hora, nome, musica in musicas:
            hora_musica = QTime.fromString(hora, "HH:mm")
            if hora_musica.toString("HH:mm") == current_time_str:
                if not self.music_played:  # Verifica se a música já foi tocada
                    self.player.setMedia(QMediaContent(QUrl.fromLocalFile(musica)))
                    self.player.play()
                    self.status_label.setText(f"Status: Reproduzindo {nome} automaticamente")
                    self.music_played = True
                break
        else:
            self.music_played = False  # Reset para permitir que a música seja tocada no próximo horário

    def on_day_button_clicked(self):
        clicked_button = self.sender()
        self.set_selected_day([day for day, button in self.buttons.items() if button is clicked_button][0])
        self.show_musicas()

    def select_current_day_button(self):
        current_day = QDate.currentDate().dayOfWeek()
        if current_day <= 5:  # Apenas dias úteis (segunda a sexta)
            current_day_str = ["segunda", "terça", "quarta", "quinta", "sexta"][current_day - 1]
            self.set_selected_day(current_day_str)
            self.show_musicas()
        else:
            # No fim de semana, selecionar segunda como padrão ou manter atual
            self.set_selected_day("segunda")
            self.show_musicas()

    def show_musicas(self):
        if not self.selected_day:
            return

        self.table_widget.setRowCount(0)
        musicas = self.logic.get_musicas_por_dia(self.selected_day)
        musicas = sorted(musicas, key=lambda x: x[0])

        for i, (hora, nome, musica) in enumerate(musicas):
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(hora))  # Coluna 0
            self.table_widget.setItem(i, 1, QTableWidgetItem(nome))  # Coluna 1
            item_musica = QTableWidgetItem(os.path.basename(musica))
            item_musica.setData(Qt.UserRole, musica)  # Armazenar caminho completo
            self.table_widget.setItem(i, 2, item_musica)  # Coluna 2

    def adicionar_nova_musica(self):
        hora_dialog = HoraInputDialog(self)
        if hora_dialog.exec() != QDialog.Accepted:
            return

        hora = hora_dialog.get_selected_time()

        nome_dialog = EditDialog(input_type="text", parent=self)
        nome_dialog.label.setText("Nome da Música:")
        if nome_dialog.exec() != QDialog.Accepted:
            return
        nome = nome_dialog.get_input()
        if not nome:
            return

        dialog = DaySelectionDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        dias_selecionados = dialog.get_selected_days()
        if not dias_selecionados:
            return

        arquivo_musica, _ = QFileDialog.getOpenFileName(self, "Selecione a música", "", "MP3 Files (*.mp3)")
        if not arquivo_musica:
            return

        for dia in dias_selecionados:
            self.logic.adicionar_musica(dia, hora, nome, arquivo_musica)
        self.show_musicas()

    def deletar_musicas_selecionadas(self):
        rows = sorted(set(index.row() for index in self.table_widget.selectedIndexes()), reverse=True)
        print(f"Linhas selecionadas para deletar: {rows}")
        for row in rows:
            hora = self.table_widget.item(row, 0).text()
            nome = self.table_widget.item(row, 1).text()
            musica = self.table_widget.item(row, 2).data(Qt.UserRole)
            print(f"Deletando: dia={self.selected_day}, hora={hora}, nome={nome}, musica={musica}")
            # Verificar se há itens similares em outros dias
            dias_similares = self.verificar_itens_similares(hora, nome, musica)
            print(f"Dias com itens similares: {dias_similares}")
            if dias_similares:
                # Mostrar diálogo de confirmação
                dialog = DeleteConfirmationDialog(dias_similares, self)
                if dialog.exec() == QDialog.Accepted:
                    dias_para_deletar = [self.selected_day] + dialog.get_selected_days()
                    print(f"Deletando de dias: {dias_para_deletar}")
                    for dia in dias_para_deletar:
                        self.logic.deletar_musica(dia, hora, nome)
                else:
                    print("Deletar cancelado")
                    continue
            else:
                self.logic.deletar_musica(self.selected_day, hora, nome)
            self.table_widget.removeRow(row)

    def play_selected_music(self):
        selected_row = self.table_widget.currentRow()
        if selected_row == -1:
            self.status_label.setText("Status: Nenhum item selecionado")
            return

        item = self.table_widget.item(selected_row, 2)
        if item is None:
            self.status_label.setText("Status: Item de música não encontrado")
            return

        music_file = item.data(Qt.UserRole)
        if not music_file:
            self.status_label.setText("Status: Caminho do arquivo de música está vazio")
            return

        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(music_file)))
        self.player.play()
        self.status_label.setText("Status: Reproduzindo manualmente")

    def stop_playing_music(self):
        self.player.stop()
        self.status_label.setText("Status: Aguardando")

    def on_player_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self.status_label.setText("Status: Aguardando")

    def editar_musica(self, item):
        row = item.row()
        column = item.column()

        if column == 0:
            campo = "hora"
        elif column == 1:
            campo = "nome"
        elif column == 2:
            campo = "musica"
        else:
            return

        hora = self.table_widget.item(row, 0).text()
        nome = self.table_widget.item(row, 1).text()

        if column in [0, 1]:  # Coluna 1: Hora, Coluna 2: Nome
            if column == 0:  # Se for a coluna de hora
                dialog = EditDialog(input_type="time", parent=self)
            elif column == 1:  # Se for a coluna de nome
                dialog = EditDialog(input_type="text", parent=self)
    
            if dialog.exec() != QDialog.Accepted:
                return

            nova_informacao = dialog.get_input()
            if nova_informacao:
                self.logic.editar_musica(self.selected_day, hora, nome, campo, nova_informacao)
                self.show_musicas()
                if column == 1:  # Se a hora foi alterada
                    self.verificar_musicas_automaticas(self.selected_day, QTime.currentTime())

        elif column == 2:  # Coluna 2: Arquivo de música
            arquivo_musica, _ = QFileDialog.getOpenFileName(self, "Selecione a nova música", "", "MP3 Files (*.mp3)")
            if arquivo_musica:
                self.logic.editar_musica(self.selected_day, hora, nome, campo, arquivo_musica)
                self.show_musicas()

    def verificar_musicas_automaticas(self, dia, hora_atual):
        musicas = self.logic.get_musicas_por_dia(dia)
        current_time_str = hora_atual.toString("HH:mm")
        
        for hora, nome, musica in musicas:
            hora_musica = QTime.fromString(hora, "HH:mm")
            if hora_musica.toString("HH:mm") == current_time_str:
                if not self.music_played:  # Verifica se a música já foi tocada
                    self.player.setMedia(QMediaContent(QUrl.fromLocalFile(musica)))
                    self.player.play()
                    self.status_label.setText(f"Status: Reproduzindo {nome} automaticamente")
                    self.music_played = True
                break
        else:
            self.music_played = False  # Reset para permitir que a música seja tocada no próximo horário

class Player(QMainWindow):
    def __init__(self):
        super().__init__()
        # Inicializa outras partes da classe
        self.musica_ja_tocada = False
        self.ultimo_horario_verificado = None
        self.timer_musica = QTimer(self)
        self.timer_musica.setSingleShot(True)  # Tocar a música apenas uma vez por evento
        self.table_widget.setItemDelegateForColumn(0, QStyledItemDelegate(self))
        self.table_widget.setItemDelegateForColumn(1, QStyledItemDelegate(self))
        self.table_widget.setItemDelegateForColumn(2, QStyledItemDelegate(self))
        self.table_widget.setItemDelegateForColumn(3, QStyledItemDelegate(self))
        
    def verificar_musicas_automaticas(self, dia, hora_atual):
        musicas = self.logic.get_musicas_por_dia(dia)
        
        # Reseta o sinalizador a cada novo minuto
        if hora_atual != self.ultimo_horario_verificado:
            self.musica_ja_tocada = False

        for hora, nome, musica in musicas:
            hora_musica = QTime.fromString(hora, "HH:mm")
            if hora_musica.hour() == hora_atual.hour() and hora_musica.minute() == hora_atual.minute():
                if not self.musica_ja_tocada:
                    self.timer_musica.timeout.connect(lambda: self.tocar_musica(musica, nome))
                    self.timer_musica.start(1000)  # Espera 1 segundo antes de tocar a música
                    self.musica_ja_tocada = True
                break

        # Atualiza o último horário verificado
        self.ultimo_horario_verificado = hora_atual

    def tocar_musica(self, musica, nome):
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(musica)))
        self.player.play()
        self.status_label.setText(f"Status: Reproduzindo {nome} automaticamente")

class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Informações do App")
        self.setStyleSheet("background-color: white;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 20, 24, 20)
        self.layout.setSpacing(20)

        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)

        tips_font = QFont()
        tips_font.setPointSize(11)

        info_font = QFont()
        info_font.setPointSize(10)

        tips_container = QFrame(self)
        tips_container.setStyleSheet("QFrame { background-color: #f6f6f6; border: 1px solid #d4d4d4; border-radius: 8px; }")
        tips_layout = QVBoxLayout(tips_container)
        tips_layout.setContentsMargins(16, 16, 16, 16)
        tips_layout.setSpacing(10)

        tips_title = QLabel("Dicas:", tips_container)
        tips_title.setFont(title_font)
        tips_title.setStyleSheet("color: #1f1f1f;")
        tips_layout.addWidget(tips_title)

        tips_text = QLabel(
            "<ul style='margin: 0; padding-left: 18px;'>"
            "<li>Ao clicar duas vezes sobre um item na tabela, você pode editá-lo.</li>"
            "<li>Mantenha a pasta com as músicas sempre junto com este programa para evitar problemas.</li>"
            "<li>Use o botão 'Novo' para adicionar sinais aos dias.</li>"
            "<li>Selecione um item e clique em 'Play' para ouvir a música.</li>"
            "<li>O aplicativo toca músicas automaticamente no horário programado.</li>"
            "</ul>",
            tips_container,
        )
        tips_text.setFont(tips_font)
        tips_text.setWordWrap(True)
        tips_text.setStyleSheet("color: #333333;")
        tips_layout.addWidget(tips_text)

        self.layout.addWidget(tips_container)

        self.info_label = QLabel("Versão 1.2.21<br>Desenvolvido por Luiz Gustavo Stelo<br>ASM", self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFont(info_font)
        self.info_label.setStyleSheet("color: #333333;")
        self.layout.addWidget(self.info_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.ok_button = QPushButton("OK", self)
        self.ok_button.setFont(tips_font)
        self.ok_button.setFixedSize(90, 40)
        self.ok_button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
        add_drop_shadow(self.ok_button)
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        button_layout.addStretch()
        self.layout.addLayout(button_layout)

class DaySelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleção de Dias")
        self.setStyleSheet("background-color: white;")
        self.layout = QVBoxLayout(self)

        self.checkboxes = {}
        for day in ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]:
            checkbox = QCheckBox(day, self)
            self.layout.addWidget(checkbox)
            self.checkboxes[day.lower()] = checkbox

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        for button in self.button_box.buttons():
            button.setFixedSize(90, 40)
            button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
            add_drop_shadow(button)

    def get_selected_days(self):
        return [day for day, checkbox in self.checkboxes.items() if checkbox.isChecked()]

class DeleteConfirmationDialog(QDialog):
    def __init__(self, dias_similares, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirmar Deletar")
        self.setStyleSheet("background-color: white;")
        self.layout = QVBoxLayout(self)

        self.label = QLabel("Foram encontrados itens similares nos seguintes dias. Deseja deletar também desses dias?", self)
        self.layout.addWidget(self.label)

        self.checkboxes = {}
        for dia in dias_similares:
            checkbox = QCheckBox(dia.capitalize(), self)
            self.layout.addWidget(checkbox)
            self.checkboxes[dia] = checkbox

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        for button in self.button_box.buttons():
            button.setFixedSize(90, 40)
            button.setStyleSheet("background-color: white; color: black; border-radius: 5px; border: 1px solid black;")
            add_drop_shadow(button)

    def get_selected_days(self):
        return [dia for dia, checkbox in self.checkboxes.items() if checkbox.isChecked()]
    

def center_window(window):
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())

def main():
    app = QApplication(sys.argv)
    logic = MusicAppLogic("dados.db")
    window = MusicAppUI(logic)
    center_window(window)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
