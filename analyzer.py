"""Achievement Streak Analyzer.

Given two TA (trueachievements.com) gamer id's produce an HTML report
comparing the achievement streaks of those two gamers.
"""


import sys
from collections import namedtuple
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import requests
from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
from lxml import html


class Streak(namedtuple("Streak", ["start_date", "length", "achievement_count"])):
    """Basic data class representing an achievement streak."""

    MIN_LENGTH = 30
    MIN_COUNT = 60

    @property
    def weighted_average(self):
        if self.length < self.MIN_LENGTH or self.achievement_count < self.MIN_COUNT:
            return -0.00001
        return (1.02 * self.achievement_count) / (self.length * 0.98)

    @property
    def filtered_average(self):
        if self.length < self.MIN_LENGTH or self.achievement_count < self.MIN_COUNT:
            return -0.000_001
        return self.average_per_day

    @property
    def average_per_day(self):
        return self.achievement_count / self.length

    @property
    def end_date(self):
        return self.start_date + timedelta(days=self.length)

    def __str__(self):
        date_fmt_string = "%B %-d, %Y"
        start_formatted = self.start_date.strftime(date_fmt_string)
        end_formatted = self.end_date.strftime(date_fmt_string)
        date_part = f"{start_formatted} to {end_formatted}".ljust(40, " ")
        return (
            f"{date_part}: {self.achievement_count:,} achievements "
            f"in {self.length:,} days (avg: {self.average_per_day:.3f} "
            f"weighted: {self.weighted_average:.3f})"
        )


def parse_it(html_content):
    """Parse the the HTML content of a TA streaks page."""

    def _process_row(row):
        tds = row.xpath(".//td")
        if not tds:
            return None
        return Streak(
            datetime.strptime(tds[0].text_content(), "%d %b %Y").date(),
            int(tds[1].text_content().replace(",", "")),
            int(tds[2].text_content().replace(",", "")),
        )

    try:
        tree = html.fromstring(html_content)
        table = tree.xpath("//table[@id='oWinStreaks']")[0]
        breadcrumbs = tree.xpath("//div[@id='breadcrumbs']")[0]
        gamertag = breadcrumbs.xpath(".//span/text()")[0]
    except IndexError:
        return []

    return (
        gamertag,
        list(
            streak
            for streak in (_process_row(row) for row in table.xpath(".//tr"))
            if streak
        ),
    )


def build_gamer(gamer_id, streaks, num_to_display):
    """Build a gamer object that contains information about a gamer."""

    Gamer = namedtuple(
        "Gamer",
        [
            "name",
            "homepage",
            "best_n_by_count",
            "best_n_by_num_days",
            "best_n_by_avg_per_day",
            "best_n_by_weighted_avg",
        ],
    )
    return Gamer(
        gamer_id,
        f"https://www.trueachievements.com/gamer/{quote_plus(gamer_id)}",
        sorted(streaks, key=lambda x: x.achievement_count, reverse=True)[
            :num_to_display
        ],
        sorted(streaks, key=lambda x: x.length, reverse=True)[:num_to_display],
        sorted(streaks, key=lambda x: x.average_per_day, reverse=True)[:num_to_display],
        sorted(streaks, key=lambda x: x.weighted_average, reverse=True)[
            :num_to_display
        ],
    )


def get_streaks(gamer_id):
    """Get achievement streaks for the given TA gamer_id."""
    page = requests.get(
        f"https://www.trueachievements.com/winstreaks.aspx?gamerid={gamer_id}"
    )
    return parse_it(page.content)

    # Debugging code
    # import pickle

    # # with open('streaks1.pkl', 'wb') as fobj:
    # #     pickle.dump(streaks, fobj)

    # with open("streaks1.pkl", "rb") as fobj:
    #     return pickle.load(fobj)


def process_streaks(gamer_id, num_to_display):
    """Process streaks for the given TA gamer_id."""

    print("Getting streaks...")
    gamertag, streaks = get_streaks(gamer_id)  # 11497)  # 20768)
    print("Done getting streaks")

    gamer = build_gamer(gamertag, streaks, num_to_display)

    return gamer


def write_html(gamer1, gamer2, num_to_display):
    """Write HTML output of comparison of two gamers to current directory."""

    def format_num(value):
        fmt_str = "{:,}"
        if isinstance(value, float):
            fmt_str = "{0:,.3f}"
        return fmt_str.format(value)

    env = Environment(
        loader=FileSystemLoader("./templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["format_num"] = format_num

    template = env.get_template("compare_gamers.jinja2")

    with open("rendered.html", "w") as fobj:
        fobj.write(
            template.render(gamer1=gamer1, gamer2=gamer2, num_streaks=num_to_display)
        )


def main():
    if len(sys.argv) != 3:
        print(f"Specify gamerid: {sys.argv[0]} <gamerid1> <gamerid2>")
        return 1
    num_streaks = 5
    gamer1 = process_streaks(int(sys.argv[1]), num_streaks)
    gamer2 = process_streaks(int(sys.argv[2]), num_streaks)
    write_html(gamer1, gamer2, num_streaks)


if __name__ == "__main__":
    exit(main())
