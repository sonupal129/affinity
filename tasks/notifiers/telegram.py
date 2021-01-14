from telethon.sync import TelegramClient

# # CODE Below

api_id = 1571454571
api_hash = "AAH_SUq7Pbp4mscOAVK5u22odnOsn8SvsOo"
bot_token = ":".join([str(api_id), api_hash])
print(bot_token)
bot = TelegramClient("aff129_bot", api_id, api_hash).start(bot_token=bot_token)

print(bot)