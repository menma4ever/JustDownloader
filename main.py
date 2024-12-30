import yt_dlp as youtube_dl
import requests
import os
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import re
from datetime import datetime
from keep_alive import keep_alive

keep_alive()

# Format the date
def format_date(date_str):
    try:
        # Parse the date string and format it as DD/MM/YYYY
        return datetime.strptime(date_str, '%Y%m%d').strftime('%d/%m/%Y')
    except ValueError:
        # Return the original date if it doesn't match the expected format
        return date_str

# Function to validate nickname
def is_valid_nickname(nickname):
    # Check if the nickname is at most 30 characters
    if len(nickname) > 30:
        return "❌ Nickname must be at most 30 characters long."
    
    # Check if the nickname starts with a lowercase letter
    if not nickname[0].isalpha() or not nickname[0].islower():
        return "❌ Nickname must start with a lowercase alphabet letter."
    
    # Check if the nickname contains only lowercase letters and numbers
    if not re.match("^[a-z0-9]+$", nickname):
        return "❌ Nickname can only contain lowercase letters and numbers, with no spaces or symbols."
    
    return True

# Function to handle nickname registration
async def register_nickname(update: Update, context):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    # Register nickname only if user is new
    if user_id not in user_data or user_data[user_id]["nickname"] is None:
        nickname = update.message.text.strip()
        validation_result = is_valid_nickname(nickname)
        
        if validation_result is not True:
            # If the validation fails, send an error message
            await update.message.reply_text(validation_result)
            return
        
        # Check if nickname already exists
        if nickname in [user["nickname"] for user in user_data.values()]:
            await update.message.reply_text(f'❌ Sorry, the nickname "{nickname}" is already taken. Please choose another one.')
        else:
            user_data[user_id] = {"nickname": nickname, "is_premium": False, "download_count": 0, "last_download_date": None}
            save_user_data(user_data)
            await update.message.reply_text(f'✅ Thank you, {nickname}! You are now registered. Send me a YouTube link to download.')
    else:
        # If the user already has a nickname, handle the video URL
        await handle_video_request(update, context)

# Set your path to ffmpeg here
FFMPEG_PATH = 'C:/ffmpeg/bin/ffmpeg.exe'  # Adjust this path according to where ffmpeg is installed on your system

# Initialize the JSON database if it doesn't exist
DATABASE_PATH = 'users.json'

if not os.path.exists(DATABASE_PATH):
    with open(DATABASE_PATH, 'w') as db_file:
        json.dump({}, db_file)

# Function to load user data from the JSON database
def load_user_data():
    with open(DATABASE_PATH, 'r') as db_file:
        return json.load(db_file)

# Function to save user data to the JSON database with better formatting
def save_user_data(data):
    with open(DATABASE_PATH, 'w') as db_file:
        json.dump(data, db_file, indent=4, sort_keys=True)

# Example of ensuring clean structure when adding a new user
def add_user(user_id, nickname, is_premium=False):
    user_data = load_user_data()
    
    # Ensure the user_id exists and has the correct structure
    if user_id not in user_data:
        user_data[user_id] = {
            "nickname": nickname,
            "is_premium": is_premium,
            "download_count": 0,
            "last_download_date": None
        }
    save_user_data(user_data)

# Function to download the video in the chosen resolution
async def download_video(update: Update, context):
    query = update.callback_query
    data = query.data.split('_')
    resolution_or_format = data[1] if len(data) > 1 else data[0]
    url = context.user_data.get('url')
    
    if not url:
        await query.message.reply_text('❌ Error: No URL found. Please try again.')
        return

    ydl_opts = {
        'ffmpeg_location': FFMPEG_PATH,  # Path to ffmpeg
    }

    if resolution_or_format == 'mp3':
        ydl_opts.update({
            'format': 'worstvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',  # Lowest resolution
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}
            ],
        })
    else:
        ydl_opts.update({
            'format': f'bestvideo[height<={resolution_or_format}]+bestaudio[ext=m4a]/mp4'
        })

    try:
        await query.answer()
        downloading_message = await query.message.reply_text(text=f'⚙️ Processing {resolution_or_format}...')

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict)

        if resolution_or_format == 'mp3':
            file_name = file_name.replace('.webm', '.mp3').replace('.mp4', '.mp3')

        if resolution_or_format == 'mp3':
            await query.message.reply_audio(audio=open(file_name, 'rb'), title=info_dict.get('title', 'Audio'))
        else:
            await query.message.reply_video(video=open(file_name, 'rb'))

        os.remove(file_name)
        await query.message.reply_text('✅ Download complete and sent!')

        resolution_message_id = context.user_data.get('resolution_message_id')
        if resolution_message_id:
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=resolution_message_id)

        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=downloading_message.message_id)

    except Exception as e:
        await query.message.reply_text(f"❌ Error during processing: {str(e)}")

