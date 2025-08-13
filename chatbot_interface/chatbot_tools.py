import os
import random

import requests
from langchain_core.tools import tool
from nltk.corpus import words
from nltk.data import path

API_URL = "http://127.0.0.1:8000/cgol/game"
NLTK_DATA = ".\\nltk_data"
path.append(NLTK_DATA)


def request_game_result(payload: dict) -> str | dict:
    response = requests.post(API_URL, json=payload, timeout=15)
    try:
        response.raise_for_status()
        response = response.json()
    except requests.exceptions.HTTPError as e:
        error_str = f"HTTP Error: {e}"
        response = {"num_generations": 0, "score": 0, "stop_reason": error_str}
    except Exception as e:
        error_str = f"Error: {e}"
        response = {"num_generations": 0, "score": 0, "stop_reason": error_str}

    return response

@tool
def get_game_result(word: str):
    """
    Call to run Conway simulation and get results for the given word.

    Args:
        word (str): The word to pass to Conway tool

    Returns:
        dict: Dictionary with keys "num_generations", "score" and "stop_reason"
    """
    payload = {"word": word}
    response = request_game_result(payload)
    return response

@tool
def get_results_for_random_words(n_words: int):
    """
    Call to generate specified number of random words (n_words) with nltk.corpus.words,
    run Conway simulation for each word and return the result for the best score.

    Args:
        n_words (int): The number of randomly generated words

    Returns:
        dict: Dictionary with keys "word", "num_generations", "score" and "stop_reason"
    """
    words_list = random.choices(words.words(), k=n_words)
    best_score = 0
    best_response = None

    for word in words_list:
        payload = {"word": word}
        response = request_game_result(payload)

        if best_response is None:
            best_score = response["score"]
            best_response = response | {"word": word}
        if response["score"] > best_score:
            best_score = response["score"]
            best_response = response | {"word": word}

    return best_response
