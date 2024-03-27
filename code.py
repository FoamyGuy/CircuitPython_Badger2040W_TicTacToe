import random
import time
import board
import displayio
import vectorio
import keypad

# display setup
display = board.DISPLAY
main_group = displayio.Group()
display.root_group = main_group

# background color palette
background_p = displayio.Palette(1)
background_p[0] = 0xffffff

# make a rectangle same size as display and add it to main group
background_rect = vectorio.Rectangle(pixel_shader=background_p, width=display.width, height=display.height)
main_group.append(background_rect)


class TicTacToeGame(displayio.Group):
    """
    Helper class to hold the visual and logical elements that make up the game.
    """
    def __init__(self, display):
        super().__init__()
        self.display = display
        
        # board lines color palette
        self.lines_p = displayio.Palette(1)
        self.lines_p[0] = 0x000000
        
        # randomly decide who is first.
        self.turn = random.choice(("X", "O"))
        
        # board lines
        self.left_line = vectorio.Rectangle(pixel_shader=self.lines_p, width=2, height=118, y=5, x=40)
        self.append(self.left_line)
        self.right_line = vectorio.Rectangle(pixel_shader=self.lines_p, width=2, height=118, y=5, x=80)
        self.append(self.right_line)
        self.top_line = vectorio.Rectangle(pixel_shader=self.lines_p, width=118, height=2, y=40, x=5)
        self.append(self.top_line)
        self.bottom_line = vectorio.Rectangle(pixel_shader=self.lines_p, width=118, height=2, y=80, x=5)
        self.append(self.bottom_line)
        
        #  dotted line box selector indicator
        self.selector_bmp = displayio.OnDiskBitmap("selector.bmp")
        self.selector_tg = displayio.TileGrid(pixel_shader=self.selector_bmp.pixel_shader, bitmap=self.selector_bmp)
        self.append(self.selector_tg)
        
        # X and O piece bmps
        self.x_bmp = displayio.OnDiskBitmap("x.bmp")
        self.o_bmp = displayio.OnDiskBitmap("o.bmp")
        
        # mapping of board position indexes to pixel locations
        self.selector_location_map = [
            [(7, 7), (45, 7), (85, 7)],
            [(7, 45), (45, 45), (85, 45)],
            [(7, 85), (45, 85), (85, 85)],
        ]

        # set starting position of the selector
        self.selector_position = [2, 1]
        
        # move the selector tilegrid to the starting position, but do not refresh yet
        self.place_tilegrid_at_board_position(self.selector_position, self.selector_tg, refresh=False)

        # list that will hold all X and O piece TileGrids, added as they get played.
        self.played_pieces = []
        
        # 2D list representation of the board state
        self.board_state = [
            ["", "", ""],
            ["", "", ""],
            ["", "", ""],
        ]

    def move_selector_up(self):
        if self.selector_position[1] > 0:
            self.selector_position[1] -= 1
            self.place_tilegrid_at_board_position(self.selector_position, self.selector_tg)

    def move_selector_down(self):
        if self.selector_position[1] < 2:
            self.selector_position[1] += 1
            self.place_tilegrid_at_board_position(self.selector_position, self.selector_tg)

    def move_selector_left(self):
        if self.selector_position[0] > 0:
            self.selector_position[0] -= 1
            self.place_tilegrid_at_board_position(self.selector_position, self.selector_tg)

    def move_selector_right(self):
        if self.selector_position[0] < 2:
            self.selector_position[0] += 1
            self.place_tilegrid_at_board_position(self.selector_position, self.selector_tg)

    def play_current_move(self):
        """
        Place a piece at the selected position based on which turn it is currently.
        """
        
        # create the right type of TileGrid based on turn
        if self.turn == "X":
            piece_tg = displayio.TileGrid(pixel_shader=self.x_bmp.pixel_shader, bitmap=self.x_bmp)
        else:  # O's turn
            piece_tg = displayio.TileGrid(pixel_shader=self.o_bmp.pixel_shader, bitmap=self.o_bmp)
        
        # append it to self Group instance
        self.append(piece_tg)
        
        # append it to pieces list so we can remove it later
        self.played_pieces.append(piece_tg)
        
        # move piece TileGrid to the current selected position, but do not refresh yet
        self.place_tilegrid_at_board_position(self.selector_position, piece_tg, refresh=False)
        
        # update the board state with this move
        self.board_state[self.selector_position[1]][self.selector_position[0]] = self.turn
        
        # set the turn to next players
        self.turn = "X" if self.turn == "O" else "O"
        
        # print the board state for debugging
        for row in self.board_state:
            print(row)
            
        # update selector_position to a random empty location
        self.selector_position = random.choice(self.empty_spots)
        
        # move the selector TileGrid to the selector_position and refresh
        self.place_tilegrid_at_board_position(self.selector_position, self.selector_tg, refresh=True)
    @property
    def empty_spots(self):
        """
        returns a list of empty board positions
        """
        empty_spots = []
        for row in range(3):
            for col in range(3):
                
                if self.board_state[col][row] == "":
                    empty_spots.append([row, col])
        return empty_spots
    def place_tilegrid_at_board_position(self, board_position, tilegrid, refresh=True):
        """
        place a tilegrid at a specified board_position. Optionally refresh the display afterward.
        """
        if 0 <= board_position[0] <= 2 and 0 <= board_position[1] <= 2:
            tilegrid.x, tilegrid.y = self.selector_location_map[board_position[1]][board_position[0]]
            if refresh:
                self.display.refresh()
        else:
            print(f"position: {board_position} is out of bounds")


# create the game instance
game = TicTacToeGame(display)

# add it to main group
main_group.append(game)

# refresh to show the game initially
display.refresh()

# button keys setup
keys = keypad.Keys((board.SW_UP, board.SW_DOWN, board.SW_A, board.SW_B, board.SW_C), value_when_pressed=True)

while True:
    event = keys.events.get()
    if event:
        print(event)
        try:
            if event.key_number == 0 and event.released:
                game.move_selector_up()
            elif event.key_number == 1 and event.released:
                game.move_selector_down()
            elif event.key_number == 2 and event.released:
                game.move_selector_left()
            elif event.key_number == 4 and event.released:
                game.move_selector_right()
    
            elif event.key_number == 3 and event.released:
                game.play_current_move()
        except RuntimeError as e:
            print("Caught Runtime error, probably refreshed too soon.")
            print(e)
            time.sleep(display.time_to_refresh + 0.6)
            display.refresh()

