#!/usr/bin/env python3 or #!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys, requests, datetime, string
from shutil import rmtree
from pathlib import Path
from lxml import html
from time import sleep
from version import __version__

def title_to_filename(title):
    valid_chars = string.ascii_letters + string.digits + '-_.() '
    translate_dict = {ord(u'ü'): u'ue', ord(u'ä'): u'ae', ord(u'ö'): u'oe', ord(u' '): u'_'}
    filename = title.translate(translate_dict)
    return ''.join(c for c in filename if c in valid_chars)


def main(podcast_url, output_dir):
    # get site content
    print('Podcast URL: {0}'.format(podcast_url))
    try:
        page = requests.get(podcast_url)
    except requests.exceptions.ProxyError as e:
        print('ERROR: could not connect to proxy ({})'.format(e.args[0].reason.args[1]))
        return 1
    except requests.exceptions.RequestException as e:
        print('Error occured: {}'.format(e))
        return 1
    if (page.status_code != 200) or (page.reason.upper() != 'OK'):
        print('Problem: Could not get data from URL')
        return 1

    # check output dir
    print('Output dir: {0}'.format(output_dir.as_posix()))
    if not output_dir.exists():
        output_dir.mkdir()
    else:
        rmtree(output_dir)
        output_dir.mkdir()

    # parse site content and get audio files
    tree = html.fromstring(page.content)
    dl_links = tree.xpath('//a[@class="ico ico_download"]')
    total = len(dl_links)
    print('Total podcasts for download: {0}'.format(total))
    if not total:
        print('Problem: No download links found via XPath')
        return 1

    # process single episodes
    for n,dl in enumerate(dl_links):
        print("({0}/{1}) ".format(n+1, total), end="")
        article = dl.getparent()
        # airdate
        airdate_str = article.xpath('./time[@class="onAirInfo"]')[0].attrib['datetime']
        airdate = datetime.datetime.strptime(airdate_str, '%Y-%m-%dT%H:%M')
        # title
        title = article.xpath('./h3/span[@class="manualteasertitle"]/text()')
        if title:
            title = title[0]
        else:
            title = 'kein Titel'
        print(airdate.strftime('%Y-%m-%d') + ' ' + title)
        # filenames + output dir
        fname_podcast = title_to_filename('{0} {1}'.format(airdate.strftime('%Y-%m-%d'), title))
        fname_info = '{0}_Info'.format(airdate.strftime('%Y-%m-%d'))
        output_podcast = Path(output_dir, airdate.strftime('%Y-%m'))
        if not output_podcast.exists():
            output_podcast.mkdir(parents=True)
        # shorttext
        shorttext = article.xpath('./div[@class="manualteasershorttext"]/p/text()')
        if shorttext:
            shorttext = shorttext[0]
        else:
            shorttext = 'nicht vorhanden'
        # download podcast and save to output
        podcast_suffix = Path(dl.attrib['href']).suffix
        print('download ... ', end="")
        podcast_data = requests.get(dl.attrib['href'])
        print('done, write to output ... ', end="")
        with open(Path(output_podcast, fname_podcast).with_suffix(podcast_suffix), "wb") as podcast_file:
            podcast_file.write(podcast_data.content)
        print('done')
        # write info file
        with open(Path(output_podcast,fname_info).with_suffix('.txt'), "w") as text_file:
            text_file.write('Titel: {0}\n'.format(title))
            text_file.write('Datum: {0}\n'.format(airdate.strftime('%Y-%m-%d %H-%M')))
            text_file.write('Beschreibung: {0}'.format(shorttext))
    return 0


if __name__ == "__main__":
    versionstr = 'Ohrenbaeren Podcast Load v{0}'.format(__version__)
    print(versionstr)
    import argparse
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description=versionstr)
    parser.add_argument("--output-dir", '-o', help="Specify output dir", metavar='<PATH>', type=Path,
                        default=Path('~/Desktop/ohrenbaer_podcast').expanduser())
    parser.add_argument("--podcast-url", '-u', help="Specify URL to podcast site with download links", metavar='<URL>',
                        type=str, default='https://www.ohrenbaer.de/podcast/podcast.html')
    parser.add_argument('--version', '-v', action='version', version='%(prog)s v{0}'.format(__version__))
    args = parser.parse_args()
    ret = main(podcast_url=args.podcast_url, output_dir=args.output_dir)
    if ret:
        sleep(4)
    sys.exit(ret)
