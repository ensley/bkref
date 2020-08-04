import re
from collections import namedtuple

import pandas as pd

from . import utils

Fields = namedtuple('Fields', ['quarter', 'time_remaining', 'team1', 'team2',
                               'action_team1', 'action_team2', 'score_team1', 'score_team2'])


def _clean_pbp_df(df, gameid, team1, team2):
    df.columns = df.columns.droplevel(0)

    records = [None] * len(df)
    q = 1
    prev_record = None

    for i, (_, row) in enumerate(df.iterrows()):
        if row['Time'][-1] == 'Q':
            q = int(row['Time'][0])
            continue
        elif row['Time'][-2:] == 'OT':
            q = 4 + int(row['Time'][0])
            continue
        elif row['Time'] == 'Time':
            continue

        score_split = row['Score'].split('-')
        if len(score_split) == 2:
            score_team1 = int(score_split[0])
            score_team2 = int(score_split[1])
        elif prev_record is None:
            score_team1 = 0
            score_team2 = 0
        else:
            score_team1 = prev_record.score_team1
            score_team2 = prev_record.score_team2

        if match := re.search('(^Start of|^End of)', row['Score']):
            row.iloc[1] = f'{match.group(1)} period'
            row.iloc[5] = f'{match.group(1)} period'

        try:
            fields = Fields(
                quarter=q,
                time_remaining=row['Time'],
                team1=team1,
                team2=team2,
                action_team1=row.iloc[1],
                action_team2=row.iloc[5],
                score_team1=score_team1,
                score_team2=score_team2
            )
        except ValueError:
            print(row)
        else:
            prev_record = fields
            records[i] = fields

    res = pd.DataFrame.from_records([r for r in records if r is not None], columns=Fields._fields)
    res.insert(0, 'Game ID', gameid)
    return res


def _parse_pbp_teams(soup):
    def get_team(link):
        if match := re.search('^/teams/([a-zA-Z]+)/.*', link):
            return match.group(1)
        else:
            return None

    teams = [get_team(team.strong.a['href']) for team in soup.find_all(itemprop='performer')]
    return teams[0], teams[1]


def _parse_pbp_from_html(soup):
    pbp = soup.find(id='pbp')

    for cell in pbp.find_all('td'):
        if links := cell.find_all('a'):
            for a in links:
                if match := re.search(r'^/players/[a-z]/([a-zA-Z0-9]+)\.html$', a['href']):
                    a.string = match.group(1)

    df = pd.read_html(str(pbp))[0]

    return df


def get_pbp(gameid):
    # logger = logging.getLogger(__name__)
    # logger.info(gameid)

    url = f'https://www.basketball-reference.com/boxscores/pbp/{gameid}.html'
    soup = utils.scrape_page(url)
    team1, team2 = _parse_pbp_teams(soup)
    df = _parse_pbp_from_html(soup)
    df = _clean_pbp_df(df, gameid, team1, team2)

    return df
