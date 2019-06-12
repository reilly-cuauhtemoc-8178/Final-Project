#! /usr/bin/env python3
"""
Module to test Summoner methods.
Note - VSCode had issues finding pytest test files while writing this.
Currently unsolved.
"""
from summoner_container import Summoner
import pytest


@pytest.mark.parametrize("input", ["Yassuo"])
def test_initialize_summoner(monkeypatch, input):
    mark_gen = (i for i in input)
    monkeypatch.setattr('builtins.input', lambda x: next(mark_gen))
    test = Summoner()
    assert type(test) == "__main__.Summoner"

def test_handle_bad_url():
    with pytest.raises(requests.exceptions.HTTPError):
        ext = 'b'
        query = test.API_TEST_KEY
        test.handle_request(ext, **query)

@pytest.mark.parametrize("input", ["Cr@nk", "Thirty_One"])
def test_bad_username(monkeypatch, input):
    mark_gen = (i for i in input)
    monkeypatch.setattr('builtins.input', lambda x: next(mark_gen))
    with pytest.raises(ValueError):
        test.get_user_input()

@pytest.mark.parametrize("input", [{"matches":None}])
def test_bad_matchlist(input):
    with pytest.raises(TypeError):
        test.compile_match_list(input, test.API_TEST_KEY)

@pytest.mark.parametrize("input", [{"dog":{1:"d", 2:"o", 3:"g"}}])
def test_flatten_dict(input):
    assert test.flatten_stat_dict(input) == ["dog", 'd', 'o', 'g']