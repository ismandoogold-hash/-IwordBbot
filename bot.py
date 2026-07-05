import os
import logging
import sys
import random
from datetime import datetime
from typing import Optional, Dict, List

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== LOGGING SETUP ====================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

# Get bot token from environment variable
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
    sys.exit(1)

logger.info("✅ Bot token loaded successfully")

# Dictionary API
DICT_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

# Cache dictionary
word_cache: Dict[str, List] = {}
CACHE_SIZE = 100

# ==================== CORE FUNCTIONS ====================

def get_cached_word(word: str) -> Optional[List]:
    """Get word from cache if available."""
    return word_cache.get(word.lower())

def cache_word(word: str, data: List) -> None:
    """Cache word data with size limit."""
    word_lower = word.lower()
    if len(word_cache) >= CACHE_SIZE:
        # Remove oldest entry
        oldest_key = next(iter(word_cache))
        del word_cache[oldest_key]
    word_cache[word_lower] = data
    logger.info(f"📚 Cached: {word} (Cache size: {len(word_cache)})")

def fetch_word_data(word: str) -> Optional[List]:
    """Fetch word data from API with error handling."""
    try:
        # Check cache first
        cached = get_cached_word(word)
        if cached:
            logger.info(f"📖 Cache hit: {word}")
            return cached

        # Fetch from API
        logger.info(f"🌐 Fetching: {word}")
        response = requests.get(f"{DICT_API_URL}{word}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            cache_word(word, data)
            return data
        elif response.status_code == 404:
            logger.warning(f"❌ Word not found: {word}")
            return None
        else:
            logger.error(f"⚠️ API error {response.status_code}: {word}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"⏰ Timeout fetching: {word}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"🚫 Request error: {e}")
        return None

def format_definition(data: List[Dict], word: str) -> str:
    """Format word data into a readable message."""
    result = f"📖 *{word.capitalize()}*\n"
    result += "═" * 30 + "\n"
    
    for entry in data:
        # Add phonetic pronunciation
        if "phonetics" in entry and entry["phonetics"]:
            phonetics = [p for p in entry["phonetics"] if "text" in p]
            if phonetics:
                result += f"🔊 {phonetics[0]['text']}\n"
        
        # Add meanings
        for meaning in entry.get("meanings", []):
            part_of_speech = meaning.get("partOfSpeech", "Unknown").capitalize()
            result += f"\n📝 *{part_of_speech}*\n"
            
            definitions = meaning.get("definitions", [])
            for idx, definition in enumerate(definitions[:3], 1):
                result += f"  {idx}. {definition.get('definition', '')}\n"
                
                if "example" in definition:
                    result += f"     📌 _Example:_ {definition['example']}\n"
    
    return result

def format_synonyms(word: str, data: List[Dict]) -> str:
    """Extract and format synonyms."""
    synonyms = []
    for entry in data:
        for meaning in entry.get("meanings", []):
            for definition in meaning.get("definitions", []):
                if "synonyms" in definition:
                    synonyms.extend(definition["synonyms"])
    
    synonyms = list(set(synonyms))[:10]
    
    if synonyms:
        result = f"🔄 *Synonyms for '{word}'*\n"
        result += "═" * 30 + "\n"
        result += "\n".join(f"• {s}" for s in synonyms)
        return result
    return f"❌ No synonyms found for '{word}'."

def format_antonyms(word: str, data: List[Dict]) -> str:
    """Extract and format antonyms."""
    antonyms = []
    for entry in data:
        for meaning in entry.get("meanings", []):
            for definition in meaning.get("definitions", []):
                if "antonyms" in definition:
                    antonyms.extend(definition["antonyms"])
    
    antonyms = list(set(antonyms))[:10]
    
    if antonyms:
        result = f"🔄 *Antonyms for '{word}'*\n"
        result += "═" * 30 + "\n"
        result += "\n".join(f"• {a}" for a in antonyms)
        return result
    return f"❌ No antonyms found for '{word}'."

def format_examples(word: str, data: List[Dict]) -> str:
    """Extract and format example sentences."""
    examples = []
    for entry in data:
        for meaning in entry.get("meanings", []):
            for definition in meaning.get("definitions", []):
                if "example" in definition:
                    examples.append(definition["example"])
    
    examples = examples[:5]
    
    if examples:
        result = f"💡 *Example sentences for '{word}'*\n"
        result += "═" * 30 + "\n"
        result += "\n".join(f"• {e}" for e in examples)
        return result
    return f"❌ No example sentences found for '{word}'."

def get_pronunciation(word: str, data: List[Dict]) -> Optional[str]:
    """Extract audio URL for pronunciation."""
    for entry in data:
        if "phonetics" in entry:
            for phonetic in entry["phonetics"]:
                if "audio" in phonetic and phonetic["audio"]:
                    return phonetic["audio"]
                if "text" in phonetic:
                    return phonetic["text"]
    return None

def get_word_of_the_day() -> str:
    """Get a word of the day from a curated list."""
    words = [
        "serendipity", "ephemeral", "eloquent", "ineffable", "paradox",
        "resilient", "tenacious", "ubiquitous", "verbose", "wistful",
        "mellifluous", "effervescent", "luminous", "ethereal", "zenith",
        "nostalgia", "euphoria", "cascade", "whimsical", "benevolent"
    ]
    day_of_year = datetime.now().timetuple().tm_yday
    return words[day_of_year % len(words)]

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    welcome_text = (
        f"👋 Hello *{user.first_name}*!\n\n"
        "📖 Welcome to *I Word Bot* - Your Live Dictionary!\n\n"
        "🔍 *Quick Start:*\n"
        "• Type any word to get its definition\n"
        "• Use commands for more features\n\n"
        "📚 *Commands:*\n"
        "• /define `<word>` - Full definition\n"
        "• /synonym `<word>` - Find synonyms\n"
        "• /antonym `<word>` - Find antonyms\n"
        "• /example `<word>` - See examples\n"
        "• /pronounce `<word>` - Hear pronunciation\n"
        "• /wordoftheday - Word of the day\n"
        "• /help - Show all commands\n"
        "• /stats - Bot statistics\n\n"
        "✨ Start typing any word now! 🚀"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Word of the Day", callback_data="word_of_day")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = (
        "📚 *I Word Bot Commands*\n\n"
        "*General Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help\n\n"
        "*Dictionary Commands:*\n"
        "/define `<word>` - Get complete definition\n"
        "/synonym `<word>` - Find synonyms\n"
        "/antonym `<word>` - Find antonyms\n"
        "/example `<word>` - See example sentences\n"
        "/pronounce `<word>` - Get pronunciation\n"
        "/wordoftheday - Get word of the day\n"
        "/stats - Bot statistics\n\n"
        "💡 *Tip:* Just type any word to get its definition instantly!\n\n"
        "🔗 *More:*\n"
        "• Word definitions include pronunciation\n"
        "• Examples help understand usage\n"
        "• Synonyms and antonyms expand vocabulary"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def define_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /define command."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a word.\n"
            "Example: `/define beautiful`",
            parse_mode="Markdown"
        )
        return
    
    word = " ".join(context.args)
    data = fetch_word_data(word)
    
    if data:
        definition = format_definition(data, word)
        await update.message.reply_text(definition, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"❌ Sorry, I couldn't find the definition for *{word}*.\n"
            "Please check the spelling and try again.",
            parse_mode="Markdown"
        )

async def synonym_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /synonym command."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a word.\n"
            "Example: `/synonym happy`",
            parse_mode="Markdown"
        )
        return
    
    word = " ".join(context.args)
    data = fetch_word_data(word)
    
    if data:
        result = format_synonyms(word, data)
        await update.message.reply_text(result, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"❌ Could not find synonyms for *{word}*.",
            parse_mode="Markdown"
        )

