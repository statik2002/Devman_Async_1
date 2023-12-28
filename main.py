import asyncio
from random import randint, choice
import time
import curses
import uuid
from curses import wrapper
from itertools import cycle
from explosion import explode

from curses_tools import draw_frame, load_sprite, read_controls, get_frame_size
from game_scenario import get_garbage_delay_tics, PHRASES
from obstacles import Obstacle
from physics import update_speed

coroutines = []
obstacles = []
obstacles_in_last_collisions = []
game_over_sprite = load_sprite('sprites/game_over.txt')
year = 1957


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


async def fly_garbage(canvas, column, garbage_frame, obstacle_uid, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start."""

    obstacle = next(obstacle for obstacle in obstacles
                    if obstacle.uid == obstacle_uid)

    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 1

    garbage_frame_size_row, garbage_frame_size_col = get_frame_size(garbage_frame)

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            obstacles.remove(obstacle)
            coroutines.append(explode(
                canvas,
                row + garbage_frame_size_row//2,
                column + garbage_frame_size_col//2
            ))
            return
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle.row += speed

    obstacles.remove(obstacle)


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
    max_row, max_column = rows - 2, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        for obstacle in obstacles:
            if obstacle.has_collision(row, column, 1, 1):
                canvas.addstr(round(row), round(column), ' ')
                obstacles_in_last_collisions.append(obstacle)
                return
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(
        canvas,
        sprites,
        row_position,
        col_position,
        col_speed,
        row_speed,
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

            for obstacle in obstacles:
                if obstacle.has_collision(
                        row_position,
                        col_position,
                        sprite_row_size,
                        sprite_col_size):
                    draw_frame(
                        canvas,
                        row_position,
                        col_position,
                        sprite,
                        negative=True
                    )
                    coroutines.append(show_gameover(canvas))
                    return

            await asyncio.sleep(0)

            row_direction, col_direction, space_pressed = read_controls(canvas)
            row_speed, col_speed = update_speed(row_speed, col_speed,
                                                row_direction, col_direction)
            row_position += row_speed
            col_position += col_speed
            if space_pressed and year > 2020:
                coroutines.append(fire(canvas, row_position,
                                       col_position, rows_speed=-1))

            new_row_position, new_col_position = change_spaceship_position(
                row_position,
                col_position,
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
                              max_row, max_col,
                              sprite_row_size, sprite_col_size):

    if row_position < 1:
        row_position = max(1, row_position)

    if row_position > max_row - sprite_row_size - 1:
        row_position = min(
            max_row - sprite_row_size - 1,
            row_position
        )

    if col_position < 1:
        col_position = max(1, col_position)

    if col_position > max_col - sprite_col_size - 2:
        col_position = min(
            max_col - sprite_col_size - 2,
            col_position)

    return row_position, col_position


async def fill_orbit_with_garbage(trash_sprites: list, canvas,
                                  star_field_width: tuple, trash_offset_tics):
    global year
    phrase = PHRASES[year]

    while True:
        canvas.addstr(0, 10, f'{year}', curses.A_DIM)
        canvas.addstr(0, 20, f'{phrase}', curses.A_DIM)
        timeout = get_garbage_delay_tics(year)
        if timeout:
            phrase = PHRASES.get(year) if PHRASES.get(year) else phrase
            trash_offset_tics = timeout
            sprite = trash_sprites[randint(0, len(trash_sprites) - 1)]
            sprite_row_size, sprite_col_size = get_frame_size(sprite)
            sprite_position = randint(*star_field_width)
            max_sprite_col_position = min(
                sprite_position,
                star_field_width[1] - sprite_col_size
            )
            obstacle = Obstacle(
                1,
                max_sprite_col_position,
                sprite_row_size,
                sprite_col_size,
                uid=uuid.uuid4()
            )
            obstacles.append(obstacle)
            coroutines.append(fly_garbage(
                canvas,
                column=max_sprite_col_position,
                garbage_frame=sprite,
                obstacle_uid=obstacle.uid)
            )

        await tick_timeout(trash_offset_tics)
        year += 1


async def tick_timeout(sec=1):
    for _ in range(sec):
        await asyncio.sleep(0)


async def show_gameover(canvas):
    max_row, max_col = canvas.getmaxyx()
    sprite_row_size, sprite_col_size = get_frame_size(game_over_sprite)

    while True:
        draw_frame(canvas, max_row//2-sprite_row_size//2,
                   max_col//2-sprite_col_size//2, game_over_sprite)
        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(0)
    canvas.border(0, 0, 0, ' ', 0, 0, ' ', ' ')
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

    tic_timeout = 0.15
    row_speed = 0
    col_speed = 0
    stars_offset_ticks = (1, 20)
    trash_offset_ticks = 10
    star_field_width = (1, max_row-2)
    star_field_height = (1, max_col-2)

    spaceship_row_position = max_row // 2
    spaceship_col_position = max_col // 2

    type_of_stars = '+*.:`"'

    coroutines.append(blink(
            canvas,
            randint(*star_field_width),
            randint(*star_field_height),
            randint(*stars_offset_ticks),
            symbol=choice(type_of_stars)
        ) for i in range(0, 200))
    coroutines.append(fill_orbit_with_garbage(trash_sprites,
                                              canvas, star_field_height,
                                              trash_offset_ticks))
    coroutines.append(
        animate_spaceship(
            canvas,
            [spaceship_sprite1, spaceship_sprite2],
            spaceship_row_position,
            spaceship_col_position,
            row_speed,
            col_speed,
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
