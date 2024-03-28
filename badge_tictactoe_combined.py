import gc
import random
import time
import board
import displayio
import vectorio
import keypad
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import bitmap_label as label
import neopixel

STATE_BADGE = 0
STATE_TIC_TAC_TOE = 1

CURRENT_STATE = STATE_BADGE

# Ignore multiple state changes if they occur within this many seconds
CHANGE_STATE_BTN_COOLDOWN = 0.75
LAST_STATE_CHANGE = -1

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Button numbers
BUTTON_UP = 0
BUTTON_DOWN = 1
BUTTON_A = 2
BUTTON_B = 3
BUTTON_C = 4

# display setup
display = board.DISPLAY
tictactoe_group = displayio.Group()


# background color palette
background_p = displayio.Palette(1)
background_p[0] = 0xffffff

# make a rectangle same size as display and add it to main group
background_rect = vectorio.Rectangle(pixel_shader=background_p, width=display.width, height=display.height)
tictactoe_group.append(background_rect)


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

        try:
            # update selector_position to a random empty location
            self.selector_position = random.choice(self.empty_spots)
        except IndexError:
            # no more empty spaces
            pass

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
tictactoe_group.append(game)

# button keys setup
buttons = keypad.Keys((board.SW_UP, board.SW_DOWN, board.SW_A, board.SW_B, board.SW_C), value_when_pressed=True)
pressed_buttons = []

pixels = neopixel.NeoPixel(board.SDA, 8)

display = board.DISPLAY

badge_group = displayio.Group()

rectangle_white = Rect(0, int(display.height / 3), display.width, int(display.height * 0.5), fill=WHITE)

badge_group.append(rectangle_white)

text = label.Label(terminalio.FONT, text="", color=WHITE)
text.x = 10
text.y = 14
badge_group.append(text)

text.scale = 2


def set_state(new_state):
    if new_state == STATE_BADGE:
        display.root_group = badge_group
    elif new_state == STATE_TIC_TAC_TOE:
        display.root_group = tictactoe_group
    try:
        display.refresh()
    except RuntimeError as e:
        print("Caught Runtime error, probably refreshed too soon.")
        print(e)
        time.sleep(display.time_to_refresh + 0.6)
        display.refresh()


set_state(CURRENT_STATE)

while True:
    event = buttons.events.get()
    if event:
        if event.pressed:
            if event.key_number not in pressed_buttons:
                pressed_buttons.append(event.key_number)
        elif event.released:
            if event.key_number in pressed_buttons:
                pressed_buttons.remove(event.key_number)
    try:
        if CURRENT_STATE == STATE_TIC_TAC_TOE:
            if event:
                print(event)

                if BUTTON_A in pressed_buttons and \
                        event.key_number == BUTTON_C and event.released:
                    print("A held and C pressed")
                    CURRENT_STATE = STATE_BADGE
                    set_state(CURRENT_STATE)
                    LAST_STATE_CHANGE = time.monotonic()
                    continue

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
        elif CURRENT_STATE == STATE_BADGE:
            if event:
                if LAST_STATE_CHANGE + CHANGE_STATE_BTN_COOLDOWN < time.monotonic():
                    print(f"badged state event: {event}")
                    if event.key_number in (BUTTON_UP, BUTTON_DOWN) and event.released:
                        print("Refreshing.")
                        print(f"free mem: {gc.mem_free()}")
                        text.text = f"Hello! {event.key_number}"
                        display.refresh()
                        print(display.time_to_refresh)
                        print(event)
                        pixels.fill((100, 0, 0))
                    elif event.key_number == BUTTON_A and event.released:
                        CURRENT_STATE = STATE_TIC_TAC_TOE
                        set_state(CURRENT_STATE)

            else:
                pixels.fill(0)

    except RuntimeError as e:
        print("Caught Runtime error, probably refreshed too soon.")
        print(e)
        time.sleep(display.time_to_refresh + 0.6)
        display.refresh()

