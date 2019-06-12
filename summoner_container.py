#! /usr/bin/env python3
"""
Container for module containing data for one summoner.

Class contains methods to operate on data.
"""
import argparse
import json
import time
import re
import requests


class Summoner:
    """Contains data for one summoner and methods to calculate return data."""

    bad_connect = False
    API_TEST_KEY = "RGAPI-fa695a0d-056b-48fd-8546-e05e28120a29"
    summoner_in = ""
    static_data = ()

    high_wins_with = []
    high_wins_as = []
    high_wins_against = []
    low_wins_with = []
    low_wins_as = []
    low_wins_against = []
    highest_mastery = []

    def __init__(self):
        """Initialize Summoner object."""
        con = self.check_connection()
        if con is True:
            self.summoner_in = self.get_user_input()
            self.static_data = self.get_static_data()
        else:
            self.bad_connect = True
            return

    def process(self):
        """Call functions used for getting information."""
        api_key = self.API_TEST_KEY
        name = self.summoner_in
        summoner_by_name = self.get_summoner_by_name(name, api_key)
        matchlist_by_summ = self.get_matchlist_by_summoner(name, api_key)
        tmp_file_name = self.compile_match_list(matchlist_by_summ, api_key)
        mastery = self.get_champion_mastery(summoner_by_name[1], api_key)
        matchlist_data = self.get_match_list_data(name, tmp_file_name)
        stat_dict = self.create_stat_dict_2(matchlist_data)
        data_array = self.flatten_stat_dict(stat_dict)
        comp_list = ["wins-as", "wins-with", "wins-against",
                     "losses-as", "losses-with", "losses-against"]
        comp_results = [self.comp_champ_stats(data_array, d)
                        for d in comp_list]
        self.high_wins_as = comp_results[0]
        self.high_wins_with = comp_results[1]
        self.high_wins_against = comp_results[2]
        self.low_wins_as = comp_results[3]
        self.low_wins_with = comp_results[4]
        self.low_wins_against = comp_results[5]
        self.highest_mastery = self.comp_champ_stats(data_array,
                                                     'wins-against',
                                                     mastery)
        self.parse_results()
        return "all clear"

    def handle_request(self, ext, **queries):
        """
        Handle API request.

        Return result if successful. Handle status code otherwise.

        Parameters:
            ext : str
                Riot API request url extension. Appended to 'base.'
            queries : str
                Key-value pairs passed in to form querystring.
        Returns : dict

        """
        base = 'https://na1.api.riotgames.com/lol/'
        querystring = {key: value for key, value in queries.items()}
        url = f"{base}{ext}"
        try:
            request = requests.get(url, params=querystring)
            header = request.headers
            if request.raise_for_status() is None:
                return request.json()
        except requests.exceptions.HTTPError as http_except:
            if request.status_code == 429:
                sleep_time = int(header["Retry-After"])+2
                print(f"Rate limit reached. Resting for {sleep_time} seconds.")
                time.sleep(sleep_time)
                return self.handle_request(ext, **queries)
            print(f"HTTP Error: {http_except}")
            raise requests.exceptions.HTTPError

        except ConnectionError as con_except:
            print(f"Connection Error: {con_except}")
        except requests.exceptions.RequestException as err:
            print(f"Error: {err}")

    def check_connection(self):
        """
        Check connection before proceeding.

        Returns : bool

        """
        ext = "status/v3/shard-data"
        query = {"api_key": self.API_TEST_KEY}
        test_request = self.handle_request(ext, **query)
        if test_request is None:
            print("There was a connection error.")
            connect = False
        else:
            connect = True
        return connect

    @staticmethod
    def get_user_input():
        """
        Prompt user to input name and check for validity.

        Returns : str

        """
        parser = argparse.ArgumentParser()
        parser.add_argument("summoner", type=str, help="Name of summoner")
        args = parser.parse_args()
        name = args.summoner
        name_is_valid = False
        while name_is_valid is False:
            try:
                if re.match(r"^[\w ]+$", name) is not None:
                    if re.match(r".*_.*", name) is None:
                        return name
                    raise ValueError
                raise ValueError
            except ValueError:
                name = input("Name invalid. Please try again: ")

    def get_summoner_by_name(self, summ_name, api_key):
        """
        Get summoner's identifiers by name.

        Parameters:
            summ_name : string
        Returns: tuple
            format : (name : str, summoner_id :
            str, account_id : str, icon : str)

        """
        query = {"api_key": api_key}
        summoner = self.handle_request(f"summoner/v4/summoners/by-name/\
{summ_name}", **query)
        name = summoner['name']
        summoner_id = summoner['id']
        account_id = summoner['accountId']
        current_ver = self.static_data[0]
        icon = f"http://ddragon.leagueoflegends.com/cdn/{current_ver}/img/\
profileicon/{summoner['profileIconId']}.png"
        return (name, summoner_id, account_id, icon)

    def get_matchlist_by_summoner(self, summ_name, api_key):
        """
        Get summoner's games for current season.

        Parameters:
            summ_name : str
            api_key : str

        Returns : dict

        """
        account_id = self.get_summoner_by_name(summ_name, api_key)[2]
        query = {"season": 13, "queue": 400, "api_key": api_key}
        match_list = self.handle_request(f"match/v4/matchlists/by-account/\
{account_id}", **query)
        return match_list

    def compile_match_list(self, matchlist, api_key):
        """
        Compile matches into one json file with detailed data.

        Parameters:
            matchlist : dict

        """
        header = "{\"matches\":["
        closer = "]}"
        breaker = ","
        temp_file_name = "temp_data_file.json"
        with open(temp_file_name, 'w+', encoding="utf-8") as write_file:
            print("Updating stats...")
            write_file.write(header)
            for match in matchlist["matches"][0:100]:
                match_id = match["gameId"]
                query = {"api_key": api_key}
                match_data = self.handle_request(f"match/v4/matches/\
{match_id}", **query)
                write_file.write(json.dumps(match_data))
                if match is not matchlist["matches"][99]:
                    write_file.write(breaker)
            write_file.write(closer)
            print("Stats updated.")

        with open(temp_file_name, 'r', encoding='utf-8') as check:
            test = json.load(check)
            for match in test["matches"]:
                if match is None:
                    print(f"Failure retrieving match {match}")
                    raise TypeError
        return temp_file_name

    @staticmethod
    def get_match_data(game, summoner):
        """
        Get data from match.

        Gets win/loss value, summoner's champion, teammates' champions, and
        opponents' champions.

        Parameters:
            game : dict
            summoner : str

        Returns : tuple

        """
        for summ in game["participantIdentities"]:
            if summ["player"]["summonerName"] == summoner:
                player_id = summ["participantId"]
                player_stats = game["participants"][player_id-1]
                player_team = player_stats["teamId"]
                player_champion = player_stats["championId"]
                player_win = player_stats["stats"]["win"]

        if player_team == 100:
            teammates = [summ for summ in game["participants"][0:5]
                         if summ["participantId"] != player_id]
            opponents = [summ for summ in game["participants"][5:10]]
        else:
            teammates = [summ for summ in game["participants"][5:10]
                         if summ["participantId"] != player_id]
            opponents = [summ for summ in game["participants"][0:5]]

        team = [summoner["championId"] for summoner in teammates]
        enemy = [summoner["championId"] for summoner in opponents]

        return_data = (player_win, player_champion, team, enemy)
        return return_data

    def get_match_list_data(self, summoner, temp_file):
        """
        Make list of results from get_match_data().

        Parameters :
            summoner : str

        Returns : list

        """
        with open(temp_file, 'r', encoding="utf-8") as data:
            matchlist = json.load(data)
            num = summoner
            ret_list = [self.get_match_data(i, num)
                        for i in matchlist["matches"]]
        return ret_list

    def get_champion_mastery(self, summoner_id, api_key):
        """
        Get five highest mastery champions for a summoner.

        Parameters:
            summoner_id : str
            api_key : str

        Returns : list
            [(id, mastery points)]

        """
        ext = f"champion-mastery/v4/champion-masteries/by-summoner/\
{summoner_id}"
        mastery_req = self.handle_request(ext, api_key=api_key)
        mastery = mastery_req
        m_list = [(x["championId"], x["championPoints"]) for x in mastery]
        m_list_2 = sorted(m_list, key=lambda x: x[1], reverse=True)[0:5]
        return m_list_2

    @staticmethod
    def get_static_data():
        """
        Get current version data.

        Retrieves latest version data and matching champion data from static
        data.

        Returns : tuple
            Format : (string, dict)

        """
        base = "https://ddragon.leagueoflegends.com"
        cv_request = requests.get(f"{base}/realms/na.json")
        current_ver = cv_request.json()["v"]
        champ_request = requests.get(f"{base}/cdn/{current_ver}\
/data/en_US/champion.json")
        champion_ids = champ_request.json()
        return current_ver, champion_ids

    @staticmethod
    def get_champion_ids(static_champions):
        """
        Get readable champion IDs.

        Returns : dict

        """
        clist = dict()
        for champ in static_champions["data"]:
            key = str(static_champions["data"][champ]["key"])
            name = static_champions["data"][champ]["id"]
            clist[key] = name
        return clist

    @staticmethod
    def stat_entry(stats, update=None):
        """
        Update stat entry.

        Parameters:
            stats : tuple
                (self, ally, enemy, win_self, win_with, win_against)
            update : dict

        Returns : dict

        """
        if update is None:
            stat_entry = {"id": stats[0],
                          "played_as": stats[1],
                          "same_team": stats[2],
                          "other_team": stats[3],
                          "wins_as": stats[4],
                          "wins_with": stats[5],
                          "wins_against": stats[6]}
            return stat_entry

        ret_update = update
        for num, key in enumerate(ret_update):
            if num > 0:
                ret_update[key] += stats[num]
        return ret_update

    def create_stat_dict_2(self, list_of_tuples):
        """
        Create dict containing data for each champion.

        Parameters:
            list_of_tuples : tuple

        Returns : dict

        """
        stat_dict = dict()
        for match in list_of_tuples:
            if match[0] is True:
                if match[1] not in stat_dict:
                    stat_dict[match[1]] = self.stat_entry((match[1],
                                                           1, 0, 0, 1, 0, 0))
                stat_dict[match[1]] = self.stat_entry((match[1],
                                                       1, 0, 0, 1, 0, 0),
                                                      stat_dict[match[1]])
                for summ_2 in match[2]:
                    if summ_2 not in stat_dict:
                        stat_dict[summ_2] = self.stat_entry((summ_2,
                                                             0, 1, 0, 0, 1, 0))
                    stat_dict[summ_2] = self.stat_entry((summ_2,
                                                         0, 1, 0, 0, 1, 0),
                                                        stat_dict[summ_2])
                for summ_3 in match[3]:
                    if summ_3 not in stat_dict:
                        stat_dict[summ_3] = self.stat_entry((summ_3,
                                                             0, 0, 1, 0, 0, 1))
                    stat_dict[summ_3] = self.stat_entry((summ_3,
                                                         0, 0, 1, 0, 0, 1),
                                                        stat_dict[summ_3])
            else:
                if match[1] not in stat_dict:
                    stat_dict[match[1]] = self.stat_entry(([match[1]],
                                                           1, 0, 0, 0, 0, 0))
                stat_dict[match[1]] = self.stat_entry(([match[1]],
                                                       1, 0, 0, 0, 0, 0),
                                                      stat_dict[match[1]])
                for summ_2 in match[2]:
                    if summ_2 not in stat_dict:
                        stat_dict[summ_2] = self.stat_entry((summ_2,
                                                             0, 1, 0, 0, 0, 0))
                    stat_dict[summ_2] = self.stat_entry((summ_2,
                                                         0, 1, 0, 0, 0, 0),
                                                        stat_dict[summ_2])
                for summ_3 in match[3]:
                    if summ_3 not in stat_dict:
                        stat_dict[summ_3] = self.stat_entry((summ_3,
                                                             0, 0, 1, 0, 0, 0))
                    stat_dict[summ_3] = self.stat_entry((summ_3,
                                                         0, 0, 1, 0, 0, 0),
                                                        stat_dict[summ_3])
        return stat_dict

    @staticmethod
    def flatten_stat_dict(stat_dict):
        """
        Flatten dictionary of champion stats into a 2D array.

        Parameters:
            stat_dict : dict
        Returns : list

        """
        keys = list(stat_dict.keys())
        champ_array = [list(stat_dict[i].values()) for i in keys]
        return champ_array

    @staticmethod
    def comp_champ_stats(champion_array, sort_by, compare=None):
        """
        Operate on 2D array of champion statistics, returning based on key.

        Parameters:
            champion_array : list
                2D array containing statistics.
            compare : list
                List containing ids of highest mastery champions.
            sort_by : str
                Key indicating what to return.
        Returns : list

        """
        if compare is not None:
            cmp_array = list()
            for c_tuple in compare:
                for d_tuple in champion_array:
                    if c_tuple[0] == d_tuple[0]:
                        cmp_array.append(d_tuple)
            return sorted(cmp_array, key=lambda x: x[6], reverse=True)
        count = 5
        if sort_by == "wins-as":
            team, rev_value, count = (1, True, 1)
        if sort_by == "wins-with":
            team, rev_value = (2, True)
        if sort_by == "wins-against":
            team, rev_value = (3, True)
        if sort_by == "losses-as":
            team, rev_value = (1, False)
        if sort_by == "losses-with":
            team, rev_value = (2, False)
        if sort_by == "losses-against":
            team, rev_value = (3, False)

        ret_list = [x for x in champion_array if x[team] >= count]
        ret_list_2 = sorted(ret_list,
                            key=lambda x: x[team],
                            reverse=rev_value)[0:5]

        return ret_list_2

    def parse_results(self):
        """Interpret results to be readable."""
        champ_ids = self.static_data[1]
        id_dict = self.get_champion_ids(champ_ids)
        print("Most frequently played as:")
        a_1 = [(id_dict[str(x[0])], f"{x[1]} games")
               for x in self.high_wins_as]
        print(a_1)

        print("Most frequently played with:")
        b_2 = [(id_dict[str(x[0])], f"{x[2]} games")
               for x in self.high_wins_with]
        print(b_2)

        print("Most frequently played against:")
        c_3 = [(id_dict[str(x[0])], f"{x[3]} games")
               for x in self.high_wins_against]
        print(c_3)

        print("Least frequently played as:")
        d_4 = [(id_dict[str(x[0])], f"{x[4]} games") for x in self.low_wins_as]
        print(d_4)

        print("Least frequently played with:")
        e_5 = [(id_dict[str(x[0])], f"{x[5]} games")
               for x in self.low_wins_with]
        print(e_5)

        print("Least frequently played against:")
        f_6 = [(id_dict[str(x[0])], f"{x[6]} games")
               for x in self.low_wins_against]
        print(f_6)


if __name__ == "__main__":
    INSTANCE = Summoner()
    print(INSTANCE.process())
