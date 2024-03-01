from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import nest_asyncio
import asyncio

class ConnectFour:
    def __init__(self):
        self.board = [[' ' for _ in range(7)] for _ in range(6)]
        self.current_player = '🔴'  # Red starts the game
        self.game_over = False
        self.last_move = None  # Track the last move made
        self.board_visible = False  # Track visibility of the board

    def print_board(self):
        if not self.board_visible:
            return f"It's Player {self.current_player}'s turn!\nBoard is hidden. Use /show to toggle visibility."
        board_view = "|1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣|\n"
        # Enhanced visual representation
        for row in self.board:
            row_str = ' '.join(['⚪️' if cell == ' ' else cell for cell in row])
            board_view += f"|{row_str}|\n"
            # Indicate whose turn it is
        if self.game_over == False:
            board_view += f"\nIt's Player {self.current_player}'s turn!\nBoard is shown. Use /show to toggle visibility."
        return board_view

    def drop_piece(self, column):
        for i in range(5, -1, -1):
            if self.board[i][column] == ' ':
                self.board[i][column] = self.current_player
                self.last_move = column  # Update the last move
                if self.check_win(i, column):
                    self.game_over = True
                else:
                    self.toggle_player()
                return True
        return False

    def check_win(self, row, col):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            for d in [1, -1]:
                r, c = row, col
                while 0 <= r+d*dr < 6 and 0 <= c+d*dc < 7 and self.board[r+d*dr][c+d*dc] == self.current_player:
                    count += 1
                    r, c = r+d*dr, c+d*dc
                    if count >= 4:
                        return True
        return False

    def toggle_player(self):
        self.current_player = '🔵' if self.current_player == '🔴' else '🔴'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = ConnectFour()
    context.chat_data['game'] = game
    keyboard = [[InlineKeyboardButton(str(i + 1), callback_data=str(i)) for i in range(7)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=game.print_board(), reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    game = context.chat_data.get('game')
    if not game:
        await query.edit_message_text(text="Game not started. Use /start to begin a game.")
        return

    if game.game_over:
        await query.edit_message_text(text="Game over. Use /start to play again.")
        return
    
    player_name = query.from_user.first_name
    if query.from_user.username:
        player_name += f" (@{query.from_user.username})"
    
    column_selected = int(query.data)
    
    last_message_id = context.chat_data.get('last_message_id')
    if last_message_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=last_message_id)
        except Exception as e:
            print(f"Failed to delete message: {e}")  # For debugging
    
    keyboard = [[InlineKeyboardButton(str(i + 1), callback_data=str(i)) for i in range(7)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    game.board_visible = False
    move_announcement = f"{player_name} played " + ("🔵" if game.current_player == '🔵' else "🔴") + f" in column {column_selected + 1}.\n\n"
    
    if game.drop_piece(column_selected):
        # Ensure the board visibility is always true after a move to show the updated board state
        text = move_announcement + game.print_board()
        
        if game.game_over:
            game.board_visible = True
            text = move_announcement + game.print_board() +                                                                     \
                    "\nGame over. " + (f"(@{query.from_user.username}) Wins!" if game.current_player == '🔴' else "🔴 Wins!") + \
                    "\nStart a new game with /start."
            # Send the game over message without reply_markup to end the game
            sent_message = await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        else:
            sent_message = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
        
    else:
        text = "Column full. Try a different one.\n" + move_announcement + game.print_board()
        sent_message = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
    
    context.chat_data['last_message_id'] = sent_message.message_id


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = context.chat_data.get('game')
    if not game:
        await update.message.reply_text("Start a new game with /start.")
        return
    
    last_message_id = context.chat_data.get('last_message_id')
    if last_message_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=last_message_id)
        except Exception as e:
            print(f"Failed to delete message: {e}")  # For debugging
    
    game.board_visible = not game.board_visible  # Toggle the visibility

    # Prepare the inline keyboard for making moves
    keyboard = [[InlineKeyboardButton(str(i + 1), callback_data=str(i)) for i in range(7)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = game.print_board()

    # Send or edit the message with the inline keyboard
    sent_message = await update.message.reply_text(text=message_text, reply_markup=reply_markup)

    # Store the message ID of the sent message for future deletion
    context.chat_data['last_message_id'] = sent_message.message_id
    

def setup_bot_commands(application):
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('show', show))

nest_asyncio.apply()

async def main():
    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
    token = '6805697306:AAFzZc1ujtzvrtxsarsAwV32f83vSRi3Qv8'
    application = Application.builder().token(token).build()

    setup_bot_commands(application)

    # Start the bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())

