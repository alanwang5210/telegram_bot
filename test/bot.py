from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

BOT_TOKEN = '7828782705:AAEqigD1AUJUTBgObs3t0aUV6L-uFqemgA0'


# /start 命令
async def start(update: Update) -> None:
    keyboard = [[InlineKeyboardButton("Authorize me", callback_data='authorize')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Hi there! Please authorize me to set up a Gmail integration.",
                                    reply_markup=reply_markup)


# 处理按钮点击
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "authorize":
        print("Authorize me")
        await query.message.reply_venue(44.4, 55.5, 'aaaa', 'bbbb', 'bbbb', '')


# 主函数
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()


if __name__ == "__main__":
    main()