async def antonym_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /antonym command."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a word.\n"
            "Example: `/antonym happy`",
            parse_mode="Markdown"
        )
        return
    
    word = " ".join(context.args)
    data = fetch_word_data(word)
    
    if data:
        result = format_antonyms(word, data)
        await update.message.reply_text(result, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"❌ Could not find antonyms for *{word}*.",
            parse_mode="Markdown"
        )

async def example_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /example command."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a word.\n"
            "Example: `/example beautiful`",
            parse_mode="Markdown"
        )
        return
    
    word = " ".join(context.args)
    data = fetch_word_data(word)
    
    if data:
        result = format_examples(word, data)
        await update.message.reply_text(result, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"❌ Could not find examples for *{word}*.",
            parse_mode="Markdown"
        )

async def pronounce_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pronounce command."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a word.\n"
            "Example: `/pronounce hello`",
            parse_mode="Markdown"
        )
        return
    
    word = " ".join(context.args)
    data = fetch_word_data(word)
    
    if data:
        pronunciation = get_pronunciation(word, data)
        if pronunciation:
            if pronunciation.startswith("http"):
                await update.message.reply_audio(
                    pronunciation,
                    caption=f"🔊 Pronunciation of *{word}*",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"🔊 *{word}* - {pronunciation}",
                    parse_mode="Markdown"
                )
        else:
            await update.message.reply_text(
                f"❌ No pronunciation found for *{word}*.",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            f"❌ Could not find pronunciation for *{word}*.",
            parse_mode="Markdown"
        )

