#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO error handling ueberall??

import sys, requests, datetime, string, os
from version import __version__
from shutil import rmtree
from pathlib import Path
from urllib.parse import urljoin
from lxml import html
from time import sleep
from colorama import Fore as Foreground, init, Style as Fontstyle
init()  # required to use colorama on windows


class Col:
    OK = Foreground.GREEN + Fontstyle.BRIGHT
    WARN = Foreground.YELLOW + Fontstyle.BRIGHT
    ERR = Foreground.RED + Fontstyle.BRIGHT
    OFF = Foreground.RESET + Fontstyle.RESET_ALL


def print_error(message):
    print(Col.ERR + 'Error: ' + Col.OFF + message)


def print_warning(message):
    print(Col.WARN + 'Warning: ' + Col.OFF + message)


def title_to_filename(title, replace=True):
    """
    Converts the title of a audio file into a valid filename

    :param str title: The title of a audio file
    :param bool replace: Replace blanks by underline
    :return: The valid filename for the audio file
    :rtype: str
    """
    valid_chars = string.ascii_letters + string.digits + '-_.() '
    # translate_dict = {ord(u'ü'): u'ue', ord(u'ä'): u'ae', ord(u'ö'): u'oe', ord(u' '): u'_'}
    translate_dict = {ord(u'ü'): u'ue', ord(u'ä'): u'ae', ord(u'ö'): u'oe'}
    if replace:
        translate_dict[ord(u' ')] = u'_'
    filename = title.translate(translate_dict)
    return ''.join(c for c in filename if c in valid_chars)


def print_substep(message):
    """
    Prints out the message without a newline at the end and will flush it to the console directly

    :param str message: Message you want to print
    """
    print(message, end="")
    sys.stdout.flush()


def process_story(output_dir, url):
    try:
        page = requests.get(url)
    except:
        print_error('not handled - ' + sys.exc_info()[0])
        return 1
    if (page.status_code != 200) or (page.reason.upper() != 'OK'):
        print_error('Could not get data from URL')
        return 1
    tree = html.fromstring(page.content)
    section = tree.xpath('//div[@id="main"]//section[contains(@class,"teaserbox") and contains(@class,"doctypeuebersicht")]')
    if section:
        section = section[0]
    else:
        print('\t' + Col.ERR + 'No podcasts available' + Col.OFF)
        return 0
    total_podcasts = section.xpath('./article[contains(@class,"doctypemanualteaser")]').__len__()
    articles_audiofiles = section.xpath('./article[contains(@class,"doctypeaudio")]')
    total_files = len(articles_audiofiles)
    if total_files == 0:
        print('\t' + Col.ERR + 'No audio files available' + Col.OFF)
        return 0
    elif total_podcasts > total_files:
        print('\t' + Col.WARN + '{0} of {1} files available'.format(total_files, total_podcasts)+ Col.OFF)
    else:
        print('\t' + Col.OK + 'All files available' + Col.OFF)
    output_dir.mkdir(parents=True)
    output_dir = output_dir.resolve()
    # process single episodes
    for n, article in enumerate(articles_audiofiles):
        # download link
        dl = article.xpath('./a[@class="ico ico_download"]')[0].attrib['href']
        # airdate
        airdate_str = article.xpath('./time[@class="onAirInfo"]')[0].attrib['datetime']
        airdate = datetime.datetime.strptime(airdate_str, '%Y-%m-%dT%H:%M')
        # title
        title = article.xpath('./h3/span[@class="manualteasertitle"]/text()')
        if title:
            title = title[0]
        else:
            title = 'kein Titel'
        print_substep('\t' + airdate.strftime('%Y-%m-%d') + ' ' + title + ': ')
        # filenames + output dir
        fname_podcast = title_to_filename('{0} {1}'.format(airdate.strftime('%Y-%m-%d'), title))
        fname_info = '{0}_Info'.format(airdate.strftime('%Y-%m-%d'))
    #     output_podcast = Path(output_dir, airdate.strftime('%Y-%m'))
    #     if not output_podcast.exists():
    #         output_podcast.mkdir(parents=True)
    #     # shorttext
    #     shorttext = article.xpath('./div[@class="manualteasershorttext"]/p/text()')
    #     if shorttext:
    #         shorttext = shorttext[0]
    #     else:
    #         shorttext = 'nicht vorhanden'
        # download podcast and save to output
        podcast_suffix = Path(dl).suffix
        print_substep('download audio ... ')
        podcast_data = requests.get(dl)
        print_substep(Col.OK + 'done   ' + Col.OFF)
        print_substep('write to output ... ')
        with open(Path(output_dir, fname_podcast).with_suffix(podcast_suffix).as_posix(), "wb") as podcast_file:
            podcast_file.write(podcast_data.content)
        print(Col.OK + 'done' + Col.OFF)
    #     # write info file
    #     with open(Path(output_podcast,fname_info).with_suffix('.txt').as_posix(), "w") as text_file:
    #         text_file.write('Titel: {0}\n'.format(title))
    #         text_file.write('Datum: {0}\n'.format(airdate.strftime('%Y-%m-%d %H-%M')))
    #         text_file.write('Beschreibung: {0}'.format(shorttext))
    return 1


