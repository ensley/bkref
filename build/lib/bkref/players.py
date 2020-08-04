from string import ascii_lowercase

import pandas as pd

from . import utils


def get_players(letter):
    url = f'https://www.basketball-reference.com/players/{letter}/'
    bs = utils.scrape_page(url)
    players = bs.find(id='players')
    header_players = players.thead.tr.find(attrs={'data-stat': 'player'})

    # inject player ID header
    header_player_id = utils.create_tag(bs, 'th', 'Player ID')
    header_players.insert_after(header_player_id)

    # inject active header
    header_active = utils.create_tag(bs, 'th', 'Active')
    header_players.insert_after(header_active)

    for th in players.tbody.find_all('th'):
        # inject player ID cell
        player_id = utils.create_tag(bs, 'td', th['data-append-csv'])
        th.insert_after(player_id)

        # inject active cell
        active = utils.create_tag(bs, 'td', 'Active' if th.strong else 'Inactive')
        th.insert_after(active)

    df = pd.read_html(str(players))[0]
    df = df.set_index('Player ID')

    # do some cleaning
    df['Hall of Famer'] = df['Player'].str.endswith('*')
    df['Height (in)'] = df['Ht'].str.split('-').apply(lambda x: 12*int(x[0]) + int(x[1]))
    df['Birth Date'] = pd.to_datetime(df['Birth Date'])

    return df


def get_all_players():
    return pd.concat([get_players(letter) for letter in ascii_lowercase])
