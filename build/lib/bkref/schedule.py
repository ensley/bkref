import re

import pandas as pd

from . import utils

_BASE_URL = 'https://www.basketball-reference.com'


def _clean_schedule(schedule, playoff_idx, playoff_flag):
    df = schedule.loc[schedule['Game ID'] != 'Playoffs', :].copy()
    df['Game ID'] = df['Game ID'].astype(str).str.extract('/boxscores/(.*).html')
    df['Visitor ID'] = df['Visitor ID'].astype(str).str.extract('/teams/(.{3})/')
    df['Home ID'] = df['Home ID'].astype(str).str.extract('/teams/(.{3})/')
    df['Date'] = pd.to_datetime(df['Date']).dt.date

    if playoff_idx is None:
        df['Playoffs'] = 'Playoffs' if playoff_flag else 'Season'
    else:
        playoff_col = df.columns.get_loc('Playoffs')
        df.iloc[:playoff_idx, playoff_col] = 'Season'
        df.iloc[playoff_idx:, playoff_col] = 'Playoffs'

    df = df.rename(columns={
        'Visitor/Neutral': 'Visitor',
        'PTS': 'Visitor Points',
        'Home/Neutral': 'Home',
        'PTS.1': 'Home Points',
        'overtimes': 'Overtime',
        'Attend.': 'Attendance'
    })
    df = df.drop('box_score_text', axis=1)

    return df


def get_schedule_month(url, playoff_flag):
    soup = utils.scrape_page(url)
    schedule = soup.find(id='schedule')

    if schedule is None:
        return None

    for header in schedule.thead.find_all('th'):
        if header.string is None or header.string.strip() == '':
            header.string = header['data-stat']

    header_gameid = utils.create_tag(soup, 'th', 'Game ID')
    schedule.thead.find(attrs={'data-stat': 'date_game'}).insert_before(header_gameid)

    header_playoffs = utils.create_tag(soup, 'th', 'Playoffs')
    schedule.thead.find(attrs={'data-stat': 'date_game'}).insert_after(header_playoffs)

    header_visitor_id = utils.create_tag(soup, 'th', 'Visitor ID')
    schedule.thead.find(attrs={'data-stat': 'visitor_team_name'}).insert_before(header_visitor_id)

    header_home_id = utils.create_tag(soup, 'th', 'Home ID')
    schedule.thead.find(attrs={'data-stat': 'home_team_name'}).insert_before(header_home_id)

    playoff_idx = None

    for i, row in enumerate(schedule.find('tbody').find_all('tr')):
        if row.string == 'Playoffs':
            playoff_idx = i
            continue

        box_score = row.find(attrs={'data-stat': 'box_score_text'})
        if box_score is None:
            continue

        box_score_link = box_score.a
        if box_score_link is None:
            continue

        gameid = utils.create_tag(soup, 'td', box_score_link['href'])
        row.find(attrs={'data-stat': 'date_game'}).insert_before(gameid)

        playoffs = utils.create_tag(soup, 'td', '')
        row.find(attrs={'data-stat': 'date_game'}).insert_after(playoffs)

        visitor_id = utils.create_tag(soup, 'td', row.find(attrs={'data-stat': 'visitor_team_name'}).a['href'])
        row.find(attrs={'data-stat': 'visitor_team_name'}).insert_before(visitor_id)

        home_id = utils.create_tag(soup, 'td', row.find(attrs={'data-stat': 'home_team_name'}).a['href'])
        row.find(attrs={'data-stat': 'home_team_name'}).insert_before(home_id)

    df = pd.read_html(str(schedule))[0]
    df = _clean_schedule(df.copy(), playoff_idx, playoff_flag)

    return df


def get_schedule(year=None, league='NBA', url=None):
    if year is not None:
        url = f'{_BASE_URL}/leagues/{league}_{year}_games.html'
    elif url is not None:
        if match := re.search(_BASE_URL + r'/leagues/[a-zA-z]+_(\d{4})_games.html', url):
            year = match.group(1)
        else:
            year = None
    else:
        raise ValueError('Either "year" or "season_url" must be provided')

    soup = utils.scrape_page(url)

    month_links = soup.find(id='content').find(class_='filter').find_all('a')
    urls = [_BASE_URL + btn['href'] for btn in month_links]

    schedules = []
    playoff_flag = False
    for url in urls:
        schedule = get_schedule_month(url, playoff_flag)
        if schedule is not None:
            playoff_flag = (schedule['Playoffs'] == 'Playoffs').any()
            schedules.append(schedule)

    df = pd.concat(schedules, sort=False, ignore_index=True).dropna(subset=['Game ID'])
    df.insert(1, 'Season', year)

    return df


def get_all_schedules():
    soup = utils.scrape_page(_BASE_URL + '/leagues')
    seasons = soup.find(id='stats')
    urls = [(_BASE_URL + cell.a['href']).replace('.html', '_games.html')
            for cell in seasons.find_all('th', class_='left')]

    df = pd.concat([get_schedule(url=url) for url in urls], sort=False)

    return df
