# vim: set ts=4 sts=4 sw=4 et ai:
import json
import re
import sys
import praw

import click
import pkg_resources
from ebooklib import epub

from reddit2epub.reddit2epubLib import get_chapters_from_anchor, create_book_from_chapters


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    infos = {
        "version": pkg_resources.get_distribution("reddit2epub").version
    }
    click.echo(json.dumps(infos))
    ctx.exit()


@click.command()
@click.option('input_url', '--input', '-i', required=True,
              help='The url of an arbitrary chapter of the series you want to convert')
@click.option('output_filename', '--output', '-o', default="",
              help='The filename of the output epub. Defaults to the first chapter title.')
@click.option('--overlap', default=2, help='How many common words do the titles have at the beginning.')
@click.option('--all-reddit/--no-all-reddit', default=False, help='Search over all reddit. '
                                                                  'Meant for stories which span subreddits')
@click.option('--client_id', '-c', required=True,
              help='The API clientId to use.')
@click.option('--api_secret', '-s', required=True,
              help='The API secret to use.')
@click.option('--version', help="Print version information and exit.", is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
def main_cli(input_url: str, overlap: int, output_filename, all_reddit, client_id: str, api_secret: str):
    reddit = praw.Reddit(client_id=client_id, client_secret=api_secret,
            user_agent='script:reddit2epub:omnigrok (by u/omnigrok, fork of mircohacker/reddit2epub)')

    author, selected_submissions, search_title = get_chapters_from_anchor(input_url, reddit, overlap, all_reddit)

    len_subs = len(selected_submissions)
    print("Total number of found posts with title prefix '{}' in subreddit: {}".format(search_title, len_subs))

    if len_subs == 1:
        raise Exception("No other chapters found, which share the first {} words with other posts from this "
                        "author in this subreddit.".format(overlap))
    elif len_subs == 0:
        raise Exception("No text chapters found")

    elif len_subs >= 200:
        print("Got more than 200 submissions from author in this subreddit :-O. "
              "It may be possible that old chapters are not included.",
              file=sys.stderr)

    # set metadata
    book_id = selected_submissions[-1].id
    book_title = selected_submissions[-1].title
    book_author = author.name

    # Build the ebook
    book = create_book_from_chapters(book_author, book_id, book_title, reversed(selected_submissions))

    # replace all non alphanumeric chars through _ for filename sanitation
    if output_filename:
        file_name = output_filename
    else:
        file_name = (re.sub('[^0-9a-zA-Z]+', '_', book_title) + ".epub").strip("_OC")

    # write to the file
    epub.write_epub(file_name, book, {})


if __name__ == '__main__':
    main_cli()
