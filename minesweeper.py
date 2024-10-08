import tkinter as tk
import random
from PIL import Image, ImageTk

class MinesweeperGUI:
    def __init__(self, root, size=5, mines=5):
        self.root = root
        self.size = size
        self.mines = mines
        self.cell_size = 40  # Each cell is 40x40 pixels
        self.mine_positions = set()  # Mines will be placed after the first click
        self.flagged_positions = set()
        self.board = [[' ' for _ in range(size)] for _ in range(size)]  # Empty board
        self.visible_board = [['_' for _ in range(size)] for _ in range(size)]
        self.remaining_mines = self.mines
        self.unopened_safe_fields = (self.size * self.size) - self.mines  # Safe unopened fields
        self.game_active = True  # Game starts in an active state
        self.load_images()  # Load the images for the game (hidden, flags, etc.)
        self.create_widgets()  # Set up the UI and game board
        # We do NOT generate mines here; we wait until the first click to do so

    def load_images(self):
        # Load sprites (ensure these image files exist in your directory)
        self.images = {}
        self.images['hidden'] = ImageTk.PhotoImage(Image.open("hidden.png").resize((self.cell_size, self.cell_size)))
        self.images['mine'] = ImageTk.PhotoImage(Image.open("mine.png").resize((self.cell_size, self.cell_size)))
        self.images['flag'] = ImageTk.PhotoImage(Image.open("flag.png").resize((self.cell_size, self.cell_size)))
        self.images['numbers'] = {
            str(i): ImageTk.PhotoImage(Image.open(f"{i}.png").resize((self.cell_size, self.cell_size))) for i in range(9)
        }

    def generate_mines(self, first_click_row, first_click_col):
        available_positions = [(r, c) for r in range(self.size) for c in range(self.size)]
        
        # Remove positions near the first click to ensure no mines are placed there
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1), (0, 0)]
        safe_zone = [(first_click_row + dr, first_click_col + dc) for dr, dc in directions]
        
        # Filter out positions in the safe zone
        available_positions = [pos for pos in available_positions if pos not in safe_zone and 0 <= pos[0] < self.size and 0 <= pos[1] < self.size]

        # Randomly place mines in available positions
        while len(self.mine_positions) < self.mines:
            position = random.choice(available_positions)
            available_positions.remove(position)
            self.mine_positions.add(position)
            self.board[position[0]][position[1]] = '*'
    
    def create_widgets(self):
        # Create the status bar showing remaining mines
        self.status_label = tk.Label(self.root, text=f"Remaining Mines: {self.remaining_mines}")
        self.status_label.pack(side=tk.TOP, pady=5)

        # Create the canvas for the game
        self.canvas = tk.Canvas(self.root, width=self.size * self.cell_size, height=self.size * self.cell_size)
        self.canvas.pack()

        self.rectangles = {}
        self.draw_board()

    def update_status(self):
        self.status_label.config(text=f"Remaining Mines: {self.remaining_mines} | Safe Unopened: {self.unopened_safe_fields}")

    def draw_board(self):
        self.canvas.delete("all")  # Clear the canvas if we're redrawing
        for r in range(self.size):
            for c in range(self.size):
                x1, y1 = c * self.cell_size, r * self.cell_size
                rect = self.canvas.create_image(x1, y1, image=self.images['hidden'], anchor='nw')
                # Bind left-click (reveal), Ctrl + Left Click (flag), and right-click (flag) events
                self.canvas.tag_bind(rect, '<Button-1>', lambda event, r=r, c=c: self.reveal(r, c))  # Left-click to reveal
                self.canvas.tag_bind(rect, '<Control-Button-1>', lambda event, r=r, c=c: self.toggle_flag(r, c))  # Ctrl + Left Click to flag
                self.canvas.tag_bind(rect, '<Button-2>', lambda event, r=r, c=c: self.toggle_flag(r, c))  # Right-click to flag
                self.rectangles[(r, c)] = rect

    def toggle_flag(self, row, col):
        if not self.game_active:
            return  # Do nothing if the game is over or won

        # Check if the cell is already revealed
        if self.visible_board[row][col] != '_':
            return  # Do nothing if the cell is already revealed

        if (row, col) in self.flagged_positions:
            # Remove the flag
            self.canvas.itemconfig(self.rectangles[(row, col)], image=self.images['hidden'])
            self.flagged_positions.remove((row, col))
            self.remaining_mines += 1
        else:
            if self.remaining_mines > 0:
                # Add the flag
                self.canvas.itemconfig(self.rectangles[(row, col)], image=self.images['flag'])
                self.flagged_positions.add((row, col))
                self.remaining_mines -= 1
        self.update_status()

    def count_adjacent_mines(self, row, col):
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        mine_count = 0
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < self.size and 0 <= c < self.size:
                if self.board[r][c] == '*':
                    mine_count += 1
        return mine_count

    def count_adjacent_flags(self, row, col):
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        flag_count = 0
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < self.size and 0 <= c < self.size:
                if (r, c) in self.flagged_positions:
                    flag_count += 1
        return flag_count
    
    def reveal(self, row, col):
        if not self.game_active:
            return  # Do nothing if the game is over or won

        # Place mines after the first click to ensure no mines near the first cell
        if len(self.mine_positions) == 0:  # This is the first click
            self.generate_mines(row, col)  # Pass the first click coordinates

        if self.visible_board[row][col].isdigit() and int(self.visible_board[row][col]) == self.count_adjacent_flags(row, col):
            self.chord_reveal(row, col)
            return

        if (row, col) in self.flagged_positions:
            return  # Do nothing if the cell is flagged

        if (row, col) in self.mine_positions:
            self.canvas.itemconfig(self.rectangles[(row, col)], image=self.images['mine'])
            self.game_over()
            return
        
        # This is the first time the cell is revealed
        mine_count = self.count_adjacent_mines(row, col)
        self.visible_board[row][col] = str(mine_count)
        self.canvas.itemconfig(self.rectangles[(row, col)], image=self.images['numbers'][str(mine_count)])

        # Decrease unopened safe fields only when a non-mine, unrevealed cell is revealed
        self.unopened_safe_fields -= 1
        self.update_status()
        
        if mine_count == 0:
            self.reveal_adjacent_cells(row, col)
        
        if self.check_win():
            self.win_game()

    def chord_reveal(self, row, col):
        # Reveal all unflagged cells around the numbered cell
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < self.size and 0 <= c < self.size:
                if (r, c) not in self.flagged_positions and self.visible_board[r][c] == '_':
                    self.reveal(r, c)

    def reveal_adjacent_cells(self, row, col):
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < self.size and 0 <= c < self.size and self.visible_board[r][c] == '_':
                self.reveal(r, c)
    
    def check_win(self):
        for r in range(self.size):
            for c in range(self.size):
                if self.visible_board[r][c] == '_' and (r, c) not in self.mine_positions:
                    return False
        return True

    def game_over(self):
        self.status_label.config(text="Game Over!")
        self.game_active = False  # Lock the game from further input
        # Reveal all mines
        for r, c in self.mine_positions:
            self.canvas.itemconfig(self.rectangles[(r, c)], image=self.images['mine'])

    def win_game(self):
        self.status_label.config(text="Game Won!")
        self.game_active = False  # Lock the game from further input
    
    def show_message(self, title, message):
        top = tk.Toplevel(self.root)
        top.title(title)
        msg = tk.Label(top, text=message)
        msg.pack(pady=10)
        btn = tk.Button(top, text="OK", command=top.destroy)
        btn.pack(pady=5)

    def set_difficulty(self, difficulty):
        if difficulty == 'Easy':
            self.size = 5
            self.mines = 5
        elif difficulty == 'Medium':
            self.size = 10
            self.mines = 15
        elif difficulty == 'Hard':
            self.size = 20
            self.mines = 70
        
        # Reset the game with the new difficulty
        self.reset_game()

    def reset_game(self):
        self.mine_positions = set()
        self.flagged_positions = set()
        self.remaining_mines = self.mines
        self.unopened_safe_fields = (self.size * self.size) - self.mines  # Reset safe unopened fields count
        self.board = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.visible_board = [['_' for _ in range(self.size)] for _ in range(self.size)]
        self.canvas.config(width=self.size * self.cell_size, height=self.size * self.cell_size)
        self.status_label.config(text=f"Remaining Mines: {self.remaining_mines} | Safe Unopened: {self.unopened_safe_fields}")
        self.game_active = True  # Reset game state to active
        self.draw_board()  # Redraw the board
        # Do NOT generate mines here — wait for the first click to generate them

def main():
    root = tk.Tk()
    root.title("Minesweeper")

    game = MinesweeperGUI(root)

    # Create a menu
    menu = tk.Menu(root)
    root.config(menu=menu)

    # Add a Difficulty menu
    difficulty_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Difficulty", menu=difficulty_menu)
    
    difficulty_menu.add_command(label="Easy", command=lambda: game.set_difficulty('Easy'))
    difficulty_menu.add_command(label="Medium", command=lambda: game.set_difficulty('Medium'))
    difficulty_menu.add_command(label="Hard", command=lambda: game.set_difficulty('Hard'))

    root.mainloop()

if __name__ == "__main__":
    main()