import click as click
import pandas as pd

import bkref


@click.group()
def cli():
    """A tool to scrape data from Basketball Reference."""
    pass


@cli.command()
@click.option('-l', '--letter', type=str, help='First letter of surname')
@click.argument('filename', type=click.Path(dir_okay=False, writable=True),
                default='data/players.csv')
def players(letter, filename):
    """Download a set of player data.

    The data will be written to FILENAME ("data/players.csv" by default). A single
    letter may be provided, and only players whose surnames start with that letter
    will be scraped. This mirrors Basketball Reference's structure of having one letter's
    worth of players per HTML page, e.g. https://www.basketball-reference.com/players/j/.
    If no letter is provided, all players will be scraped.
    """
    if letter is None:
        df = bkref.get_all_players()
    else:
        df = bkref.get_players(letter)

    df.to_csv(filename)


@cli.command()
@click.option('-s', '--season', type=int, help='Season whose games will be scraped')
@click.argument('filename', type=click.Path(dir_okay=False, writable=True),
                default='data/schedule.csv')
def schedule(season, filename):
    """Download a set of game information.

    The data will be written to FILENAME ("data/schedule.csv" by default). A single
    season may be provided, in which case only games played during that season will be
    scraped. If no season is provided, all available seasons will be scraped.
    """
    if season is None:
        df = bkref.get_all_schedules()
    else:
        df = bkref.get_schedule(season)

    df.to_csv(filename, index=False)


@cli.command()
@click.option('-s', '--season', type=int, help='Season whose box scores will be scraped')
@click.argument('filename', type=click.Path(dir_okay=False, writable=True))
def boxscores(season, filename):
    """Download a season's box scores.

    The data will be written to FILENAME (no default). A single season must be provided.
    This generally takes about an hour to pull an entire season's worth of box scores.
    """
    if season is None:
        click.echo('Season not specified.')
    click.echo(f'Getting schedule for the {season} season')
    sched = bkref.get_schedule(season)
    boxes = []

    schedule_iterator = sched[['Game ID', 'Visitor ID', 'Home ID']].itertuples(index=False)
    with click.progressbar(schedule_iterator,
                           length=len(sched),
                           label='Getting box scores...',
                           item_show_func=lambda x: x[0] if x else '') as rows:
        for row in rows:
            box = bkref.get_box_score(*row)
            boxes.append(box)

    df = pd.concat(boxes, sort=False)
    df.to_csv(filename, index=False)


@cli.command()
@click.option('-s', '--season', type=int, help='Season whose play-by-play data will be scraped')
@click.argument('filename', type=click.Path(dir_okay=False, writable=True))
def pbp(season: int, filename: click.Path) -> None:
    """Download a season's play-by-play data.

    The data will be written to FILENAME (no default). A single season must be provided.
    This generally takes about ten minutes to pull an entire season's worth of play-by-play
    reports.
    """
    if season is None:
        click.echo('Season not specified.')
    click.echo(f'Getting schedule for the {season} season')
    sched = bkref.get_schedule(season)
    boxes = []

    with click.progressbar(sched['Game ID'],
                           label='Getting play-by-play reports...',
                           item_show_func=lambda x: x if x else '') as gameids:
        for gameid in gameids:
            box = bkref.get_pbp(gameid)
            boxes.append(box)

    df = pd.concat(boxes, sort=False)
    df.to_csv(filename, index=False)


if __name__ == '__main__':
    cli()
