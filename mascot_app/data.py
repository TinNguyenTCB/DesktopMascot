import os
from pathlib import Path

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSET_GIF_DIR = PROJECT_ROOT / "assets" / "gifs"


def resolve_asset_path(filename: str) -> str:
    candidate_paths = []
    if filename and os.path.isabs(filename):
        candidate_paths.append(filename)
    else:
        if filename:
            candidate_paths.append(PROJECT_ROOT / filename)
            candidate_paths.append(ASSET_GIF_DIR / filename)
            candidate_paths.append(PROJECT_ROOT / "assets" / "gifs" / filename)
        candidate_paths.append(PROJECT_ROOT / "Wave.gif")
    for candidate in candidate_paths:
        if candidate and os.path.exists(candidate):
            return str(candidate)
    return str(PROJECT_ROOT / "assets" / "gifs" / "Wave.gif")


LANGUAGES = {
    "🇻🇳 Tiếng Việt": {
        "title_setup": "⚙️ Cài đặt Nhân vật & Vai trò Mascot",
        "group_char": "1. Chọn Nhân vật Mascot",
        "group_role": "2. Chọn Vai trò xưng hô (AI Chat)",
        "group_lang": "3. Chọn Ngôn ngữ giao diện",
        "btn_start": "🚀 Bắt đầu Mascot",
        "title_chat": "💬 Trò chuyện với Mascot AI",
        "chat_ph": "Nhập tin nhắn...",
        "chat_send": "Gửi",
        "chat_user_label": "Bạn",
        "chat_thinking": "<i>Mascot đang suy nghĩ...</i>",
        "title_reminder_mgr": "📋 Quản lý danh sách Lời nhắc",
        "btn_add": "➕ Thêm mới",
        "btn_edit": "✏️ Sửa",
        "btn_delete": "🗑️ Xóa",
        "btn_close": "Đóng",
        "title_reminder_edit": "⚙️ Cài đặt Lời nhắc / Báo thức",
        "lbl_content": "Lời nhắc:",
        "lbl_type": "Loại nhắc nhở:",
        "lbl_interval": "Chu kỳ lặp:",
        "lbl_alarm_time": "Mốc giờ báo thức:",
        "lbl_duration": "Thời gian hiện:",
        "type_interval": "⏱️ Theo chu kỳ lặp",
        "type_alarm": "⏰ Báo thức giờ cố định",
        "unit_sec": " giây",
        "unit_min": " phút",
        "unit_hour": " giờ",
        "btn_save": "Lưu",
        "btn_cancel": "Hủy",
        "menu_behavior": "🎭 Hành vi",
        "act_free": "🐾 Hoạt động tự do (Chạy)",
        "act_stay": "🧘 Ngồi yên ngoan ngoãn",
        "act_sleep": "💤 Đi ngủ (Zzz)",
        "act_cross_screen": "🌐 Chạy sang màn hình khác",
        "act_setup": "⚙️ Cài đặt Nhân vật & Ngôn ngữ...",
        "act_manage_reminders": "⏰ Quản lý Lời nhắc...",
        "act_chat": "💬 Hỏi đáp / Trò chuyện",
        "act_quit": "❌ Thoát Mascot",
        "status_sleep": "💤 [Đi ngủ]",
        "status_note": "📝 [Ghi chú...]",
        "status_alarm": "⏰ [BÁO THỨC!]",
        "status_falling": "🪂 [Đang rơi...]",
        "status_free": "🐾 [Chạy tự do]",
        "status_stay": "✨ [Ngồi yên]",
        "default_reminder": "Uống nước thôi iu ơi!",
        "ai_prompt_suffix": "Hãy trả lời bằng Tiếng Việt ngắn gọn (dưới 3 câu).",
        "lbl_repeat_prefix": "Lặp:",
        "lbl_duration_prefix": "Kéo dài:",
        "lbl_alarm_prefix": "Báo thức:",
        "quick_chat_btn": "💬 Chat"
    },
    "🇯🇵 日本語": {
        "title_setup": "⚙️ キャラクターと役割の設定",
        "group_char": "1. マスコットキャラクターの選択",
        "group_role": "2. AIチャットの役割・呼び方",
        "group_lang": "3. 表示言語の選択",
        "btn_start": "🚀 マスコットを起動",
        "title_chat": "💬 AIマスコットとおしゃべり",
        "chat_ph": "メッセージを入力...",
        "chat_send": "送信",
        "chat_user_label": "あなた",
        "chat_thinking": "<i>マスコットが考え中...</i>",
        "title_reminder_mgr": "📋 リマインダー管理",
        "btn_add": "➕ 新規追加",
        "btn_edit": "✏️ 編集",
        "btn_delete": "🗑️ 削除",
        "btn_close": "閉じる",
        "title_reminder_edit": "⚙️ リマインダー／アラーム設定",
        "lbl_content": "リマインダー:",
        "lbl_type": "通知タイプ:",
        "lbl_interval": "繰り返し間隔:",
        "lbl_alarm_time": "アラーム時刻:",
        "lbl_duration": "表示時間:",
        "type_interval": "⏱️ 繰り返し通知",
        "type_alarm": "⏰ 指定時刻アラーム",
        "unit_sec": "秒",
        "unit_min": "分",
        "unit_hour": "時間",
        "btn_save": "保存",
        "btn_cancel": "キャンセル",
        "menu_behavior": "🎭 アクション",
        "act_free": "🐾 自由に動き回る",
        "act_stay": "🧘 おとなしく待機",
        "act_sleep": "💤 睡眠モード (Zzz)",
        "act_cross_screen": "🌐 画面間を移動する",
        "act_setup": "⚙️ キャラクター・言語設定...",
        "act_manage_reminders": "⏰ リマインダー管理...",
        "act_chat": "💬 チャットでおしゃべり",
        "act_quit": "❌ マスコットを終了",
        "status_sleep": "💤 [睡眠中]",
        "status_note": "📝 [メモ中...]",
        "status_alarm": "⏰ [アラーム!]",
        "status_falling": "🪂 [落下中...]",
        "status_free": "🐾 [自由移動]",
        "status_stay": "✨ [待機中]",
        "default_reminder": "お水を飲んでね！",
        "ai_prompt_suffix": "日本語で簡潔に（3文 family/friendly 以内）答えてください。",
        "lbl_repeat_prefix": "繰り返し:",
        "lbl_duration_prefix": "表示:",
        "lbl_alarm_prefix": "アラーム:",
        "quick_chat_btn": "💬 チャット"
    }
}

