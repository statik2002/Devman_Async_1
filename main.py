import asyncio
import random
import time
import curses
from curses import wrapper
from itertools import cycle

from curses_tools import draw_frame, load_sprite, read_controls, get_frame_size


async def blink(canvas, row, column, offset_tics, symbol='*'):

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(offset_tics):
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


async def fire(canvas, start_row, start_column,
               rows_speed=-0.3, columns_speed=0):
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


async def animate_spaceship(
        canvas,
        sprites,
        row_position,
        col_position,
        spaceship_speed,
        max_row,
        max_col,
        sprite_row_size,
        sprite_col_size):

    for sprite in cycle(sprites):
        prev_row_pos = row_position
        prev_col_pos = col_position

        draw_frame(
            canvas,
            row_position,
            col_position,
            sprite
        )

        old_sprite = sprite
        await asyncio.sleep(0)

        row_direction, col_direction, space_pressed = read_controls(canvas)
        new_row_position, new_col_position = change_spaceship_position(
            row_position,
            col_position,
            row_direction,
            col_direction,
            space_pressed,
            spaceship_speed,
            max_row,
            max_col,
            sprite_row_size,
            sprite_col_size
        )

        draw_frame(
            canvas,
            prev_row_pos,
            prev_col_pos,
            old_sprite,
            negative=True
        )
        row_position = new_row_position
        col_position = new_col_position


def change_spaceship_position(row_position, col_position,
                              row_direction, col_direction,
                              space_pressed, spaceship_speed,
                              max_row, max_col,
                              sprite_row_size, sprite_col_size):

    spaceship_new_row_position = row_position + row_direction * spaceship_speed
    spaceship_new_col_position = col_position + col_direction * spaceship_speed

    if spaceship_new_row_position < 1:
        spaceship_new_row_position = max(1, spaceship_new_row_position)

    if spaceship_new_row_position > max_row - sprite_row_size - 1:
        spaceship_new_row_position = min(
            max_row - sprite_row_size - 1,
            spaceship_new_row_position
        )

    if spaceship_new_col_position < 1:
        spaceship_new_col_position = max(1, spaceship_new_col_position)

    if spaceship_new_col_position > max_col - sprite_col_size - 2:
        spaceship_new_col_position = min(
            max_col - sprite_col_size - 2,
            spaceship_new_col_position)

    return spaceship_new_row_position, spaceship_new_col_position


def draw(canvas):
    curses.curs_set(0)
    canvas.border()
    canvas.nodelay(True)
    max_row, max_col = canvas.getmaxyx()

    spaceship_sprite1 = load_sprite('sprites/rocket_frame_1.txt')
    spaceship_sprite2 = load_sprite('sprites/rocket_frame_2.txt')

    sprite_row_size, sprite_col_size = get_frame_size(spaceship_sprite1)

    tic_timeout = 0.1
    spaceship_speed = 1
    stars_offset_ticks = (1, 20)
    star_field_width = (1, max_row-2)
    star_field_height = (1, max_col-2)

    spaceship_row_position = max_row // 2
    spaceship_col_position = max_col // 2

    type_of_stars = '+*.:`"'

    coroutines = [
        blink(
            canvas,
            random.randint(*star_field_width),
            random.randint(*star_field_height),
            random.randint(*stars_offset_ticks),
            symbol=random.choice(type_of_stars)
        ) for i in range(0, 200)
    ]
    animate_fire = fire(canvas, max_row//2, max_col//2)
    coroutines.append(animate_fire)
    coroutines.append(
        animate_spaceship(
            canvas,
            [spaceship_sprite1, spaceship_sprite2],
            spaceship_row_position,
            spaceship_col_position,
            spaceship_speed,
            max_row,
            max_col,
            sprite_row_size,
            sprite_col_size
        )
    )

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)

        canvas.refresh()
        time.sleep(tic_timeout)


if __name__ == '__main__':
    curses.update_lines_cols()
    wrapper(draw)