async def word_of_the_day_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /wordoftheday command."""
    word = get_word_of_the_day()
    data = fetch_word_data(word)
    
    if data:
        definition = format_definition(data, word)
        await update.message.reply_text(
            f"🌟 *Word of the Day* 🌟\n\n{definition}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Could not fetch word of the day. Please try again later."
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command."""
    stats_text = (
        "📊 *Bot Statistics*\n"
        "═" * 30 + "\n\n"
        f"📚 *Words in Cache:* {len(word_cache)}\n"
        f"🔄 *Cache Limit:* {CACHE_SIZE}\n"
        f"⏰ *Uptime:* Since deployment\n\n"
        "🔍 *Dictionary API:* FreeDictionaryAPI\n"
        "💻 *Status:* 🟢 Online\n\n"
        "📖 *Tip:* Type any word to look it up!"
    )
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages."""
    word = update.message.text.strip()
    if not word or len(word) < 2:
        await update.message.reply_text("❌ Please enter a valid word (minimum 2 characters).")
        return
    
    data = fetch_word_data(word)
    if data:
        definition = format_definition(data, word)
        await update.message.reply_text(definition, parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"❌ Sorry, I couldn't find the definition for *{word}*.\n"
            "Please check the spelling and try again, or use a different word.",
            parse_mode="Markdown"
        )

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "word_of_day":
        await word_of_the_day_command(update, context)
    elif query.data == "help":
        await help_command(update, context)
    elif query.data == "stats":
        await stats_command(update, context)
    else:
        await query.message.reply_text("❌ Unknown option.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"❌ Update {update} caused error: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred while processing your request.\n"
            "Please try again later."
        )

# ==================== MAIN FUNCTION ====================

def main() -> None:
    """Start the bot."""
    logger.info("🚀 Starting I Word Bot...")
    logger.info(f"🤖 Bot Token: {TOKEN[:15]}...")
    
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("define", define_command))
        application.add_handler(CommandHandler("synonym", synonym_command))
        application.add_handler(CommandHandler("antonym", antonym_command))
        application.add_handler(CommandHandler("example", example_command))
        application.add_handler(CommandHandler("pronounce", pronounce_command))
        application.add_handler(CommandHandler("wordoftheday", word_of_the_day_command))
        application.add_handler(CommandHandler("stats", stats_command))
        
        # Add callback query handler
        application.add_handler(CallbackQueryHandler(button_callback_handler))
        
        # Add message handler for text messages
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
        )
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Start bot with polling
        logger.info("✅ Bot started successfully! Ready to serve...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
