import pygame
from pygame.locals import *
import random
import abc
import time
import copy
import curses

class GameOfLife:

    def __init__(self, size, randomize=True, max_generations=False) -> None:
        # Размер клеточного поля
        self.rows, self.cols = size
        # Предыдущее поколение клеток
        self.prev_generation = self.cell_list()
        # Текущее поколение клеток
        self.curr_generation = self.cell_list(randomize=randomize)
        # Максимальное число поколений
        self.max_generations = max_generations
        # Текущее число поколений
        self.generations = 1

    def cell_list(self, randomize=False):
        """ Создание списка клеток.
        :param randomize: Если True, то создается список клеток, где
        каждая клетка равновероятно может быть живой (1) или мертвой (0).
        :return: Список клеток, представленный в виде матрицы
        """
        self.clist = [[random.randint(0, 1) if randomize else 0 for i in range(
                                        self.rows)] for i in range(self.cols)]
        return self.clist

    def get_neighbours(self, cell):
        """ Вернуть список соседей для указанной ячейки
        :param cell: Позиция ячейки в сетке, задается кортежем вида (row, col)
        :return: Одномерный список ячеек, смежных к ячейке cell
        """
        neighbours = []
        cell_row, cell_col = cell
        for row in range(3):
            for col in range(3):
                cur_row, cur_col = cell_row - 1 + row, cell_col - 1 + col

                if(
                    (cur_row, cur_col) != cell and
                    cur_row >= 0 and cur_col >= 0 and
                    cur_col < self.cols and
                    cur_row < self.rows
                ):
                    neighbours.append((cell_row - 1 + row, cell_col - 1 + col))

        return neighbours

    def update_cell_list(self, cell_list):
        """ Выполнить один шаг игры.
        Обновление всех ячеек происходит одновременно. Функция возвращает
        новое игровое поле.
        :param cell_list: Игровое поле, представленное в виде матрицы
        :return: Обновленное игровое поле
        """
        new_clist = [[0 for i in range(self.cols)] for i in range(self.rows)]

        for row in range(self.rows):
            for col in range(self.cols):
                neighbours_count = 0

                for cur_cell in self.get_neighbours((row, col)):
                    if cell_list[cur_cell[0]][cur_cell[1]]:
                        neighbours_count += 1

                if(
                    cell_list[row][col] == 1 and neighbours_count >= 2 and
                    neighbours_count <= 3
                ):
                    new_clist[row][col] = 1
                elif cell_list[row][col] == 0 and neighbours_count == 3:
                    new_clist[row][col] = 1

        self.clist = new_clist
        return self.clist

    def step(self) -> None:
        """
        Выполнить один шаг игры.
        """
        self.prev_generation = copy.deepcopy(self.curr_generation)
        self.curr_generation = copy.deepcopy(self.update_cell_list(
                                                    self.curr_generation))
        self.generations += 1

    @property
    def is_max_generations_exceeded(self) -> bool:
        """
        Не превысило ли текущее число поколений максимально допустимое.
        """
        if self.max_generations:
            return self.generations >= self.max_generations
        return False

    @property
    def is_changing(self) -> bool:
        """
        Изменилось ли состояние клеток с предыдущего шага.
        """
        return self.prev_generation != self.curr_generation

    @staticmethod
    def from_file(filename) -> 'GameOfLife':
        """
        Прочитать состояние клеток из указанного файла.
        """
        grid_file = open(filename)

        grid = grid_file.readlines()
        for i in range(len(grid)):
            grid[i] = list(map(int, list(grid[i][0:len(grid[i])-1])))
        life = GameOfLife((len(grid), len(grid[i])))
        life.curr_generation = grid

        grid_file.close()

        return life

    def save(self, filename) -> None:
        """
        Сохранить текущее состояние клеток в указанный файл.
        """
        file = open(filename, 'w')
        for row in range(len(self.curr_generation)):
            file.write("".join(map(str, self.curr_generation[row])) + '\n')

        file.close()



class UI(abc.ABC):
    def __init__(self, life: GameOfLife) -> None:
        self.life = life

    @abc.abstractmethod
    def run(self) -> None:
        pass


class Console(UI):
    def __init__(self, life: GameOfLife) -> None:
        super().__init__(life)

    def draw_borders(self, screen) -> None:
        """ Отобразить рамку """
        for x in range(life.cols+1):
            screen.addstr(x, 0, '|')
            screen.addstr(x, life.rows+1, '|')

        for y in range(1, life.rows+1):
            screen.addstr(0, y, '-')
            screen.addstr(life.cols+1, y, '-')

        screen.addstr(0,           0,         '+')
        screen.addstr(0,           life.cols+1, '+')
        screen.addstr(life.rows+1, 0,         '+')
        screen.addstr(life.rows+1, life.cols+1, '+')

    def draw_grid(self, screen) -> None:
        """ Отобразить состояние клеток """
        for x in range(len(life.curr_generation)):
            for y in range(len(life.curr_generation)):
                if life.curr_generation[x][y]:
                    screen.addstr(x+1, y+1, '*')
                else:
                    screen.addstr(x+1, y+1, ' ')

    def run(self) -> None:
        screen = curses.initscr()
        curses.curs_set(0)

        self.draw_borders(screen)
        self.draw_grid(screen)

        running = True

        while running:
            while life.is_changing and not life.is_max_generations_exceeded:
                life.step()
                self.draw_grid(screen)

                screen.refresh()
                time.sleep(0.5)
            else:
                running = False

        curses.endwin()


if __name__ == '__main__':
    randomize = True
    size = tuple(map(int, input("(row,col): ").split(',')))
    max_generations = int(input('Максимальное количество поколений: '))
    life = GameOfLife(
        size,
        randomize=randomize,
        max_generations=max_generations
        )
    ui = Console(life)
    ui.run()