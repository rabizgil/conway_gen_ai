# Conway Game of Life Chatbot and RESTful game service

## Description
This repository contains a working implementation of Conway's Game of Life as a RESTful service.
The service takes a word, converts it into an ASCII bitmap and centers it on a grid.
The service returns max score as the total number of spawned cells, number of generations passed until stable state,
and the reason to stop. <br>

The repository also contains a GenAI chat interface app built with Streamlit.
The agent is created with LangGraph and is able to access the REST service to parse the results basing on user requests.

## Approach
* Read the challenge, think about the project structure. Define mandatory functions. Used ChatGPT for structured options.
* Implement a chatbot interface with Streamlit for easy prototyping and LangGraph for agent-like chatbot. Used ChatGPT to understand some of the errors during debugging.
* Build and validate CGoL game engine. Pretty straigt forward, have not used GenAI.
* Create a FastAPI REST service.
* Link chatbot and RESTful service using LangGraph tools.

## How to run
* Please install python's UV package manager with `pip install uv`.
* Navigate to the root directory and run `uv sync`. This should install necessary packages and python version.
* Activate created environment via `.\venv\Scripts\activate` on Windows or `source .venv/bin/activate.sh` on Linux.
* Run `uv run run_service.py` and in a separate terminal `uv run run_streamlit_ui.py`.