ROLES = {
    "💕 Người yêu (Em - Iu) / 恋人 (彼女)": "Bạn là người yêu đáng yêu, ngọt ngào của người dùng. Hãy xưng 'em' và gọi người dùng là 'iu'. / ユーザーの可愛い恋人（彼女）になりきり, 親しみやすく甘い口調で答えてください。",
    "💕 Người yêu 2 (Anh - Iu) / 恋人 (彼氏)": "Bạn là người yêu hiền lành, chiều chuộng của người dùng. Hãy xưng 'anh' và gọi người dùng là 'iu'. / ユーザーの優しい恋人（彼氏）になりきり, 優しく包み込む口調で答えてください。",
    "💼 Trợ lý nghiêm túc (Em - Anh/Chị) / 秘書 (敬語)": "Bạn là một trợ lý AI chuyên nghiệp, lịch sự. Hãy xưng 'em' và gọi người dùng là 'anh/chị'. / 礼儀正しくプロフェッショナルなAIアシスタントとして丁寧な敬語で答えてください。"
}

CHARACTERS = {
    "🦈 Sharkun": {
        "prefix": "",
        "name": "Sharkun",
        "preview_gif": "Gym.gif",
        "y_offset": 0
    },
    "🐳 Whaly": {
        "prefix": "W_",
        "name": "Whale",
        "preview_gif": "W_Gym.gif",
        "y_offset": 0
    },
    "🐟 Pinkun": {
        "prefix": "P_",
        "name": "Pinkun",
        "preview_gif": "P_Gym.gif",
        "y_offset": 0
    },
    "🐸 Frog": {
        "prefix": "F_",
        "name": "Froggy",
        "preview_gif": "F_Gym.gif",
        "y_offset": 8
    }
}
