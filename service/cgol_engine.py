import ctypes
import sys
from hashlib import md5
from pathlib import Path
from typing import Tuple

import numpy as np

from .data_model import GameResponse


class GameOfLifeEngine:

    def __init__(
        self, max_generations: int = 1000, repeat_threshold: int = 10, grid_rows: int = 60, grid_cols: int = 40
    ):
        self.grid_rows: int = grid_rows
        self.grid_cols: int = grid_cols
        self.mid_row = self.grid_rows // 2
        self.mid_col = self.grid_cols // 2
        self.grid = np.zeros((self.grid_rows, self.grid_cols))

        self.max_generations = max_generations
        self.repeat_threshold = repeat_threshold

        self.cpp_lib = self._setup_cpp_lib()

    def _setup_cpp_lib(self):
        lib_name = self.get_cpp_lib_name()
        lib_path = Path(__file__).parent / "cpp_engine" / lib_name
        cpp_lib = ctypes.cdll.LoadLibrary(lib_path)

        cpp_lib.runFromWord.argtypes = [
            np.ctypeslib.ndpointer(dtype=np.uint8, ndim=1, flags="C_CONTIGUOUS"),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        cpp_lib.runFromWord.restype = ctypes.c_int

        return cpp_lib

    def bitmask_reshape(self, bitmask: np.ndarray) -> np.ndarray:
        max_len = self.grid_rows * self.grid_cols
        if len(bitmask) >= max_len:
            bitmask = bitmask[:max_len]
            return bitmask.reshape(self.grid.shape)

        optimal_shape = self.find_optimal_shape(bitmask, target_shape=self.grid.shape)
        return bitmask.reshape(optimal_shape)

    def inject_bitmask_seed(self, bitmask: np.ndarray) -> None:
        inj_row = self.mid_row - bitmask.shape[0] // 2
        inj_col = self.mid_col - bitmask.shape[1] // 2

        self.grid[inj_row : inj_row + bitmask.shape[0], inj_col : inj_col + bitmask.shape[1]] = bitmask

    def run_step(self):
        new_grid = np.zeros((self.grid_rows, self.grid_cols))
        populated: int = 0

        for row_idx, col_idx in np.ndindex(self.grid.shape):
            cell = self.grid[row_idx, col_idx]
            num_neighbours = self.count_cell_neighbours(row_idx, col_idx)

            if cell == 1 and num_neighbours in {2, 3}:
                new_grid[row_idx, col_idx] = 1
            elif cell == 0 and num_neighbours == 3:
                new_grid[row_idx, col_idx] = 1
                populated += 1

        equal_flag: bool = np.array_equal(new_grid, self.grid)
        self.grid = new_grid
        return populated, equal_flag

    def count_cell_neighbours(self, row_idx: int, col_idx: int) -> int:
        neigbour_count: int = 0
        for row_delta in [-1, 0, 1]:
            for col_delta in [-1, 0, 1]:
                if row_delta == col_delta == 0:
                    continue
                neigbour_row_idx = row_idx + row_delta
                neigbour_col_idx = col_idx + col_delta
                if 0 <= neigbour_row_idx < self.grid_rows and 0 <= neigbour_col_idx < self.grid_cols:
                    neigbour_count += self.grid[neigbour_row_idx, neigbour_col_idx]
        return neigbour_count

    def run_from_word(self, word: str):
        self.grid = np.zeros((self.grid_rows, self.grid_cols))
        bitmask = self.word_to_bitmask(word)
        bitmask = self.bitmask_reshape(bitmask)
        self.inject_bitmask_seed(bitmask=bitmask)

        total_score: int = 0
        seen_hashmap = {}
        seen_hashmap[self.hash_array(self.grid)] = 0

        for generation_num in range(self.max_generations):
            populated, equal_flag = self.run_step()
            total_score += populated
            grid_hash = self.hash_array(self.grid)

            if not np.any(self.grid):
                return GameResponse(
                    num_generations=generation_num + 1,
                    score=total_score,
                    stop_reason="extinction",
                )

            if equal_flag:
                return GameResponse(
                    num_generations=generation_num + 1,
                    score=total_score,
                    stop_reason="persistent_state",
                )

            if not grid_hash in seen_hashmap:
                seen_hashmap[grid_hash] = generation_num
                continue

            generation_period = generation_num - seen_hashmap[grid_hash]
            if generation_period < 10:
                return GameResponse(
                    num_generations=generation_num + 1,
                    score=total_score,
                    stop_reason="repeated_pattern",
                )
            seen_hashmap[grid_hash] = generation_num

        return GameResponse(
            num_generations=generation_num + 1,
            score=total_score,
            stop_reason="reached_max_generation",
        )

    def run_from_word_cpp(self, word: str):
        self.grid = np.zeros((self.grid_rows, self.grid_cols), dtype=np.uint8)
        bitmask = self.word_to_bitmask(word)
        bitmask = self.bitmask_reshape(bitmask)
        self.inject_bitmask_seed(bitmask=bitmask)

        flat_grid = np.ascontiguousarray(self.grid).reshape(-1)

        out_generations = ctypes.c_int()
        out_score = ctypes.c_int()
        reason_buffer = ctypes.create_string_buffer(128)

        self.cpp_lib.runFromWord(
            flat_grid,
            self.grid_rows,
            self.grid_cols,
            self.max_generations,
            self.repeat_threshold,
            out_generations,
            out_score,
            reason_buffer,
            ctypes.sizeof(reason_buffer),
        )

        return GameResponse(
            num_generations=out_generations.value,
            score=out_score.value,
            stop_reason=reason_buffer.value.decode(),
        )

    @staticmethod
    def word_to_bitmask(word: str) -> np.ndarray:
        byte_arr = []
        for char in word:
            byte_arr.append(format(ord(char), "08b"))
        return np.array([int(byte) for byte_str in byte_arr for byte in byte_str])

    @staticmethod
    def find_optimal_shape(array: np.ndarray, target_shape: np.shape) -> Tuple[int, int]:
        len_array = len(array)
        factors = [(f, len_array // f) for f in range(1, int(len_array**0.5) + 1) if len_array % f == 0]
        factors = [(row, col) for row, col in factors if row <= target_shape[0] and col <= target_shape[1]]
        optimal_shape = min(factors, key=lambda pair: abs(pair[0] - pair[1]))
        return optimal_shape

    @staticmethod
    def hash_array(array: np.ndarray) -> str:
        return md5(array.tobytes()).hexdigest()

    @staticmethod
    def get_cpp_lib_name():
        if sys.platform.startswith("win"):
            lib_name = "cgol_engine.dll"
        else:
            lib_name = "cgol_engine.so"

        return lib_name
