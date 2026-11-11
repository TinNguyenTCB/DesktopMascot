from PySide6.QtCore import QPoint, QTime, QTimer, Qt
from PySide6.QtGui import QAction, QGuiApplication, QMovie, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .ai import GeminiWorker
from .data import CHARACTERS, GEMINI_API_KEY, LANGUAGES, ROLES, resolve_asset_path
from .utils import format_seconds_to_readable


class ChatDialog(QDialog):
    def __init__(self, mascot_window):
        super().__init__(None)
        self.mascot_window = mascot_window
        self.lang = LANGUAGES.get(self.mascot_window.current_language, LANGUAGES["🇻🇳 Tiếng Việt"])

        self.is_locked = True
        self.internal_moving = False
        self.drag_offset = QPoint()

        self.setWindowTitle(self.lang["title_chat"])
        self.resize(320, 360)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        self.setStyleSheet("""
            QDialog { background-color: #21252b; color: #ffffff; border: 2px solid #61afef; border-radius: 12px; }
            QTextEdit { background-color: #282c34; border: 1px solid #4b5263; color: #abb2bf; border-radius: 8px; padding: 8px; }
            QLineEdit { background-color: #282c34; border: 1px solid #4b5263; color: #ffffff; border-radius: 6px; padding: 6px; }
            QPushButton { background-color: #61afef; color: #ffffff; border-radius: 6px; font-weight: bold; padding: 6px 12px; }
            QPushButton:hover { background-color: #528bff; }
            QPushButton#btnLock { background-color: #3b4048; padding: 4px 8px; border-radius: 4px; }
            QPushButton#btnLock:hover { background-color: #4b5263; }
        """)

        layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        self.btn_lock = QPushButton("🔒")
        self.btn_lock.setObjectName("btnLock")
        self.btn_lock.setToolTip("Click để Mở khóa / Khóa vị trí cửa sổ chat")
        self.btn_lock.setAutoDefault(False)
        self.btn_lock.setDefault(False)
        self.btn_lock.clicked.connect(self.toggle_lock)

        top_bar.addStretch()
        top_bar.addWidget(self.btn_lock)
        layout.addLayout(top_bar)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.lang["chat_ph"])
        self.btn_send = QPushButton(self.lang["chat_send"])
        self.btn_send.setAutoDefault(False)
        self.btn_send.setDefault(False)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.btn_send)
        layout.addLayout(input_layout)

        self.btn_send.clicked.connect(self.send_message)
        self.input_field.returnPressed.connect(self.send_message)

    def move(self, *args):
        if not self.is_locked and not self.internal_moving:
            return
        super().move(*args)

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.btn_lock.setText("🔒")
            self.snap_to_mascot()
        else:
            self.btn_lock.setText("🔓")

    def update_position(self):
        if self.is_locked:
            self.snap_to_mascot()

    def snap_to_mascot(self):
        m_x = self.mascot_window.x()
        m_y = self.mascot_window.y() - self.mascot_window.get_current_y_offset()
        pop_x = m_x - (self.width() - self.mascot_window.width()) // 2
        pop_y = m_y - self.height() - 15

        self.internal_moving = True
        super().move(pop_x, pop_y)
        self.internal_moving = False

    def update_ui_language(self):
        self.lang = LANGUAGES.get(self.mascot_window.current_language, LANGUAGES["🇻🇳 Tiếng Việt"])
        self.setWindowTitle(self.lang["title_chat"])
        self.input_field.setPlaceholderText(self.lang["chat_ph"])
        self.btn_send.setText(self.lang["chat_send"])

    def mousePressEvent(self, event):
        if not self.is_locked and event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.is_locked and event.buttons() == Qt.MouseButton.LeftButton:
            target_pos = event.globalPosition().toPoint() - self.drag_offset
            self.internal_moving = True
            super().move(target_pos)
            self.internal_moving = False
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def send_message(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return

        user_label = self.lang.get("chat_user_label", "Bạn")
        self.chat_history.append(f"<b>{user_label}:</b> {user_text}")
        self.input_field.clear()
        self.btn_send.setEnabled(False)
        self.chat_history.append(self.lang["chat_thinking"])

        default_prompt = list(ROLES.values())[0]
        role_prompt = ROLES.get(self.mascot_window.current_role, default_prompt)

        self.worker = GeminiWorker(
            user_text,
            GEMINI_API_KEY,
            role_prompt,
            self.mascot_window.reminders,
            self.mascot_window.current_language,
        )
        self.worker.response_received.connect(self.handle_response)
        self.worker.start()

    def handle_response(self, response_text, reminder_data, delete_index):
        self.chat_history.append(f"<b>{self.mascot_window.get_mascot_name()}:</b> {response_text}\n")
        if reminder_data:
            self.mascot_window.add_custom_reminder(reminder_data)
        if delete_index is not None and delete_index >= 0:
            self.mascot_window.remove_custom_reminder(delete_index)
        self.btn_send.setEnabled(True)

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class SetupDialog(QDialog):
    def __init__(self, current_char, current_role, current_lang, parent=None):
        super().__init__(parent)
        self.current_lang = current_lang
        self.lang = LANGUAGES.get(current_lang, LANGUAGES["🇻🇳 Tiếng Việt"])

        self.setWindowTitle(self.lang["title_setup"])
        self.resize(480, 520)
        self.setStyleSheet("""
            QDialog { background-color: #282c34; color: #ffffff; border-radius: 10px; }
            QGroupBox { font-weight: bold; border: 1px solid #61afef; border-radius: 8px; margin-top: 10px; padding-top: 10px; color: #61afef; }
            QRadioButton { color: #ffffff; font-size: 13px; font-weight: bold; padding: 4px; }
            QRadioButton::indicator:checked { background-color: #61afef; border: 2px solid #ffffff; border-radius: 6px; }
            QComboBox { background-color: #21252b; color: #ffffff; border: 1px solid #4b5263; padding: 6px; border-radius: 5px; }
            QPushButton { background-color: #61afef; color: #ffffff; font-weight: bold; padding: 10px 15px; border-radius: 6px; font-size: 14px; }
            QPushButton:hover { background-color: #528bff; }
        """)

        layout = QVBoxLayout(self)

        self.group_char = QGroupBox(self.lang["group_char"])
        grid_layout = QGridLayout(self.group_char)

        self.btn_group = QButtonGroup(self)
        self.movies = []
        self.radio_buttons = {}

        positions = {
            "🦈 Sharkun": (0, 0, 1),
            "🐳 Whaly": (0, 1, 1),
            "🐟 Pinkun": (1, 0, 1),
            "🐸 Frog": (1, 1, 1),
        }

        for char_key, char_info in CHARACTERS.items():
            row, col, col_span = positions.get(char_key, (0, 0, 1))

            col_widget = QWidget()
            col_layout = QVBoxLayout(col_widget)
            col_layout.setContentsMargins(0, 0, 0, 0)

            radio = QRadioButton(char_key)
            self.btn_group.addButton(radio)
            self.radio_buttons[char_key] = radio
            col_layout.addWidget(radio, alignment=Qt.AlignmentFlag.AlignCenter)

            label_gif = QLabel()
            if char_key == "🐟 Pinkun":
                label_gif.setFixedSize(75, 75)
            else:
                label_gif.setFixedSize(90, 90)
            label_gif.setAlignment(Qt.AlignmentFlag.AlignCenter)

            preview_file = resolve_asset_path(char_info.get("preview_gif", "Wave.gif"))
            movie = QMovie(preview_file)
            if movie.isValid():
                label_gif.setMovie(movie)
                label_gif.setScaledContents(True)
                movie.start()
                self.movies.append(movie)
            else:
                label_gif.setText(f"{char_key[:2]}\n[No Preview]")
                label_gif.setStyleSheet("border: 1px dashed #4b5263; border-radius: 8px;")

            col_layout.addWidget(label_gif, alignment=Qt.AlignmentFlag.AlignCenter)
            grid_layout.addWidget(col_widget, row, col, 1, col_span, alignment=Qt.AlignmentFlag.AlignCenter)

        if current_char in self.radio_buttons:
            self.radio_buttons[current_char].setChecked(True)
        else:
            list(self.radio_buttons.values())[0].setChecked(True)

        layout.addWidget(self.group_char)

        self.group_role = QGroupBox(self.lang["group_role"])
        role_layout = QVBoxLayout(self.group_role)
        self.combo_role = QComboBox()
        self.combo_role.addItems(list(ROLES.keys()))
        if current_role in ROLES:
            self.combo_role.setCurrentText(current_role)
        role_layout.addWidget(self.combo_role)
        layout.addWidget(self.group_role)

        self.group_lang = QGroupBox(self.lang["group_lang"])
        lang_layout = QVBoxLayout(self.group_lang)
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(list(LANGUAGES.keys()))
        if current_lang in LANGUAGES:
            self.combo_lang.setCurrentText(current_lang)
        lang_layout.addWidget(self.combo_lang)
        layout.addWidget(self.group_lang)

        self.btn_start = QPushButton(self.lang["btn_start"])
        layout.addWidget(self.btn_start)

        self.combo_lang.currentIndexChanged.connect(self.on_language_changed)
        self.btn_start.clicked.connect(self.accept)

    def on_language_changed(self):
        new_lang_key = self.combo_lang.currentText()
        self.lang = LANGUAGES.get(new_lang_key, LANGUAGES["🇻🇳 Tiếng Việt"])

        self.setWindowTitle(self.lang["title_setup"])
        self.group_char.setTitle(self.lang["group_char"])
        self.group_role.setTitle(self.lang["group_role"])
        self.group_lang.setTitle(self.lang["group_lang"])
        self.btn_start.setText(self.lang["btn_start"])

    def get_config(self):
        selected_char = list(CHARACTERS.keys())[0]
        for char_key, radio in self.radio_buttons.items():
            if radio.isChecked():
                selected_char = char_key
                break

        return {
            'character': selected_char,
            'role': self.combo_role.currentText(),
            'language': self.combo_lang.currentText(),
        }


class SpeechBubble(QWidget):
    expired = QDialog.Signal if False else None

    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        from PySide6.QtCore import Signal
        self.expired = Signal(object, dict)
        self.item_data = item_data
        display_time_ms = item_data.get('duration', 5) * 1000

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.label = QLabel(item_data.get('text', ''), self)
        self.label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                color: #282c34;
                font-size: 13px;
                font-weight: bold;
                border-radius: 12px;
                padding: 10px;
                border: 2px solid #61afef;
            }
        """)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(220)
        self.label.adjustSize()
        self.adjustSize()

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.on_timeout)
        self.hide_timer.start(display_time_ms)

    def on_timeout(self):
        self.expired.emit(self, self.item_data)
        self.close()
        self.deleteLater()


class QuickChatBubble(QWidget):
    def __init__(self, mascot_window, parent=None):
        super().__init__(parent)
        self.mascot_window = mascot_window
        lang = self.mascot_window.get_lang()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.btn_quick = QPushButton(lang.get("quick_chat_btn", "💬 Chat"))
        self.btn_quick.setStyleSheet("""
            QPushButton {
                background-color: #61afef;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                border-radius: 10px;
                padding: 6px 12px;
                border: 2px solid #ffffff;
            }
            QPushButton:hover {
                background-color: #528bff;
            }
        """)
        self.btn_quick.clicked.connect(self.on_click)
        layout.addWidget(self.btn_quick)
        self.adjustSize()

    def enterEvent(self, event):
        self.mascot_window.hide_quick_timer.stop()
        self.mascot_window.hover_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.mascot_window.hide_quick_timer.start(200)
        super().leaveEvent(event)

    def update_position(self):
        m_x = self.mascot_window.x()
        m_y = self.mascot_window.y() - self.mascot_window.get_current_y_offset()
        pop_x = m_x + (self.mascot_window.width() - self.width()) // 2
        pop_y = m_y - self.height() - 8
        self.move(pop_x, pop_y)

    def on_click(self):
        self.hide()
        self.mascot_window.open_chat_dialog()


class ReminderEditDialog(QDialog):
    def __init__(self, mascot_window, item_data=None, parent=None):
        super().__init__(parent)
        self.mascot_window = mascot_window
        self.lang = LANGUAGES.get(self.mascot_window.current_language, LANGUAGES["🇻🇳 Tiếng Việt"])

        self.setWindowTitle(self.lang["title_reminder_edit"])
        self.resize(380, 280)

        self.setStyleSheet("""
            QDialog {
                background-color: #21252b;
                color: #ffffff;
                border: 2px solid #61afef;
                border-radius: 12px;
            }
            QLabel {
                color: #abb2bf;
                font-weight: bold;
                font-size: 12px;
            }
            QLabel:disabled {
                color: #5c6370;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #282c34;
                border: 1px solid #4b5263;
                color: #ffffff;
                border-radius: 6px;
                padding: 5px;
                font-size: 12px;
            }
            QLineEdit:disabled, QSpinBox:disabled {
                background-color: #1b1d23;
                border: 1px solid #353b45;
                color: #5c6370;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #61afef;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                border-left: 1px solid #4b5263;
                border-bottom: 1px solid #4b5263;
                border-top-right-radius: 6px;
                background-color: #3b4048;
            }
            QSpinBox::up-button:hover {
                background-color: #61afef;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                border-left: 1px solid #4b5263;
                border-bottom-right-radius: 6px;
                background-color: #3b4048;
            }
            QSpinBox::down-button:hover {
                background-color: #61afef;
            }
            QPushButton {
                background-color: #61afef;
                color: #ffffff;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #528bff;
            }
            QPushButton#btnCancel {
                background-color: #4b5263;
            }
            QPushButton#btnCancel:hover {
                background-color: #5c6370;
            }
        """)

        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText(self.lang["lbl_content"])
        self.input_text.textChanged.connect(self.reset_input_style)

        self.combo_type = QComboBox()
        self.combo_type.addItems([self.lang["type_interval"], self.lang["type_alarm"]])

        self.interval_container = QWidget()
        interval_layout = QHBoxLayout(self.interval_container)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.setSpacing(4)

        self.spin_hours = QSpinBox()
        self.spin_hours.setRange(0, 23)
        self.spin_hours.setSuffix(self.lang["unit_hour"])

        self.spin_mins = QSpinBox()
        self.spin_mins.setRange(0, 59)
        self.spin_mins.setSuffix(self.lang["unit_min"])

        self.spin_secs = QSpinBox()
        self.spin_secs.setRange(0, 59)
        self.spin_secs.setSuffix(self.lang["unit_sec"])

        interval_layout.addWidget(self.spin_hours)
        interval_layout.addWidget(self.spin_mins)
        interval_layout.addWidget(self.spin_secs)

        self.alarm_container = QWidget()
        alarm_layout = QHBoxLayout(self.alarm_container)
        alarm_layout.setContentsMargins(0, 0, 0, 0)
        alarm_layout.setSpacing(4)

        self.alarm_spin_hours = QSpinBox()
        self.alarm_spin_hours.setRange(0, 23)
        self.alarm_spin_hours.setSuffix(self.lang["unit_hour"])
        self.alarm_spin_hours.setValue(QTime.currentTime().hour())

        self.alarm_spin_mins = QSpinBox()
        self.alarm_spin_mins.setRange(0, 59)
        self.alarm_spin_mins.setSuffix(self.lang["unit_min"])
        self.alarm_spin_mins.setValue(QTime.currentTime().minute())

        alarm_layout.addWidget(self.alarm_spin_hours)
        alarm_layout.addWidget(self.alarm_spin_mins)

        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(1, 60)
        self.spin_duration.setSuffix(self.lang["unit_sec"])
        self.spin_duration.setValue(5)

        self.lbl_interval = QLabel(self.lang["lbl_interval"])
        self.lbl_alarm_time = QLabel(self.lang["lbl_alarm_time"])

        layout.addRow(self.lang["lbl_content"], self.input_text)
        layout.addRow(self.lang["lbl_type"], self.combo_type)
        layout.addRow(self.lbl_interval, self.interval_container)
        layout.addRow(self.lbl_alarm_time, self.alarm_container)
        layout.addRow(self.lang["lbl_duration"], self.spin_duration)

        btn_box = QHBoxLayout()
        btn_save = QPushButton(self.lang["btn_save"])
        btn_cancel = QPushButton(self.lang["btn_cancel"])
        btn_cancel.setObjectName("btnCancel")

        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addRow(btn_box)

        self.combo_type.currentIndexChanged.connect(self.toggle_type_view)
        btn_save.clicked.connect(self.on_save_clicked)
        btn_cancel.clicked.connect(self.reject)

        if item_data:
            self.input_text.setText(item_data.get('text', ''))
            self.spin_duration.setValue(item_data.get('duration', 5))
            if item_data.get('type') == 'alarm':
                self.combo_type.setCurrentIndex(1)
                alarm_parts = item_data.get('alarm_time', '00:00').split(':')
                if len(alarm_parts) == 2:
                    self.alarm_spin_hours.setValue(int(alarm_parts[0]))
                    self.alarm_spin_mins.setValue(int(alarm_parts[1]))
            else:
                self.combo_type.setCurrentIndex(0)
                tot_secs = item_data.get('interval', 10)
                h = tot_secs // 3600
                m = (tot_secs % 3600) // 60
                s = tot_secs % 60
                self.spin_hours.setValue(h)
                self.spin_mins.setValue(m)
                self.spin_secs.setValue(s)

        self.toggle_type_view()

    def reset_input_style(self):
        self.input_text.setStyleSheet("""
            QLineEdit {
                background-color: #282c34;
                border: 1px solid #4b5263;
                color: #ffffff;
                border-radius: 6px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #61afef;
            }
        """)

    def on_save_clicked(self):
        text_content = self.input_text.text().strip()
        if not text_content:
            self.input_text.setStyleSheet("""
                QLineEdit {
                    background-color: #282c34;
                    border: 2px solid #e06c75;
                    color: #ffffff;
                    border-radius: 6px;
                    padding: 5px;
                }
            """)
            self.input_text.setFocus()

            warning_msg = "⚠️ Hãy nhập nội dung lời nhắc trước khi lưu nhé!" if self.mascot_window.current_language == "🇻🇳 Tiếng Việt" else "⚠️ リマインダーの内容を入力してください！"
            err_data = {"text": warning_msg, "duration": 4, "type": "interval"}
            self.mascot_window.trigger_single_reminder(err_data)
            return

        self.accept()

    def toggle_type_view(self):
        is_alarm = self.combo_type.currentIndex() == 1

        self.spin_hours.setEnabled(not is_alarm)
        self.spin_mins.setEnabled(not is_alarm)
        self.spin_secs.setEnabled(not is_alarm)
        self.lbl_interval.setEnabled(not is_alarm)

        self.alarm_spin_hours.setEnabled(is_alarm)
        self.alarm_spin_mins.setEnabled(is_alarm)
        self.lbl_alarm_time.setEnabled(is_alarm)

    def get_data(self):
        is_alarm = self.combo_type.currentIndex() == 1
        tot_secs = self.spin_hours.value() * 3600 + self.spin_mins.value() * 60 + self.spin_secs.value()
        if tot_secs < 5:
            tot_secs = 5

        alarm_str = f"{self.alarm_spin_hours.value():02d}:{self.alarm_spin_mins.value():02d}"

        return {
            'text': self.input_text.text().strip(),
            'type': 'alarm' if is_alarm else 'interval',
            'interval': tot_secs,
            'alarm_time': alarm_str,
            'duration': self.spin_duration.value(),
            'triggered_today': False,
        }


class ReminderManagerDialog(QDialog):
    def __init__(self, mascot_window, parent=None):
        super().__init__(parent)
        self.mascot_window = mascot_window
        self.lang = LANGUAGES.get(self.mascot_window.current_language, LANGUAGES["🇻🇳 Tiếng Việt"])

        self.setWindowTitle(self.lang["title_reminder_mgr"])
        self.resize(520, 360)

        self.setStyleSheet("""
            QDialog {
                background-color: #21252b;
                color: #ffffff;
                border: 2px solid #61afef;
                border-radius: 12px;
            }
            QListWidget {
                background-color: #282c34;
                border: 1px solid #4b5263;
                color: #abb2bf;
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                background-color: #21252b;
                border: 1px solid #3b4048;
                border-radius: 6px;
                margin-bottom: 6px;
                padding: 10px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #2c313a;
                border: 1px solid #61afef;
            }
            QListWidget::item:selected {
                background-color: #3e4451;
                border: 1px solid #61afef;
                color: #61afef;
                font-weight: bold;
            }
            QPushButton {
                background-color: #61afef;
                color: #ffffff;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #528bff;
            }
            QPushButton#btnDelete {
                background-color: #e06c75;
            }
            QPushButton#btnDelete:hover {
                background-color: #d15663;
            }
            QPushButton#btnClose {
                background-color: #4b5263;
            }
            QPushButton#btnClose:hover {
                background-color: #5c6370;
            }
        """)

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.load_reminders()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton(self.lang["btn_add"])
        btn_edit = QPushButton(self.lang["btn_edit"])
        btn_delete = QPushButton(self.lang["btn_delete"])
        btn_delete.setObjectName("btnDelete")
        btn_close = QPushButton(self.lang["btn_close"])
        btn_close.setObjectName("btnClose")

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        btn_add.clicked.connect(self.add_reminder)
        btn_edit.clicked.connect(self.edit_reminder)
        btn_delete.clicked.connect(self.delete_reminder)
        btn_close.clicked.connect(self.accept)

    def load_reminders(self):
        self.list_widget.clear()
        lbl_rem = self.lang["lbl_content"]
        lbl_rep = self.lang.get("lbl_repeat_prefix", "Lặp:")
        lbl_dur = self.lang.get("lbl_duration_prefix", "Kéo dài:")
        lbl_alm = self.lang.get("lbl_alarm_prefix", "Báo thức:")

        for data in self.mascot_window.reminders:
            text_val = data.get('text', '')
            dur_val = f"{data.get('duration', 5)}s"

            if data.get('type') == 'alarm':
                alm_val = data.get('alarm_time', '00:00')
                text_disp = f"💬 {lbl_rem} {text_val}   |   ⏰ {lbl_alm} {alm_val}   |   ⏱️ {lbl_dur} {dur_val}"
            else:
                interval_secs = data.get('interval', 10)
                readable_interval = format_seconds_to_readable(interval_secs)
                text_disp = f"💬 {lbl_rem} {text_val}   |   🔄 {lbl_rep} {readable_interval}   |   ⏱️ {lbl_dur} {dur_val}"

            item = QListWidgetItem(text_disp)
            item.setData(Qt.ItemDataRole.UserRole, data)
            self.list_widget.addItem(item)

    def add_reminder(self):
        dialog = ReminderEditDialog(self.mascot_window, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data['text']:
                self.mascot_window.add_custom_reminder(data)
                self.load_reminders()

    def edit_reminder(self):
        curr_item = self.list_widget.currentItem()
        if curr_item:
            old_data = curr_item.data(Qt.ItemDataRole.UserRole)
            row_idx = self.list_widget.currentRow()
            dialog = ReminderEditDialog(self.mascot_window, item_data=old_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.get_data()
                if new_data['text']:
                    self.mascot_window.update_custom_reminder(row_idx, new_data)
                    self.load_reminders()

    def delete_reminder(self):
        row_idx = self.list_widget.currentRow()
        if row_idx >= 0:
            self.mascot_window.remove_custom_reminder(row_idx)
            self.load_reminders()