# Define a function to start the bot
async def start(update: Update, context):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    if user_id not in user_data or user_data[user_id]["nickname"] is None:
        # New user or user without a nickname
        await update.message.reply_text('👋 Hello! Please enter your nickname to register:')
    else:
        # Existing user with a nickname, prompt for URL directly
        await update.message.reply_text('👋 Welcome back! Send me a YouTube link to download.')

# Function to handle video URL input (for registered users)
async def handle_video_request(update: Update, context):
    url = update.message.text
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    if user_id not in user_data or user_data[user_id]["nickname"] is None:
        await update.message.reply_text('❌ Please register first by sending a nickname using /start.')
        return

    user = user_data[user_id]
    is_premium, download_count, last_download_date = user["is_premium"], user["download_count"], user["last_download_date"]

    if not is_premium and download_count >= 3:
        await update.message.reply_text('Sorry, you have reached your daily limit of 3 downloads. Upgrade to premium for unlimited downloads! If you want a premium subscription, connect with @enemyofeternity.')
        return

    # Restrict TikTok and Instagram to premium users
    if 'tiktok' in url or 'instagram' in url:
        if not is_premium:
            await update.message.reply_text('❌ Sorry, only premium users can download from TikTok or Instagram. For premium requests, contact @enemyofeternity.')
            return

    ydl_opts = {
        'noplaylist': True,  # Ensuring playlist downloading is disabled
        'ffmpeg_location': FFMPEG_PATH,  # Add the path to ffmpeg here
        # Removed proxy setting here
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            if 'entries' in info_dict:
                if not is_premium:
                    await update.message.reply_text('Sorry, downloading playlists is not supported. For questions and premium requests, please contact @enemyofeternity.')
                    return

            if info_dict.get('is_live', False):
                if not is_premium:
                    await update.message.reply_text('Sorry, only premium users can download live streams. For questions and premium requests, please contact @enemyofeternity.')
                    return

            context.user_data['url'] = url

            formats = info_dict.get('formats', [])
            thumbnail_url = info_dict.get('thumbnail', '')
            resolutions = set()
            for f in formats:
                if 'height' in f and f['height'] is not None and 'ext' in f:
                    resolutions.add(f['height'])

            filtered_resolutions = {r for r in resolutions if r >= 360}

            buttons = []
            for r in sorted(filtered_resolutions):
                # Use emojis based on resolution size
                if r <= 360:
                    emoji = '🔺'# Smallest
                elif r <= 480:
                    emoji = '🔻'# Slightly bigger
                elif r <= 720:
                    emoji = '🔸'# Medium resolution
                elif r <= 1080:
                    emoji = '🔹'# Larger resolution
                elif r <= 1440:
                    emoji = '🔶'# Even larger resolution
                elif r <= 2160:
                    emoji = '🔷' # High resolution
                else:
                    emoji = '🟥' # Highest resolution
                
                buttons.append([InlineKeyboardButton(f'{emoji} {r}p', callback_data=f'resolution_{r}')])

            buttons.append([InlineKeyboardButton('🎵 MP3', callback_data='mp3')])

            video_name = info_dict.get('title', 'Unknown Video')
            views = info_dict.get('view_count', 'Unknown')
            likes = info_dict.get('like_count', 'Unknown')
            upload_date = info_dict.get('upload_date', 'Unknown')
            author = info_dict.get('uploader', 'Unknown')
            duration = info_dict.get('duration', 'Unknown')

            # Update video_info with formatted date
            video_info = (f"{video_name}\n"
                        f"📊 Views: {views}\n"
                        f"❤️ Likes: {likes}\n"
                        f"⬆️ Uploaded on: {format_date(upload_date)}\n"
                        f"🖋 Author: {author}\n"
                        f"⏳ Duration: {duration}s\n"
                        f'🎦 Choose the resolution or format:')

            if thumbnail_url:
                thumbnail_response = requests.get(thumbnail_url)
                thumbnail_file = os.path.join('thumbnail.jpg')
                with open(thumbnail_file, 'wb') as f:
                    f.write(thumbnail_response.content)

                resolution_message = await update.message.reply_photo(photo=open(thumbnail_file, 'rb'), caption=video_info, reply_markup=InlineKeyboardMarkup(buttons))
                os.remove(thumbnail_file)
            else:
                resolution_message = await update.message.reply_text(video_info, reply_markup=InlineKeyboardMarkup(buttons))

            context.user_data['resolution_message_id'] = resolution_message.message_id

    except youtube_dl.utils.DownloadError:
        await update.message.reply_text('❌ This video might be unavailable in your country.❌')
    except Exception as e:
        await update.message.reply_text(f'❌ Error: {str(e)}')

# Main function to run the bot
def main():
    app = ApplicationBuilder().token('7647197927:AAGg2XI6KA33RlrXMlnyTqkN2XGx_PltTyw').build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register_nickname))  # Handle nickname registration
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_request))  # Handle video URL input
    app.add_handler(CallbackQueryHandler(download_video))  # Handle download options

    app.run_polling()

if __name__ == '__main__':
    main()
