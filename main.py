import asyncio
import random
import time
import curses
from curses import wrapper
from itertools import cycle

from curses_tools import draw_frame, load_sprite, read_controls, get_frame_size

global SPACESHIP_ROW_POSITION
global SPACESHIP_COL_POSITION


async def blink(canvas, row, column, symbol='*'):

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(random.randint(1, 20)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, sprites):

    for sprite in cycle(sprites):
        prev_row_pos = SPACESHIP_ROW_POSITION
        prev_col_pos = SPACESHIP_COL_POSITION
        draw_frame(
            canvas,
            SPACESHIP_ROW_POSITION,
            SPACESHIP_COL_POSITION,
            sprite
        )
        await asyncio.sleep(0)
        draw_frame(canvas, prev_row_pos, prev_col_pos, sprite, negative=True)


def draw(canvas):
    curses.curs_set(0)
    canvas.border()
    canvas.nodelay(True)
    max_row, max_col = canvas.getmaxyx()

    spaceship_sprite1 = load_sprite('sprites/rocket_frame_1.txt')
    spaceship_sprite2 = load_sprite('sprites/rocket_frame_2.txt')

    sprite_row_size, sprite_col_size = get_frame_size(spaceship_sprite1)

    TIC_TIMEOUT = 0.1
    spaceship_speed = 2

    global SPACESHIP_ROW_POSITION
    global SPACESHIP_COL_POSITION

    SPACESHIP_ROW_POSITION = max_row//2
    SPACESHIP_COL_POSITION = max_col//2

    type_of_stars = '+*.:`"'

    coroutines = [
        blink(
            canvas, random.randint(2, max_row-2), random.randint(2, max_col-2),
            symbol=random.choice(type_of_stars)
            ) for i in range(0, 200)
    ]
    coroutine_fire = fire(canvas, max_row//2, max_col//2)
    coroutines.append(coroutine_fire)
    coroutines.append(
        animate_spaceship(canvas, [spaceship_sprite1, spaceship_sprite2])
    )

    while True:

        for coroutine in coroutines.copy():
            try:

                coroutine.send(None)

                row_direction, col_direction, space_pressed = read_controls(canvas)
                if SPACESHIP_ROW_POSITION+row_direction*spaceship_speed < 1:
                    SPACESHIP_ROW_POSITION = 1
                else:
                    SPACESHIP_ROW_POSITION += row_direction * spaceship_speed

                if SPACESHIP_ROW_POSITION + row_direction * spaceship_speed\
                        > max_row - sprite_row_size - 1:
                    SPACESHIP_ROW_POSITION = max_row - sprite_row_size - 1
                else:
                    SPACESHIP_ROW_POSITION += row_direction * spaceship_speed

                if SPACESHIP_COL_POSITION+col_direction*spaceship_speed\
                        > max_col-sprite_col_size-1:
                    SPACESHIP_COL_POSITION = max_col - sprite_col_size - 1
                else:
                    SPACESHIP_COL_POSITION += col_direction * spaceship_speed

                if SPACESHIP_COL_POSITION+col_direction*spaceship_speed < 1:
                    SPACESHIP_COL_POSITION = 1
                else:
                    SPACESHIP_COL_POSITION += col_direction * spaceship_speed

            except StopIteration:
                coroutines.remove(coroutine)

        if len(coroutines) == 0:
            coroutines = [
                blink(
                    canvas,
                    random.randint(2, max_row-2),
                    random.randint(2, max_col-2),
                    symbol=random.choice(type_of_stars)
                ) for i in range(0, 200)
            ]
            coroutines.append(
                animate_spaceship(
                    canvas,
                    [spaceship_sprite1, spaceship_sprite2]
                )
            )

        canvas.refresh()

        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    wrapper(draw)
