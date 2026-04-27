import pytest
import sys
import os

# Add src to sys.path to allow importing from src.utils.cards
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.cards import calculate_score

def test_calculate_score_no_aces():
    cards = [{'rank': '10', 'suit': '♠'}, {'rank': 'K', 'suit': '♥'}]
    assert calculate_score(cards) == 20

def test_calculate_score_single_ace_below_21():
    cards = [{'rank': 'A', 'suit': '♠'}, {'rank': '9', 'suit': '♥'}]
    assert calculate_score(cards) == 20

def test_calculate_score_single_ace_above_21():
    cards = [{'rank': 'A', 'suit': '♠'}, {'rank': '9', 'suit': '♥'}, {'rank': 'K', 'suit': '♣'}]
    assert calculate_score(cards) == 20

def test_calculate_score_multiple_aces():
    cards = [{'rank': 'A', 'suit': '♠'}, {'rank': 'A', 'suit': '♥'}]
    assert calculate_score(cards) == 12

def test_calculate_score_multiple_aces_complex():
    # A, A, 9 -> 11 + 1 + 9 = 21
    cards = [{'rank': 'A', 'suit': '♠'}, {'rank': 'A', 'suit': '♥'}, {'rank': '9', 'suit': '♣'}]
    assert calculate_score(cards) == 21

def test_calculate_score_multiple_aces_more_complex():
    # A, A, A, 9 -> 11 + 1 + 1 + 9 = 22 -> 1 + 1 + 1 + 9 = 12
    cards = [{'rank': 'A', 'suit': '♠'}, {'rank': 'A', 'suit': '♥'}, {'rank': 'A', 'suit': '♦'}, {'rank': '9', 'suit': '♣'}]
    assert calculate_score(cards) == 12

def test_calculate_score_blackjack():
    cards = [{'rank': 'A', 'suit': '♠'}, {'rank': 'J', 'suit': '♥'}]
    assert calculate_score(cards) == 21

def test_calculate_score_empty_hand():
    assert calculate_score([]) == 0

def test_calculate_score_all_aces():
    # A, A, A, A -> 11 + 1 + 1 + 1 = 14
    cards = [{'rank': 'A', 'suit': '♠'}, {'rank': 'A', 'suit': '♥'}, {'rank': 'A', 'suit': '♦'}, {'rank': 'A', 'suit': '♣'}]
    assert calculate_score(cards) == 14
