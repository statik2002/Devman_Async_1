import asyncio
from random import randint, choice
import time
import curses
from curses import wrapper
from itertools import cycle

from curses_tools import draw_frame, load_sprite, read_controls, get_frame_size


async def blink(canvas, row, column, offset_tics, symbol='*'):

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await tick_timeout(offset_tics)

        canvas.addstr(row, column, symbol)
        await tick_timeout(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await tick_timeout(5)

        canvas.addstr(row, column, symbol)
        await tick_timeout(3)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


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
        for tick in range(2):
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
            row_position = new_row_position
            col_position = new_col_position

            draw_frame(
                canvas,
                prev_row_pos,
                prev_col_pos,
                old_sprite,
                negative=True
            )



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


async def fill_orbit_with_garbage(trash_sprites :list, coroutines :list, canvas, star_field_width: tuple, trash_offset_tics):

    while True:
        sprite = trash_sprites[randint(0, len(trash_sprites)-1)]
        sprite_row_size, sprite_col_size = get_frame_size(sprite)
        sprite_position = randint(*star_field_width)
        max_sprite_col_position = min(sprite_position, star_field_width[1]-sprite_col_size)
        coroutines.append(fly_garbage(canvas, column=max_sprite_col_position, garbage_frame=sprite))
        await tick_timeout(trash_offset_tics)


async def tick_timeout(sec=1):
    for _ in range(sec):
        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(0)
    canvas.border()
    canvas.nodelay(True)
    max_row, max_col = canvas.getmaxyx()

    spaceship_sprite1 = load_sprite('sprites/rocket_frame_1.txt')
    spaceship_sprite2 = load_sprite('sprites/rocket_frame_2.txt')

    trash_sprites = [
        load_sprite('sprites/duck.txt'),
        load_sprite('sprites/hubble.txt'),
        load_sprite('sprites/lamp.txt'),
        load_sprite('sprites/trash_large.txt'),
        load_sprite('sprites/trash_small.txt'),
        load_sprite('sprites/trash_xl.txt')
    ]

    sprite_row_size, sprite_col_size = get_frame_size(spaceship_sprite1)

    tic_timeout = 0.1
    spaceship_speed = 1
    stars_offset_ticks = (1, 20)
    trash_offset_ticks = 10
    star_field_width = (1, max_row-2)
    star_field_height = (1, max_col-2)

    spaceship_row_position = max_row // 2
    spaceship_col_position = max_col // 2

    type_of_stars = '+*.:`"'

    coroutines = [
        blink(
            canvas,
            randint(*star_field_width),
            randint(*star_field_height),
            randint(*stars_offset_ticks),
            symbol=choice(type_of_stars)
        ) for i in range(0, 200)
    ]
    animate_fire = fire(canvas, max_row//2, max_col//2)
    coroutines.append(animate_fire)
    coroutines.append(fill_orbit_with_garbage(trash_sprites, coroutines, canvas, star_field_height, trash_offset_ticks))
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
