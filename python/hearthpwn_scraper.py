from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import json

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log('error: Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def log(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)

def top_user_decks(pages):
    """
    Gets the hearthpwn.com urls for pages worth of top-rated user-created decks
    Returns a list of urls
    """
    top_decks = []
    main_url = "https://www.hearthpwn.com/"
    search_url = "decks?filter-deck-tag=1&filter-show-constructed-only=y&filter-show-standard=1&page="
    deck_link_re = re.compile('^\/decks\/[0-9].*')
    for i in range(pages):
        raw_html = simple_get(main_url+search_url+str(i))
        if raw_html is not None:
            html = BeautifulSoup(raw_html, 'html.parser')
            top_decks = get_links(html, deck_link_re, top_decks)
            
        else:
            log("error: top_user_decks simple_get returned None")
    log("Found {0} user decks over {1} pages".format(len(top_decks), pages))
    return top_decks

def top_general_decks():
    """
    Gets the hearthpwn.com urls for pages worth of top-rated generalized meta decks
    Returns a list of urls
    """
    top_decks = []
    main_url = "https://www.hearthpwn.com/"
    page_1_url = "top-decks?page=1&sort=-rating"
    page_2_url = "top-decks?page=2&sort=-rating"
    deck_link_re = re.compile('^\/top-decks\/[0-9].*')
    
    raw_html = simple_get(main_url+page_1_url)
    if raw_html is not None:
        html = BeautifulSoup(raw_html, 'html.parser')
        top_decks = get_links(html, deck_link_re, top_decks)
                
        raw_html = simple_get(main_url+page_2_url)
        if raw_html is not None:
            html = BeautifulSoup(raw_html, 'html.parser')
            top_decks = get_links(html, deck_link_re, top_decks)
            log("Found {0} general decks over {1} pages".format(len(top_decks), 2))
        else:
            log("error: top_general_decks simple_get returned None")
    else:
        log("error: top_general_decks simple_get returned None")
    
    
    return top_decks

def get_links(html, regex, deck_list):
    """
    Parses html, finding all matches of regex for all anchor elements
    appends the hearthpwn.com urls it finds to the deck_list, and returns deck_list
    """
    for link in html.find_all('a'):
        href = str(link.get('href'))
        if regex.match(href):
            deck_list.append(href)
    return deck_list


def card_list(search_url):
    """
    Given a hearthpwn.com deck url, gets the url of each card in the deck
    If two of the same card are in the deck, a duplicate url will be appended to the list
    Returns the list of these urls. 
    """
    card_list = []
    card_link_re = re.compile('^\/cards\/[0-9].*')
    
    main_url = "https://www.hearthpwn.com"
    
    raw_html = simple_get(main_url+search_url)
    if raw_html is not None:
        html = BeautifulSoup(raw_html, 'html.parser')
        for link in html.aside.find_all('a'):
            href = str(link.get('href'))
            if card_link_re.match(href):    
                try:
                    count = int(link['data-count'])
                    if count == 2:
                        card_list.append(href)
                except:
                    log("data-count error. Likely extraneous card. Skipping...")
                    continue
                card_list.append(href)
                #log(href)
    else:
        log("error: card_list simple_get returned None")
    log("Found {0} cards in deck.".format(len(card_list)))
    return card_list


def test_full_card_list():
    deck_list = top_user_decks(2)
    deck_list.extend(top_general_decks())
    full_card_list = []
    for url in deck_list:
        log(url)
        full_card_list.extend(card_list(url))
    #log(full_card_list)
    with open("cards.json", 'w') as cards:
        json.dump(full_card_list, cards)

#card_list("/decks/1140105-up-mill-warlock-top-100-by-illness")
#card_list("/decks/1142643-the-light-wills-it")
test_full_card_list()
