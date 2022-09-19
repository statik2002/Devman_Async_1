import asyncio
import time
import curses
from curses import wrapper


async def blink(canvas, row, column, symbol='#'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)


def draw_star(row, column, canvas):
    canvas.addch(row, column, '*', curses.A_DIM)
    canvas.refresh()
    time.sleep(2)
    canvas.addch(row, column, '*')
    canvas.refresh()
    time.sleep(0.3)
    canvas.addch(row, column, '*', curses.A_BOLD)
    time.sleep(0.5)
    canvas.refresh()
    time.sleep(0.5)
    canvas.addch(row, column, '*')
    canvas.refresh()
    time.sleep(0.3)


def draw(canvas):
    curses.curs_set(0)
    canvas.border()
    count = 5
    coroutine = blink(canvas, 5, 5)
    while count > 0:

        try:
            coroutine.send(None)
            canvas.refresh()
            time.sleep(1)
        except StopIteration:
            coroutine = blink(canvas, 5, 5)
            count -= 1


if __name__ == '__main__':
    curses.update_lines_cols()
    wrapper(draw)
