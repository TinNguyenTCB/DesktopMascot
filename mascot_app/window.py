import json
import os
import random
import sys

from PySide6.QtCore import QPoint, QTime, QTimer, Qt
from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QMovie, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QMenu, QMessageBox, QWidget

from .data import CHARACTERS, PROJECT_ROOT, LANGUAGES, ROLES, resolve_asset_path
from .dialogs import (
    ChatDialog,
    QuickChatBubble,
    ReminderManagerDialog,
    SetupDialog,
    SpeechBubble,
)


class MascotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.state = "Stay"
        self.previous_state = "Free"
        self.old_pos = QPoint()

        self.walk_direction = 1
        self.walk_speed = 3
        self.fall_speed = 8
        self.allow_cross_screen = True

        self.is_chat_locked = True
        self.is_first_run = True
        self.is_playing_temp_anim = False

        self.config_file_path = str(PROJECT_ROOT / "config.json")
        self.json_file_path = str(PROJECT_ROOT / "reminders.json")

        self.current_character = "🦈 Sharkun"
        self.current_role = "💕 Người yêu (Em - Iu) / 恋人 (彼女)"
        self.current_language = "🇻🇳 Tiếng Việt"
        self.load_config()

        self.reminders = self.load_reminders_from_file()
        self.reminder_timers = []
        self.active_bubbles = []

        self.chat_dialog = None
        self.quick_chat_bubble = None
        self.movie = None

        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.show_quick_chat)

        self.hide_quick_timer = QTimer(self)
        self.hide_quick_timer.setSingleShot(True)
        self.hide_quick_timer.timeout.connect(self.hide_quick_chat)

        self.init_ui()
        self.setup_reminder_timers()
        self.init_clock_checker()
        self.init_idle_animation_timer()
        self.init_movement_timer()

    def enterEvent(self, event):
        self.hide_quick_timer.stop()
        if not (self.chat_dialog and self.chat_dialog.isVisible()):
            if not (self.quick_chat_bubble and self.quick_chat_bubble.isVisible()):
                self.hover_timer.start(1000)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover_timer.stop()
        if self.quick_chat_bubble and self.quick_chat_bubble.isVisible():
            self.hide_quick_timer.start(300)
        super().leaveEvent(event)

    def show_quick_chat(self):
        if self.state in ["Sleep", "Falling", "Dragging"]:
            return
        if not self.quick_chat_bubble:
            self.quick_chat_bubble = QuickChatBubble(self)
        self.quick_chat_bubble.update_position()
        self.quick_chat_bubble.show()

    def hide_quick_chat(self):
        if self.quick_chat_bubble:
            self.quick_chat_bubble.hide()

    def open_chat_dialog(self):
        self.hide_quick_chat()
        from .ai import GEMINI_API_KEY
        if not GEMINI_API_KEY.strip():
            QMessageBox.warning(self, "API Key Error", "Set the GEMINI_API_KEY environment variable to use AI chat.")
            return

        if not self.chat_dialog:
            self.chat_dialog = ChatDialog(self)
            self.chat_dialog.snap_to_mascot()
        else:
            self.chat_dialog.update_ui_language()

        self.clear_all_bubbles()
        self.chat_dialog.show()
        self.chat_dialog.raise_()
        self.chat_dialog.activateWindow()

    def get_lang(self):
        return LANGUAGES.get(self.current_language, LANGUAGES["🇻🇳 Tiếng Việt"])

    def get_mascot_name(self):
        return CHARACTERS.get(self.current_character, {}).get("name", "Mascot")

    def get_current_y_offset(self):
        base_offset = CHARACTERS.get(self.current_character, {}).get("y_offset", 0)
        if self.current_character == "🐸 Frog" and self.state == "Sleep":
            base_offset += 10
        return base_offset

    def get_gif_filename(self, action_name):
        prefix = CHARACTERS.get(self.current_character, {}).get("prefix", "")
        filename = f"{prefix}{action_name}"
        resolved = resolve_asset_path(filename)
        if os.path.exists(resolved):
            return resolved
        return resolve_asset_path(action_name)

    def load_config(self):
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.current_character = cfg.get("character", self.current_character)
                    self.current_role = cfg.get("role", self.current_role)
                    self.current_language = cfg.get("language", self.current_language)
                    self.is_first_run = cfg.get("is_first_run", False)
            except Exception as e:
                print(f"Lỗi đọc config: {e}")

    def save_config(self):
        try:
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "character": self.current_character,
                    "role": self.current_role,
                    "language": self.current_language,
                    "is_first_run": False,
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Lỗi lưu config: {e}")

    def load_reminders_from_file(self):
        if os.path.exists(self.json_file_path):
            try:
                with open(self.json_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Lỗi đọc file JSON: {e}")
        return [
            {"text": self.get_lang()["default_reminder"], "type": "interval", "interval": 900, "duration": 6},
        ]

    def save_reminders_to_file(self):
        try:
            with open(self.json_file_path, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Lỗi lưu file JSON: {e}")

    def init_ui(self):
        if os.path.exists(str(PROJECT_ROOT / "icon.ico")):
            self.setWindowIcon(QIcon(str(PROJECT_ROOT / "icon.ico")))
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(100, 100)

        self.image_label = QLabel(self)
        self.image_label.setGeometry(0, 0, 100, 100)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.update_mascot_display()
        self.snap_to_taskbar()

    def open_setup_dialog(self):
        dialog = SetupDialog(self.current_character, self.current_role, self.current_language, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cfg = dialog.get_config()
            self.current_character = cfg['character']
            self.current_role = cfg['role']
            self.current_language = cfg['language']
            self.save_config()

            if self.chat_dialog:
                self.chat_dialog.update_ui_language()

            self.update_mascot_display()
            self.snap_to_taskbar()

    def setup_reminder_timers(self):
        for t in self.reminder_timers:
            t.stop()
            t.deleteLater()
        self.reminder_timers.clear()

        for item in self.reminders:
            if item.get('type') == 'interval':
                timer = QTimer(self)
                timer.timeout.connect(lambda i=item: self.trigger_single_reminder(i))
                timer.start(item['interval'] * 1000)
                self.reminder_timers.append(timer)

    def init_clock_checker(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.check_alarm_clock)
        self.clock_timer.start(1000)

    def check_alarm_clock(self):
        now_str = QTime.currentTime().toString("HH:mm")

        if now_str == "00:00":
            for item in self.reminders:
                if item.get('type') == 'alarm':
                    item['triggered_today'] = False

        for item in self.reminders:
            if item.get('type') == 'alarm':
                if item.get('alarm_time') == now_str and not item.get('triggered_today', False):
                    item['triggered_today'] = True
                    self.trigger_single_reminder(item)

    def trigger_single_reminder(self, item_data):
        if self.state in ["Sleep", "Falling", "Dragging"] or (self.chat_dialog and self.chat_dialog.isVisible()):
            return

        if item_data.get('type') == 'alarm':
            if self.state != "Alarm":
                self.previous_state = self.state
            self.state = "Alarm"
            self.update_mascot_display()

        bubble = SpeechBubble(item_data)
        bubble.expired.connect(self.remove_bubble)
        bubble.show()

        self.active_bubbles.insert(0, bubble)
        self.update_bubbles_positions()

    def remove_bubble(self, bubble, item_data):
        if bubble in self.active_bubbles:
            self.active_bubbles.remove(bubble)
            self.update_bubbles_positions()

        if item_data.get('type') == 'alarm' and self.state == "Alarm":
            self.state = self.previous_state if self.previous_state != "Alarm" else "Free"
            self.update_mascot_display()

    def update_bubbles_positions(self):
        current_y = self.y() - self.get_current_y_offset() - 10
        for bubble in self.active_bubbles:
            current_y -= bubble.height()
            bubble.move(self.x(), current_y)
            current_y -= 5

    def clear_all_bubbles(self):
        for b in list(self.active_bubbles):
            b.close()
            b.deleteLater()
        self.active_bubbles.clear()

    def add_custom_reminder(self, data):
        self.reminders.append(data)
        self.save_reminders_to_file()
        self.setup_reminder_timers()

    def update_custom_reminder(self, idx, data):
        if 0 <= idx < len(self.reminders):
            self.reminders[idx] = data
            self.save_reminders_to_file()
            self.setup_reminder_timers()

    def remove_custom_reminder(self, idx):
        if 0 <= idx < len(self.reminders):
            del self.reminders[idx]
            self.save_reminders_to_file()
            self.setup_reminder_timers()

    def get_current_screen_geometry(self):
        mascot_center = QPoint(self.x() + self.width() // 2, self.y() + self.height() // 2)
        for screen in QGuiApplication.screens():
            if screen.geometry().contains(mascot_center):
                return screen.availableGeometry()
        return QGuiApplication.primaryScreen().availableGeometry()

    def snap_to_taskbar(self):
        avail_geo = self.get_current_screen_geometry()
        pos_x = avail_geo.x() + avail_geo.width() - self.width() - 30
        pos_y = avail_geo.y() + avail_geo.height() - self.height() + self.get_current_y_offset()
        self.move(pos_x, pos_y)

    def init_idle_animation_timer(self):
        self.idle_anim_timer = QTimer(self)
        self.idle_anim_timer.timeout.connect(self.play_random_idle_animation)
        self.idle_anim_timer.start(20000)

    def init_movement_timer(self):
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_physics_and_movement)
        self.move_timer.start(30)

    def update_physics_and_movement(self):
        y_offset = self.get_current_y_offset()

        if self.state == "Falling":
            current_screen_geo = self.get_current_screen_geometry()
            target_y = current_screen_geo.y() + current_screen_geo.height() - self.height() + y_offset

            if self.y() + self.fall_speed >= target_y:
                self.move(self.x(), target_y)
                self.state = self.previous_state if self.previous_state != "Falling" else "Free"
                self.update_mascot_display()
            else:
                self.move(self.x(), self.y() + self.fall_speed)

        elif self.state == "Free":
            screens = QGuiApplication.screens()

            if self.allow_cross_screen:
                min_x = min(s.geometry().x() for s in screens)
                max_x = max(s.geometry().x() + s.geometry().width() for s in screens)
            else:
                curr_geo = self.get_current_screen_geometry()
                min_x = curr_geo.x()
                max_x = curr_geo.x() + curr_geo.width()

            new_x = self.x() + (self.walk_speed * self.walk_direction)

            if new_x >= max_x - self.width():
                new_x = max_x - self.width()
                self.walk_direction = -1
            elif new_x <= min_x:
                new_x = min_x
                self.walk_direction = 1

            current_target_y = self.y()
            center_x = new_x + self.width() // 2
            for screen in screens:
                s_geo = screen.geometry()
                if s_geo.x() <= center_x <= s_geo.x() + s_geo.width():
                    avail_geo = screen.availableGeometry()
                    current_target_y = avail_geo.y() + avail_geo.height() - self.height() + y_offset
                    break

            self.move(new_x, current_target_y)

        self.update_bubbles_positions()
        if self.quick_chat_bubble and self.quick_chat_bubble.isVisible():
            self.quick_chat_bubble.update_position()

        if self.chat_dialog and self.chat_dialog.isVisible():
            self.chat_dialog.update_position()

    def mousePressEvent(self, event):
        self.hide_quick_chat()
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            if self.state not in ["Dragging", "Falling"]:
                self.previous_state = self.state
            self.state = "Dragging"
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.state == "Dragging":
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())

            self.update_bubbles_positions()
            if self.chat_dialog and self.chat_dialog.isVisible():
                self.chat_dialog.update_position()

            self.old_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.state == "Dragging":
            target_state = self.previous_state if self.previous_state != "Falling" else "Free"
            current_screen_geo = self.get_current_screen_geometry()

            target_y = current_screen_geo.y() + current_screen_geo.height() - self.height() + self.get_current_y_offset()

            if abs(self.y() - target_y) <= 20:
                self.move(self.x(), target_y)
                self.state = target_state
            else:
                self.state = "Falling"

            self.update_mascot_display()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def play_random_idle_animation(self):
        if self.state == "Stay" and not self.is_playing_temp_anim:
            self.is_playing_temp_anim = True
            random_stay_gifs = ["Hiphop.gif", "Gym.gif", "HappDance.gif", "Ngao.gif"]
            chosen_action = random.choice(random_stay_gifs)
            self.load_gif_movie(self.get_gif_filename(chosen_action))
            QTimer.singleShot(5000, self.restore_main_stay_animation)

    def restore_main_stay_animation(self):
        self.is_playing_temp_anim = False
        if self.state == "Stay":
            self.load_gif_movie(self.get_gif_filename("Wave.gif"))

    def on_frame_changed(self):
        if not self.movie or not self.movie.isValid():
            return

        pixmap = self.movie.currentPixmap()
        if pixmap.isNull():
            return

        if self.state == "Free":
            if self.walk_direction == 1:
                img = pixmap.toImage().mirrored(True, False)
                pixmap = QPixmap.fromImage(img)

        self.image_label.setPixmap(pixmap)

    def load_gif_movie(self, gif_filename):
        if self.movie:
            try:
                self.movie.frameChanged.disconnect(self.on_frame_changed)
            except Exception:
                pass

        movie = QMovie(gif_filename)
        if movie.isValid():
            self.movie = movie
            self.movie.frameChanged.connect(self.on_frame_changed)
            self.image_label.setScaledContents(True)
            self.movie.start()
            self.image_label.setStyleSheet("background-color: transparent; border: none;")
        else:
            self.image_label.setMovie(None)
            self.image_label.setScaledContents(False)

            lang = self.get_lang()
            if self.state == "Sleep":
                status_icon = lang["status_sleep"]
            elif self.state == "Note":
                status_icon = lang["status_note"]
            elif self.state == "Alarm":
                status_icon = lang["status_alarm"]
            elif self.state == "Falling":
                status_icon = lang["status_falling"]
            elif self.state == "Free":
                status_icon = lang["status_free"]
            else:
                status_icon = lang["status_stay"]

            display_text = f"🐸 {self.get_mascot_name()}\n{status_icon}"
            self.image_label.setText(display_text)
            self.image_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(30, 34, 42, 230);
                    color: #ffffff;
                    font-size: 13px;
                    font-weight: bold;
                    border-radius: 20px;
                    padding: 10px;
                    border: 2px solid #61afef;
                }
            """)

    def update_mascot_display(self):
        self.is_playing_temp_anim = False

        if self.state == "Note":
            selected_action = "Note.gif"
        elif self.state == "Alarm":
            selected_action = "Alarm.gif"
        elif self.state == "Falling":
            selected_action = "Fall.gif"
        elif self.state == "Free":
            selected_action = "Run.gif"
        elif self.state == "Sleep":
            selected_action = "Sleep.gif"
        else:
            selected_action = "Wave.gif"

        self.load_gif_movie(self.get_gif_filename(selected_action))

    def contextMenuEvent(self, event):
        self.hide_quick_chat()
        lang = self.get_lang()
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #282c34;
                color: #abb2bf;
                border: 1px solid #4b5263;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item:selected {
                background-color: #61afef;
                color: #ffffff;
            }
        """)

        behavior_menu = menu.addMenu(lang["menu_behavior"])
        from PySide6.QtGui import QAction
        act_free = QAction(lang["act_free"], self)
        act_stay = QAction(lang["act_stay"], self)
        act_sleep = QAction(lang["act_sleep"], self)

        act_cross_screen = QAction(lang["act_cross_screen"], self)
        act_cross_screen.setCheckable(True)
        act_cross_screen.setChecked(self.allow_cross_screen)

        behavior_menu.addAction(act_free)
        behavior_menu.addAction(act_stay)
        behavior_menu.addAction(act_sleep)
        behavior_menu.addSeparator()
        behavior_menu.addAction(act_cross_screen)

        act_setup = QAction(lang["act_setup"], self)
        act_manage_reminders = QAction(lang["act_manage_reminders"], self)

        menu.addAction(act_setup)
        menu.addAction(act_manage_reminders)

        act_chat = QAction(lang["act_chat"], self)
        act_quit = QAction(lang["act_quit"], self)

        menu.addAction(act_chat)
        menu.addSeparator()
        menu.addAction(act_quit)

        action = menu.exec(self.mapToGlobal(event.pos()))

        if action == act_quit:
            self.clear_all_bubbles()
            if self.chat_dialog:
                self.chat_dialog.deleteLater()
            QApplication.quit()
        elif action == act_free:
            self.state = "Free"
            self.update_mascot_display()
        elif action == act_stay:
            self.state = "Stay"
            avail_geo = self.get_current_screen_geometry()
            pos_y = avail_geo.y() + avail_geo.height() - self.height() + self.get_current_y_offset()
            self.move(self.x(), pos_y)
            self.update_mascot_display()
        elif action == act_sleep:
            self.state = "Sleep"
            self.clear_all_bubbles()
            self.update_mascot_display()
            avail_geo = self.get_current_screen_geometry()
            pos_y = avail_geo.y() + avail_geo.height() - self.height() + self.get_current_y_offset()
            self.move(self.x(), pos_y)
        elif action == act_cross_screen:
            self.allow_cross_screen = act_cross_screen.isChecked()
        elif action == act_setup:
            self.open_setup_dialog()
        elif action == act_manage_reminders:
            old_state = self.state
            self.state = "Note"
            self.update_mascot_display()

            dialog = ReminderManagerDialog(self)
            dialog.exec()

            self.state = old_state
            self.update_mascot_display()
        elif action == act_chat:
            self.open_chat_dialog()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    mascot = MascotWindow()

    if mascot.is_first_run:
        setup_dialog = SetupDialog(mascot.current_character, mascot.current_role, mascot.current_language)
        if setup_dialog.exec() == QDialog.DialogCode.Accepted:
            cfg = setup_dialog.get_config()
            mascot.current_character = cfg['character']
            mascot.current_role = cfg['role']
            mascot.current_language = cfg['language']
            mascot.save_config()
            mascot.update_mascot_display()

    mascot.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
