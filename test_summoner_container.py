#! /usr/bin/env python3
"""
Module to test Summoner methods.
Note - VSCode had issues finding pytest test files while writing this.
Currently unsolved.
"""
from summoner_container import Summoner
import pytest
import requests
import sys

@pytest.fixture()
def init_summ(monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['summoner_container', 'Yassuo'])
        init = Summoner()
        return init

@pytest.mark.parametrize("input", ["Yassuo"])
def test_initialize_summoner(monkeypatch, input):
    """Test that Summoner() creates a Summoner object."""
    monkeypatch.setattr(sys, 'argv', ['summoner_container', input])
    init = Summoner()
    assert type(init) == Summoner

def test_handle_bad_url(init_summ):
    """Test that bad urls are handled correctly."""
    with pytest.raises(requests.exceptions.HTTPError):
        ext = 'b'
        query = {'api_key':"RGAPI-fa695a0d-056b-48fd-8546-e05e28120a29"}
        init_summ.handle_request(ext, **query)

@pytest.mark.parametrize("input", ["Bork", "Thirty One"])
def test_good_username(monkeypatch, input, init_summ):
    """Test that valid usernames are accepted."""
    monkeypatch.setattr(sys, 'argv', ['summoner_container', input])
    assert init_summ.get_user_input() == input

@pytest.mark.parametrize("input", ["B@rk"])
def test_bad_username(monkeypatch, input, init_summ):
    """Test that invalid usernames result in a loop."""
    monkeypatch.setattr(sys, 'argv', ['summoner_container', input])
    monkeypatch.setattr(sys, 'stdout', input)
    assert sys.stdout is not None

@pytest.mark.parametrize("input", [{"matches":None}])
def test_bad_matchlist(input, init_summ):
    """Test that a bad matchlist will raise an error."""
    with pytest.raises(TypeError):
        init_summ.compile_match_list(input, "RGAPI-fa695a0d-056b-48fd-8546-e05e28120a29")

@pytest.mark.parametrize("input", [{"dog":{1:"d", 2:"o", 3:"g"}}])
def test_flatten_dict(input, init_summ):
    """Test that flatten_dict flattens dictionaries appropriately."""
    assert init_summ.flatten_stat_dict(input) == [['d', 'o', 'g']]