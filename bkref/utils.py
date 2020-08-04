import requests
from bs4 import BeautifulSoup


def create_tag(soup, tag, string):
    el = soup.new_tag(tag)
    el.string = string
    return el


def scrape_page(url):
    r = requests.get(url)
    r.raise_for_status()

    bs = BeautifulSoup(r.text, 'html.parser')
    return bs