def process_year(output_dir, url):
    try:
        page = requests.get(url)
    except:
        print_error('not handled - ' + sys.exc_info()[0])
        return 1
    if (page.status_code != 200) or (page.reason.upper() != 'OK'):
        print_error('Could not get data from URL')
        return 1
    tree = html.fromstring(page.content)
    articles_stories = tree.xpath('//div[@id="main"]//article[contains(@class,"manualteaser")]')
    stories = dict()
    if not articles_stories:
        print_error('Could not get links to stories')
        return 1
    else:
        for n,a in enumerate(articles_stories):
            story_title = a.xpath('./h3/a[@class="sendeplatz"]/span[@class="manualteasertitle"]/text()')[0]
            story_url = a.xpath('./h3/a[@class="sendeplatz"]')[0].attrib['href']
            stories[n+1] = {'title': story_title, 'url': urljoin(url, story_url)}
    total_stories = len(stories)
    print('Total number of stories: {0}'.format(total_stories))

    for n, atr in enumerate(stories):
        data = stories[atr]
        print('({0}/{1}) {2}'.format(n + 1, total_stories, data['title']))
        process_story(output_dir=Path(output_dir, data['title']), url=data['url'])
    return 0


def main(podcast_url, output_dir, year):
    # get site content
    print('Podcast URL: {0}'.format(podcast_url))
    try:
        page = requests.get(podcast_url)
    except requests.exceptions.ProxyError as e:
        print_error('could not connect to proxy ({})'.format(e.args[0].reason.args[1]))
        return 1
    except requests.exceptions.RequestException as e:
        print_error(e)
        return 1
    if (page.status_code != 200) or (page.reason.upper() != 'OK'):
        print_error('Could not get data from URL')
        return 1

    # check output dir
    print('Output dir: {0}'.format(output_dir.as_posix()))
    try:
        if not output_dir.exists():
            output_dir.mkdir()
        else:
            rmtree(output_dir.as_posix())
            output_dir.mkdir()
    except PermissionError as e:
        print_error('Could not write to given output-dir. Please provide a path with write-access')
        return 1
    except:
        print_error('not handled - ' + sys.exc_info()[0])
        return 1
    output_dir = output_dir.resolve()
    # parse years from archive
    tree = html.fromstring(page.content)
    article_years = tree.xpath('//div[@id="main"]//article[contains(@class,"manualteaser")]')
    years = dict()
    if not article_years:
        print_error('Could not get links to years in archive')
        return 1
    # elif not year:
        # TODO: implement handling specific year
    else:
        for a in article_years:
            key = a.xpath('.//div[@class="teasertext"]/h3/a[@class="uebersicht"]/span[@class="manualteasertitle"]/text()')[0]
            val = a.xpath('.//div[@class="teasertext"]/h3/a[@class="uebersicht"]')[0].attrib['href']
            years[key] = urljoin(podcast_url, val)

    total_years = len(years)
    print('Total number of years to search: {0}'.format(total_years))
    if not total_years:
        print_warning('No years in archive found')
        return 1
    # process years
    for n, y_str in enumerate(years):
        print('\n[{0}/{1}] Year: {2}'.format(n+1, total_years, y_str))
        process_year(output_dir=output_dir.joinpath(y_str), url=years[y_str])
    return 0


if __name__ == "__main__":
    versionstr = 'Ohrenbaeren Podcast Load v{0}'.format(__version__)
    print(versionstr)
    import argparse
    parser = argparse.ArgumentParser(description=versionstr, prog='opl')
    parser.add_argument('-o', '--output', metavar='<PATH>', default=Path(Path.cwd(), 'ohrenbaer_podcast'), type=Path,
                        help="Path to dir where audio files will be stored")
    parser.add_argument('-y', '--year', metavar='<YEAR>', default=None, type=int,
                        help="Specific year which is checked in the arcive for available audio files")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s v{0}'.format(__version__))
    args = parser.parse_args()
    ret = main(podcast_url='https://www.ohrenbaer.de/sendung/jahresarchive/uebersicht-jahresarchive.html',
               output_dir=args.output, year=args.year)
    if ret:
        sleep(4)
    sys.exit(ret)
