import pandas as pd

from . import utils


def _parse_box_score_from_html(soup):
    box = soup.find('table')

    header_row = None

    for row in box.thead.find_all('tr'):
        if 'over_header' in row.get('class', []):
            row.decompose()
        else:
            header_row = row

    header_player_id = utils.create_tag(soup, 'th', 'Player ID')
    header_row.find('th').insert_before(header_player_id)

    for header in header_row:
        if header.has_attr('data-stat'):
            header.string = header['data-stat']

    for row in box.tbody.find_all('tr'):
        if 'thead' in row.get('class', []):
            row.decompose()
            continue

        player = row.find(attrs={'data-stat': 'player'})
        player_id = utils.create_tag(soup, 'th', player['data-append-csv'])
        player.insert_before(player_id)

    if box.tfoot:
        box.tfoot.decompose()

    df = pd.read_html(str(box), na_values=['Did Not Play', 'Did Not Dress', 'Not With Team'])[0]

    return df


def parse_box_score(gameid, teamid, boxtype):
    url = f"https://widgets.sports-reference.com/wg.fcgi?css=1&site=bbr&url=%2Fboxscores%2F{gameid}.html" \
          f"&div=div_box-{teamid}-game-{boxtype}"
    soup = utils.scrape_page(url)
    return _parse_box_score_from_html(soup)


def stitch_box_scores(gameid, teamid1, teamid2, boxtype):
    teams = [teamid1, teamid2]
    boxes = [parse_box_score(gameid, t, boxtype) for t in teams]
    return pd.concat(boxes, keys=teams, names=['Team ID']).reset_index(level=0)


def get_box_score(gameid, teamid1, teamid2):
    # logger = logging.getLogger(__name__)
    # logger.info(gameid)
    basic = stitch_box_scores(gameid, teamid1, teamid2, 'basic')
    advanced = stitch_box_scores(gameid, teamid1, teamid2, 'advanced')
    box = basic.merge(advanced, how='outer').dropna(subset=['mp'])

    box = box.convert_dtypes().drop(['fg_pct', 'fg3_pct', 'ft_pct'], axis=1)
    box.insert(0, 'Game ID', gameid)

    return box
