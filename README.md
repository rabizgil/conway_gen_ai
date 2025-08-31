# Conway Game of Life Chatbot and RESTful service

## Description
This repository contains a working implementation of Conway's Game of Life as a RESTful service.
The service takes a word, converts it into an ASCII bitmap and centers it on a 2D grid.
The service returns max score as the total number of spawned cells, number of generations passed until stable state,
and the reason to stop. <br>

The repository also contains a GenAI chat interface app built with Streamlit.
The agent is created with LangGraph and is able to access the REST service to parse the results basing on user requests.

The project is for educational and personal purposes.

## Approach
* Use python for high-level application work and prototyping and C++ for low-level game engine computations.
* Use FastAPI for the service.
* The C++ game engine library is statically compiled for smooth distribution.
* The C++ game engine library is called with python's ctypes.
* The C++ game engine library takes the grid as a contiguous flattened array for simpler memory handling. Runs a naive implementation iterating per each cell.
* Use Streamlit for smooth chatbot UI prototyping.
* Build a LangGraph chatbot with short-term memory and ability to call the game engine API to get the results. The underlying LLM is gpt-4o-mini.
* Additionally add a tool to generate a specified number of random words and return the results with maximum score.

## Game engine performance benchmarks

The following benchmarks illustrate the optimization achieved by using a C++ backend for the Game of Life engine:

| Grid Size | Python Naive Implementation   | C++ Naive Implementation     | Speedup Factor |
|:---------:|:-----------------------------:|:----------------------------:|:--------------:|
| 50x50     | 2.84 s &plusmn; 0.04 s        | 0.26 s &plusmn; 0.01 s       |        ~11x    |
| 100x100   | 27.5 s &plusmn; 0.44 s        | 2.46 s &plusmn; 0.03 s       |        ~11x    |
| 200x200   | 105.0 s &plusmn; 1.78 s       | 9.63 s &plusmn; 0.11 s       |        ~11x    |

**Note:** Benchmarks measured for 952 generations using the word `'persistent_state'` on a single CPU - 11th Gen Intel(R) Core(TM) i5-11400H @ 2.70GHz.

## How to run locally
* Please install python's UV package manager with `pip install uv`.
* Navigate to the root directory and run `uv sync`. This should install necessary packages and python version.
* Activate created environment via `.\venv\Scripts\activate` on Windows or `source .venv/bin/activate.sh` on Linux.
* Run `uv run run_service.py` and in a separate terminal `uv run run_streamlit_ui.py`.
* Please make sure you
