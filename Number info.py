# bot.py
import requests
import re
import telebot
import json
import sqlite3
import time
from datetime import datetime

# Configuration
BOT_TOKEN = "7998706457:AAGmJfDTYwNacp2NDaPRJ7vrQOntboR2kFM"
API_BASE = "https://shadow-x-osint.vercel.app/api?key=Shadow&type=mobile&term="
ADMIN_ID = 1614927658

# Blocked numbers - inko search karne par realistic error milega
BLOCKED_NUMBERS = ["9335073755", "9120424900", "9794584222", "8299500285"]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# Database setup for user management
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, 
                  last_name TEXT, joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users 
                 (user_id, username, first_name, last_name) 
                 VALUES (?, ?, ?, ?)''',
              (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT user_id, username, first_name, last_name, joined_date 
                 FROM users ORDER BY joined_date DESC''')
    users = c.fetchall()
    conn.close()
    return users

def get_user_count():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT COUNT(*) FROM users''')
    count = c.fetchone()[0]
    conn.close()
    return count

init_db()

def extract_phone(text):
    """Extract 10 digit phone number from text"""
    if not text:
        return None
    m = re.search(r'(\d{10})', text)
    return m.group(1) if m else None

def format_address(address):
    """Format address by replacing ! with new lines"""
    if not address:
        return "N/A"
    formatted = address.replace('!!', '\n').replace('!', '\n')
    return formatted

def create_realistic_error(number):
    """Create realistic error messages for blocked numbers or API errors"""
    error_messages = [
        f"📭 <b>Data Not Available</b>\n\n📱 Number: <code>{number}</code>\n\n⚡ <b>Query Status:</b> Completed\n📈 <b>Records Found:</b> 0\n<i>This number is not available in our database</i>",
        f"❌ <b>Database Query Failed</b>\n\n📱 Number: <code>{number}</code>\n\n🔍 <b>Status:</b> No records found in telecom database\n💡 <i>This number might be unregistered or recently activated</i>",
        f"🚫 <b>Information Unavailable</b>\n\n📱 Number: <code>{number}</code>\n\n⚠️ <b>Reason:</b> Number not found in subscriber database\n🔒 <i>Data privacy restrictions may apply</i>",
        f"🔍 <b>Search Results Empty</b>\n\n📱 Number: <code>{number}</code>\n\n📊 <b>Database Status:</b> No matching records\n🌐 <i>Try again later or check the number format</i>",
        f"🔒 <b>Access Restricted</b>\n\n📱 Number: <code>{number}</code>\n\n🚫 <b>Error Code:</b> DB_404\n📡 <i>Telecom operator data not accessible for this number</i>",
        f"🌐 <b>Network Error</b>\n\n📱 Number: <code>{number}</code>\n\n⚡ <b>Query Status:</b> Failed\n🔍 <b>Reason:</b> Number registry not found\n<i>Please verify the number and try again</i>"
    ]
    import random
    return random.choice(error_messages)

def create_mono_formatted_response(data):
    """Create beautifully formatted response with mono effect for ALL data"""
    if not data or len(data) == 0:
        return "❌ No data found for this number"
    
    formatted_text = "<pre>\n"
    formatted_text += "┌─────────────────────────────────────────────────────┐\n"
    formatted_text += "│               📱 NUMBER INFORMATION                 │\n"
    formatted_text += "└─────────────────────────────────────────────────────┘\n\n"
    
    # Process all records
    for idx, record in enumerate(data, 1):
        if len(data) > 1:
            formatted_text += f"📋 RECORD #{idx}\n"
            formatted_text += "────────────────────────────\n"
        
        # All fields from API - handle different field names
        formatted_text += f"📞 <b>Mobile Number:</b> {record.get('mobile', record.get('number', 'N/A'))}\n"
        formatted_text += f"👤 <b>Name:</b> {record.get('name', 'N/A')}\n"
        formatted_text += f"👨‍👦 <b>Father's Name:</b> {record.get('fname', record.get('father_name', 'N/A'))}\n"
        
        # Handle address formatting
        address = record.get('address', 'N/A')
        if address and address != 'N/A':
            formatted_text += f"📍 <b>Address:</b>\n{format_address(address)}\n"
        else:
            formatted_text += f"📍 <b>Address:</b> N/A\n"
            
        formatted_text += f"📱 <b>Alternate Number:</b> {record.get('alt', record.get('alternate_number', 'N/A'))}\n"
        formatted_text += f"🏢 <b>Circle:</b> {record.get('circle', 'N/A')}\n"
        formatted_text += f"🆔 <b>ID:</b> {record.get('id', 'N/A')}\n"
        
        # Additional fields that might be in API response
        if 'operator' in record:
            formatted_text += f"📡 <b>Operator:</b> {record.get('operator', 'N/A')}\n"
        if 'email' in record:
            formatted_text += f"📧 <b>Email:</b> {record.get('email', 'N/A')}\n"
        if 'dob' in record:
            formatted_text += f"🎂 <b>Date of Birth:</b> {record.get('dob', 'N/A')}\n"
        if 'gender' in record:
            formatted_text += f"⚧️ <b>Gender:</b> {record.get('gender', 'N/A')}\n"
        if 'network' in record:
            formatted_text += f"🌐 <b>Network:</b> {record.get('network', 'N/A')}\n"
        if 'state' in record:
            formatted_text += f"🏛️ <b>State:</b> {record.get('state', 'N/A')}\n"
        if 'pincode' in record:
            formatted_text += f"📮 <b>Pincode:</b> {record.get('pincode', 'N/A')}\n"
        if 'country' in record:
            formatted_text += f"🌍 <b>Country:</b> {record.get('country', 'N/A')}\n"
        if 'provider' in record:
            formatted_text += f"🏢 <b>Provider:</b> {record.get('provider', 'N/A')}\n"
        if 'location' in record:
            formatted_text += f"🗺️ <b>Location:</b> {record.get('location', 'N/A')}\n"
        
        formatted_text += "\n"
    
    formatted_text += "┌─────────────────────────────────────────────────────┐\n"
    formatted_text += "│        🔒 INFORMATION RETRIEVED SUCCESSFULLY         │\n"
    formatted_text += "└─────────────────────────────────────────────────────┘\n"
    formatted_text += "</pre>"
    
    # Add Techno Beats branding
    formatted_text += "\n\n🔰 <b>Powered by Techno Beats</b>\n"
    formatted_text += "👨‍💻 <i>Created by</i> @Techno_beats"
    
    return formatted_text

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Save user to database
    save_user(message.from_user.id, 
              message.from_user.username, 
              message.from_user.first_name, 
              message.from_user.last_name)
    
    welcome_text = """
🔰 <b>Techno Beats - Number Information Bot</b>

📱 <i>Send me any 10-digit mobile number to get complete information</i>

<b>Example:</b> <code>9305562389</code>

🔍 <b>All Details Included:</b>
• Mobile Number & Alternate Number
• Name & Father's Name  
• Complete Address with Pincode
• Telecom Circle & Operator
• ID and all other available information

⚡ <b>Powered by Techno Beats</b>
👨‍💻 <i>Created by</i> @Techno_beats
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Unauthorized. Only admin can use this command.")
        return
    
    # Extract broadcast message from command
    broadcast_text = message.text.replace('/broadcast', '').strip()
    if not broadcast_text:
        bot.reply_to(message, "❌ Please provide a message to broadcast.\nUsage: /broadcast Your message here")
        return
    
    users = get_all_users()
    total_users = len(users)
    success_count = 0
    fail_count = 0
    
    status_msg = bot.reply_to(message, f"📢 Starting broadcast to {total_users} users...")
    
    for user in users:
        try:
            user_id = user[0]
            bot.send_message(user_id, f"📢 <b>Announcement from Techno Beats:</b>\n\n{broadcast_text}\n\n🔰 <b>Techno Beats</b>\n👨‍💻 @Techno_beats")
            success_count += 1
            time.sleep(0.5)  # Avoid hitting rate limits
        except Exception as e:
            fail_count += 1
            print(f"Failed to send to user {user_id}: {e}")
    
    bot.edit_message_text(
        chat_id=status_msg.chat.id,
        message_id=status_msg.message_id,
        text=f"✅ <b>Broadcast Completed</b>\n\n📊 <b>Statistics:</b>\n• Total Users: {total_users}\n• Successful: {success_count}\n• Failed: {fail_count}\n\n🔰 <b>Techno Beats</b>"
    )

@bot.message_handler(commands=['users'])
def show_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Unauthorized. Only admin can use this command.")
        return
    
    users = get_all_users()
    total_users = get_user_count()
    
    if total_users == 0:
        bot.reply_to(message, "📊 <b>User Statistics:</b>\n• Total Users: 0\n\n🔰 <b>Techno Beats</b>")
        return
    
    user_list = "📊 <b>User List</b>\n\n"
    user_list += f"• <b>Total Users:</b> {total_users}\n\n"
    
    for idx, user in enumerate(users[:50], 1):  # Show first 50 users
        user_id, username, first_name, last_name, joined_date = user
        name = f"{first_name or ''} {last_name or ''}".strip()
        if not name:
            name = "No Name"
        
        user_list += f"{idx}. {name}"
        if username:
            user_list += f" (@{username})"
        user_list += f" - ID: {user_id}\n"
    
    if total_users > 50:
        user_list += f"\n... and {total_users - 50} more users"
    
    user_list += "\n\n🔰 <b>Techno Beats</b>"
    
    bot.reply_to(message, user_list)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Unauthorized. Only admin can use this command.")
        return
    
    total_users = get_user_count()
    bot.reply_to(message, 
                 f"📈 <b>Bot Statistics</b>\n\n"
                 f"👥 <b>Total Users:</b> {total_users}\n"
                 f"📅 <b>Last Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                 f"🔰 <b>Techno Beats</b>")

@bot.message_handler(func=lambda message: True)
def handle_number_query(message):
    # Save user to database
    save_user(message.from_user.id, 
              message.from_user.username, 
              message.from_user.first_name, 
              message.from_user.last_name)
    
    text = message.text.strip()
    
    # Check if it's a command
    if text.startswith('/'):
        return
    
    number = extract_phone(text)
    
    if not number:
        bot.reply_to(message, 
            "❌ <b>Invalid Format</b>\n\n"
            "Please send a valid 10-digit mobile number.\n"
            "<b>Example:</b> <code>9305562389</code>\n\n"
            "🔰 <b>Techno Beats</b>"
        )
        return
    
    # Check if number is blocked
    if number in BLOCKED_NUMBERS:
        error_msg = create_realistic_error(number)
        bot.reply_to(message, error_msg)
        return
    
    # Show processing message
    processing_msg = bot.reply_to(message, 
        f"🔍 <b>Searching for complete information...</b>\n"
        f"📱 Number: <code>{number}</code>\n"
        f"⏳ Please wait while we fetch all details...\n\n"
        f"🔰 <b>Techno Beats</b>"
    )
    
    try:
        # Call the new API
        api_url = f"{API_BASE}{number}"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if API returned successful data
            if data and isinstance(data, list) and len(data) > 0:
                # Check if first item has actual data or is empty
                first_item = data[0]
                if any(value for key, value in first_item.items() if key != 'number' and value):
                    # Format the response with ALL data
                    formatted_result = create_mono_formatted_response(data)
                    
                    # Check if message is too long for Telegram
                    if len(formatted_result) > 4096:
                        # Split into multiple messages or send as file
                        bot.edit_message_text(
                            chat_id=processing_msg.chat.id,
                            message_id=processing_msg.message_id,
                            text="📁 <b>Data too large, sending as file...</b>\n\n🔰 <b>Techno Beats</b>"
                        )
                        
                        # Send as text file
                        filename = f"number_info_{number}.txt"
                        with open(filename, 'w', encoding='utf-8') as f:
                            # Create plain text version without HTML tags
                            plain_text = formatted_result.replace('<pre>', '').replace('</pre>', '').replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
                            f.write(plain_text)
                        
                        with open(filename, 'rb') as f:
                            bot.send_document(
                                chat_id=message.chat.id,
                                document=f,
                                caption=f"📄 Complete information for: {number}\n\n🔰 <b>Techno Beats</b>\n👨‍💻 <i>Created by</i> @Techno_beats"
                            )
                    else:
                        bot.edit_message_text(
                            chat_id=processing_msg.chat.id,
                            message_id=processing_msg.message_id,
                            text=formatted_result
                        )
                else:
                    # API returned empty data structure
                    error_msg = create_realistic_error(number)
                    bot.edit_message_text(
                        chat_id=processing_msg.chat.id,
                        message_id=processing_msg.message_id,
                        text=error_msg
                    )
            else:
                # No data found - show realistic error
                error_msg = create_realistic_error(number)
                bot.edit_message_text(
                    chat_id=processing_msg.chat.id,
                    message_id=processing_msg.message_id,
                    text=error_msg
                )
                
        else:
            bot.edit_message_text(
                chat_id=processing_msg.chat.id,
                message_id=processing_msg.message_id,
                text=f"❌ <b>API Error</b>\n\nStatus Code: {response.status_code}\nResponse: {response.text}\nPlease try again later.\n\n🔰 <b>Techno Beats</b>"
            )
            
    except requests.exceptions.Timeout:
        bot.edit_message_text(
            chat_id=processing_msg.chat.id,
            message_id=processing_msg.message_id,
            text=f"❌ <b>Request Timeout</b>\n\nServer is taking too long to respond. Please try again.\n\n🔰 <b>Techno Beats</b>"
        )
        
    except requests.exceptions.RequestException as e:
        bot.edit_message_text(
            chat_id=processing_msg.chat.id,
            message_id=processing_msg.message_id,
            text=f"❌ <b>Connection Error</b>\n\n{str(e)}\n\n🔰 <b>Techno Beats</b>"
        )
        
    except Exception as e:
        bot.edit_message_text(
            chat_id=processing_msg.chat.id,
            message_id=processing_msg.message_id,
            text=f"❌ <b>Unexpected Error</b>\n\n{str(e)}\n\n🔰 <b>Techno Beats</b>"
        )

if __name__ == "__main__":
    print("🔰 Techno Beats - Number Information Bot Started!")
    print(f"👤 Admin ID: {ADMIN_ID}")
    print(f"🚫 Blocked Numbers: {BLOCKED_NUMBERS}")
    print("📱 Send any mobile number to get complete information")
    print("👨‍💻 Created by @Techno_beats")
    print("✅ Bot is running...")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ Bot error: {e}")