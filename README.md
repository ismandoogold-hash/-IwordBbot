# 📖 I Word Bot - Telegram Live Dictionary

A powerful Telegram bot that provides instant word definitions, synonyms, antonyms, examples, and pronunciations.

## ✨ Features

- 📖 **Live Definitions** - Get instant word definitions
- 🔊 **Audio Pronunciation** - Hear how words are pronounced
- 🔄 **Synonyms & Antonyms** - Expand your vocabulary
- 💡 **Example Sentences** - See words in context
- 🌟 **Word of the Day** - Learn a new word daily
- 📊 **Smart Caching** - Fast response times
- 🎯 **Intuitive Interface** - Just type any word!

## 📚 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start the bot | `/start` |
| `/help` | Show help | `/help` |
| `/define <word>` | Get full definition | `/define beautiful` |
| `/synonym <word>` | Find synonyms | `/synonym happy` |
| `/antonym <word>` | Find antonyms | `/antonym happy` |
| `/example <word>` | See examples | `/example beautiful` |
| `/pronounce <word>` | Hear pronunciation | `/pronounce hello` |
| `/wordoftheday` | Word of the day | `/wordoftheday` |
| `/stats` | Bot statistics | `/stats` |

## 🚀 Deployment on Railway

### 1. Get Bot Token from Telegram
- Open Telegram
- Search for `@BotFather`
- Send: `/newbot`
- Name: `I Word Bot`
- Username: `IwordBbot`
- Copy the token you receive

### 2. Deploy on Railway
1. Fork this repository on GitHub
2. Go to [Railway.app](https://railway.app)
3. Click "Start a New Project"
4. Select "Deploy from GitHub repo"
5. Connect your GitHub account
6. Select the repository
7. Add Environment Variable:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: Your bot token from BotFather
8. Click "Deploy"

### 3. Test Your Bot
Open Telegram and send:
- `/start` to initialize
- Type `serendipity` to get definition
- `/wordoftheday` for word of the day

## 🔧 Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/IwordBbot.git
cd IwordBbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export TELEGRAM_BOT_TOKEN=your_token_here

# Run the bot
python bot.py
