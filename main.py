from flet import *
import asyncio
from telegram import *
from telegram.ext import *

received_message = []
sent_message = []
user_chat_ids = set()
bot_running = False  # Global variable to track if the bot is running
app = None  # Bot app to track and stop


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_chat_ids.add(user_id)
    await update.message.reply_text("Welcome! You will receive a message every 10 seconds.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track users who send any message."""
    user_id = update.effective_chat.id
    user_chat_ids.add(user_id)
    message = update.message.text
    received_message.append(message)
    await asyncio.sleep(1)


def stop_bot():
    """Gracefully stop the bot polling."""
    global app
    if app:
        print("Stopping bot...")
        app.stop_running()
        print("Bot stopped.")


async def manual_polling(app_instance):
    print("Bot is running manually...")
    offset = None
    print("Bot started.")
    while bot_running:  # Continue polling only if the bot is running
        try:
            updates = await app_instance.bot.get_updates(offset=offset, timeout=5)
            for update in updates:
                await app_instance.process_update(update)
                offset = update.update_id + 1
            print("Updates fetched and processed.")
        except Exception as e:
            print(f"Error during manual polling: {e}")
        await asyncio.sleep(1)


async def broadcast_message(context):
    """Send a message to all stored users and remove the message from the list."""
    while bot_running:  # Send messages only if the bot is running
        if sent_message:
            for num in sent_message:
                for user_id in user_chat_ids:
                    try:
                        await context.bot.send_message(chat_id=user_id, text=num)
                    except Exception as e:
                        print(f"Failed to send message to {user_id}: {e}")
            sent_message.clear()
        await asyncio.sleep(1)


async def bot(bot_api):
    global app
    app = ApplicationBuilder().token(bot_api).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, message_handler))
    await app.initialize()

    try:
        task1 = asyncio.create_task(manual_polling(app))
        task2 = asyncio.create_task(broadcast_message(app))
        await asyncio.gather(task1, task2)
    except (KeyboardInterrupt, SystemExit):
        print("Bot is shutting down due to an interrupt...")
        stop_bot()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        stop_bot()
        raise


# Function to start or stop the bot when the button is clicked
async def toggle_bot_button(start_button, page, api_input):
    global bot_running
    bot_api = api_input.value

    if bot_running == True or bot_running== None:
        bot_running = False
        start_button.text = "Start Bot"
        start_button.bgcolor = colors.GREEN
        stop_bot()  # Stop the bot properly
        page.update()
        print("Bot stopped.")
    elif bot_running == False:
        bot_running = True
        start_button.text = "Stop Bot"
        start_button.color = colors.RED
        page.go("/home")
        page.update()  # Immediately update the UI
        print("Starting the bot...")
        try:
            await asyncio.gather(bot(bot_api))  # Run the bot in the background
        except Exception as e:
            print(f"Failed to start the bot: {e}")
            bot_running = False
            start_button.text = "Start Bot"
            start_button.bgcolor = colors.GREEN
            page.update()

async def flet(page: Page):
    page.title = "Flet to Telegram"
    page.window.height = 600
    page.window.width = 400
    def clicked(e):
        if bot_running:
            message = chat_input.value
            if not message == "":
                sent_message.append(message)
                column.controls.append(
                    Row(
                        [
                            Container(
                                content=Text(value=str(message), selectable=True, bgcolor=colors.PINK),
                                padding=10,  # Add padding around the text
                                border_radius=15,  # Rounded edges
                                bgcolor=colors.PINK,  # Background color
                            )
                        ],
                        alignment=MainAxisAlignment.END,
                        wrap=True
                    )
                )
                chat_input.value = ""
        else:
            column.controls.append(
                Row(
                    [
                        Container(
                            content=Text(value="Error: The message was not sent, you have to start the bot first",
                                         selectable=True, bgcolor=colors.RED),
                            padding=10,
                            border_radius=15,
                            bgcolor=colors.RED,
                        )
                    ],
                    alignment=MainAxisAlignment.END,
                    wrap=True
                )
            )


    column = ListView(
        auto_scroll=True,
        expand=True,
        spacing=10
    )
    chat_input = TextField(
        width=300,
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit= clicked
    )

    send_button = FloatingActionButton(on_click=clicked, icon=icons.SEND_ROUNDED, mini=True,)
    start_button = ElevatedButton(
        text="Start Bot",
        on_click=lambda e: asyncio.run(toggle_bot_button(start_button, page, api_input)),
        bgcolor=colors.GREEN,

    )
    api_input = TextField(
        hint_text="Paste your bot API here...",
        autofocus=True,
        filled=True,
        on_submit=lambda e: asyncio.run(toggle_bot_button(start_button, page, api_input))
    )

    def route_change(route):
        if page.route == "/":
            page.views.clear()
            if not any(v.route== "/" for v in page.views):
                page.views.append(
                    View(
                        "/",
                        [
                            AppBar(
                                title= Text("Telegram App"),
                                center_title= True,
                                bgcolor=colors.WHITE,
                                color= colors.BLACK,
                            ),
                            Container(
                                content=Column([
                                    api_input,
                                    Row([start_button], alignment=MainAxisAlignment.CENTER),
                                ],
                                    expand=True,
                                    spacing=10,
                                ),
                                padding=10,
                                expand=True,
                                bgcolor= colors.WHITE
                            )
                        ]
                    )
                )
        if page.route == "/home":
            page.views.clear()
            if not any(v.route== "/home" for v in page.views):
                page.views.append(
                    View(
                        "/home",
                        [
                            AppBar(
                                title= Text("Telegram App"),
                                center_title= True,
                                bgcolor=colors.WHITE,
                                color= colors.BLACK,

                            ),
                            Container(
                                content=Column([
                                    column,
                                    Row([chat_input, send_button, start_button], alignment=MainAxisAlignment.END),
                                ],
                                    expand=True,
                                    spacing=10,
                                ),
                                padding=10,
                                expand=True,
                                bgcolor= colors.WHITE
                            )
                        ]
                    )
                )
        page.update()

    page.on_route_change = route_change
    page.go(page.route)
    page.update()

    async def receive_messages(page: Page):
        while True:
            for message in received_message:
                column.controls.append(
                    Row(
                        [
                            Container(
                                content=Text(value=str(message), selectable=True, bgcolor=colors.GREEN),
                                padding=10,  # Padding for received messages
                                border_radius=15,  # Rounded edges
                                bgcolor=colors.GREEN,
                            )
                        ],
                        alignment=MainAxisAlignment.START,  # Received messages aligned to the left
                        wrap=True
                    )
                )
            page.update()
            received_message.clear()
            await asyncio.sleep(1)


    await asyncio.create_task(receive_messages(page))


async def main():
    task2 = asyncio.create_task(app_async(target=flet))
    await asyncio.gather(task2)


if __name__ == "__main__":
    asyncio.run(main())

