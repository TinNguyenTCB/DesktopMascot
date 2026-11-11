from PySide6.QtCore import QTime, QThread, Signal
from google import genai
from google.genai import types

from .data import GEMINI_API_KEY, LANGUAGES


add_reminder_tool = types.FunctionDeclaration(
    name="add_reminder",
    description="Thêm một lời nhắc hoặc báo thức mới vào danh sách dựa trên yêu cầu của người dùng.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "text": types.Schema(type=types.Type.STRING, description="Nội dung lời nhắc/báo thức."),
            "type": types.Schema(type=types.Type.STRING, description="'interval' hoặc 'alarm'."),
            "interval": types.Schema(type=types.Type.INTEGER, description="Số giây đếm ngược nếu type='interval'."),
            "alarm_time": types.Schema(type=types.Type.STRING, description="Giờ HH:mm nếu type='alarm'."),
            "duration": types.Schema(type=types.Type.INTEGER, description="Thời gian hiện (giây).")
        },
        required=["text", "type"]
    )
)

delete_reminder_tool = types.FunctionDeclaration(
    name="delete_reminder",
    description="Xóa một lời nhắc hoặc báo thức khỏi danh sách dựa trên index.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "index": types.Schema(type=types.Type.INTEGER, description="Index của lời nhắc cần xóa (từ 0).")
        },
        required=["index"]
    )
)


class GeminiWorker(QThread):
    response_received = Signal(str, dict, object)

    def __init__(self, prompt, api_key, system_instruction, reminders_list, language):
        super().__init__()
        self.prompt = prompt
        self.api_key = api_key or GEMINI_API_KEY
        self.system_instruction = system_instruction
        self.reminders_list = reminders_list
        self.language = language

    def run(self):
        try:
            client = genai.Client(api_key=self.api_key)
            current_time_str = QTime.currentTime().toString("HH:mm")

            reminders_context = ""
            for idx, item in enumerate(self.reminders_list):
                if item.get('type') == 'alarm':
                    reminders_context += f"- Index {idx}: [Alarm {item.get('alarm_time')}] \"{item.get('text')}\"\n"
                else:
                    reminders_context += f"- Index {idx}: [Interval {item.get('interval')}s] \"{item.get('text')}\"\n"

            lang_suffix = LANGUAGES.get(self.language, LANGUAGES["🇻🇳 Tiếng Việt"])["ai_prompt_suffix"]

            full_instruction = (
                f"{self.system_instruction}\n"
                f"{lang_suffix}\n"
                f"Current time: {current_time_str}.\n"
                f"Current Reminders:\n{reminders_context if reminders_context else 'None.'}\n"
                f"If user asks to set/add reminder: Call add_reminder.\n"
                f"If user asks to delete/cancel reminder: Call delete_reminder with correct Index."
            )

            config = types.GenerateContentConfig(
                system_instruction=full_instruction,
                tools=[types.Tool(function_declarations=[add_reminder_tool, delete_reminder_tool])]
            )

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=self.prompt,
                config=config
            )

            reminder_data = None
            delete_index = None
            response_text = ""

            if response.function_calls:
                for call in response.function_calls:
                    if call.name == "add_reminder":
                        args = call.args
                        reminder_data = {
                            "text": args.get("text", "Reminder"),
                            "type": args.get("type", "interval"),
                            "interval": int(args.get("interval", 10)),
                            "alarm_time": args.get("alarm_time", ""),
                            "duration": int(args.get("duration", 6)),
                            "triggered_today": False
                        }
                    elif call.name == "delete_reminder":
                        args = call.args
                        delete_index = int(args.get("index", -1))

            if response.text:
                response_text = response.text
            elif reminder_data:
                response_text = "OK!"
            elif delete_index is not None and delete_index >= 0:
                response_text = "OK!"

            self.response_received.emit(response_text, reminder_data, delete_index)
        except Exception as e:
            self.response_received.emit(f"Error: {str(e)}", None, None)
