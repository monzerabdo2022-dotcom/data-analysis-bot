import json
import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'questions.json'), 'r', encoding='utf-8') as f:
    QUESTIONS = json.load(f)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8818213009:AAE0A7q_LB-sD9rFIKjcvnwdfygMTeexx7U")

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("العربية", callback_data='lang_ar')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Please choose your language:\nمرحباً! الرجاء اختيار لغتك:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_states:
        user_states[user_id] = {'lang': 'en', 'topic': None, 'difficulty': None, 'q_index': 0}
    data = query.data
    if data.startswith('lang_'):
        user_states[user_id]['lang'] = data.split('_')[1]
        await send_topic_selection(query, user_id)
    elif data.startswith('topic_'):
        user_states[user_id]['topic'] = data.split('_')[1]
        user_states[user_id]['q_index'] = 0
        await send_difficulty_selection(query, user_id)
    elif data.startswith('diff_'):
        user_states[user_id]['difficulty'] = data.split('_')[1]
        user_states[user_id]['q_index'] = 0
        await send_question(query, user_id)
    elif data == 'show_answer':
        await show_answer(query, user_id)
    elif data == 'next_question':
        user_states[user_id]['q_index'] += 1
        await send_question(query, user_id)
    elif data == 'prev_question':
        user_states[user_id]['q_index'] = max(0, user_states[user_id]['q_index'] - 1)
        await send_question(query, user_id)
    elif data == 'back_to_topics':
        user_states[user_id]['topic'] = None
        user_states[user_id]['difficulty'] = None
        user_states[user_id]['q_index'] = 0
        await send_topic_selection(query, user_id)
    elif data == 'back_to_difficulty':
        user_states[user_id]['difficulty'] = None
        user_states[user_id]['q_index'] = 0
        await send_difficulty_selection(query, user_id)

async def send_topic_selection(query, user_id):
    lang = user_states[user_id]['lang']
    text = "Please choose a topic:" if lang == 'en' else "الرجاء اختيار الموضوع:"
    topics = QUESTIONS[lang].keys()
    keyboard = [[InlineKeyboardButton(topic, callback_data=f'topic_{topic}')] for topic in topics]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def send_difficulty_selection(query, user_id):
    lang = user_states[user_id]['lang']
    topic = user_states[user_id]['topic']
    text = f"Choose difficulty for {topic}:" if lang == 'en' else f"اختر مستوى الصعوبة لـ {topic}:"
    difficulties = QUESTIONS[lang][topic].keys()
    keyboard = [[InlineKeyboardButton(diff, callback_data=f'diff_{diff}')] for diff in difficulties]
    keyboard.append([InlineKeyboardButton("🔙 Back" if lang == 'en' else "🔙 رجوع", callback_data='back_to_topics')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def send_question(query, user_id):
    lang = user_states[user_id]['lang']
    topic = user_states[user_id]['topic']
    difficulty = user_states[user_id]['difficulty']
    q_index = user_states[user_id]['q_index']
    questions_list = QUESTIONS[lang][topic][difficulty]
    if not questions_list:
        text = "No questions available." if lang == 'en' else "لا توجد أسئلة متاحة."
        keyboard = [[InlineKeyboardButton("🔙 Back" if lang == 'en' else "🔙 رجوع", callback_data='back_to_difficulty')]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if q_index >= len(questions_list):
        user_states[user_id]['q_index'] = 0
        q_index = 0
    question_data = questions_list[q_index]
    question_text = question_data['question']
    text = f"📌 {topic} | {difficulty}\n\n❓ Question {q_index + 1}/{len(questions_list)}:\n\n{question_text}" if lang == 'en' else \
           f"📌 {topic} | {difficulty}\n\n❓ سؤال {q_index + 1}/{len(questions_list)}:\n\n{question_text}"
    keyboard = [
        [InlineKeyboardButton("💡 Show Answer" if lang == 'en' else "💡 الإجابة", callback_data='show_answer')],
        [InlineKeyboardButton("⬅️", callback_data='prev_question'),
         InlineKeyboardButton("➡️", callback_data='next_question')],
        [InlineKeyboardButton("🔙 Difficulty" if lang == 'en' else "🔙 المستوى", callback_data='back_to_difficulty'),
         InlineKeyboardButton("🏠 Topics" if lang == 'en' else "🏠 المواضيع", callback_data='back_to_topics')]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_answer(query, user_id):
    lang = user_states[user_id]['lang']
    topic = user_states[user_id]['topic']
    difficulty = user_states[user_id]['difficulty']
    q_index = user_states[user_id]['q_index']
    question_data = QUESTIONS[lang][topic][difficulty][q_index]
    question_text = question_data['question']
    answer_text = question_data['answer']
    text = f"📌 {topic} | {difficulty}\n\n❓ Question {q_index + 1}/{len(QUESTIONS[lang][topic][difficulty])}:\n\n{question_text}\n\n✅ Answer:\n\n{answer_text}" if lang == 'en' else \
           f"📌 {topic} | {difficulty}\n\n❓ سؤال {q_index + 1}/{len(QUESTIONS[lang][topic][difficulty])}:\n\n{question_text}\n\n✅ الإجابة:\n\n{answer_text}"
    keyboard = [
        [InlineKeyboardButton("⬅️", callback_data='prev_question'),
         InlineKeyboardButton("➡️", callback_data='next_question')],
        [InlineKeyboardButton("🔙 Difficulty" if lang == 'en' else "🔙 المستوى", callback_data='back_to_difficulty'),
         InlineKeyboardButton("🏠 Topics" if lang == 'en' else "🏠 المواضيع", callback_data='back_to_topics')]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

def main() -> None:
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .http_version("1.1")
        .get_updates_http_version("1.1")
        .read_timeout(60)
        .write_timeout(60)
        .connect_timeout(60)
        .pool_timeout(60)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    print("Bot is running...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=1.0,
        timeout=30
    )

if __name__ == '__main__':
    main()
