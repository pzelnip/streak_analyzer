"""Achievement Streak Analyzer.

Given two TA (trueachievements.com) gamer id's produce an HTML report
comparing the achievement streaks of those two gamers.
"""

import sys
from collections import namedtuple
from datetime import datetime, timedelta
from multiprocessing.pool import ThreadPool
from urllib.parse import quote_plus

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from lxml import html


class Streak(
    namedtuple("Streak", ["start_date", "url", "length", "achievement_count"])
):
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
        def _process_date(tdnode):
            url = (
                "https://www.trueachievements.com" + tdnode.xpath(".//a")[0].values()[0]
            )
            return datetime.strptime(tdnode[0].text_content(), "%d %b %Y").date(), url

        tds = row.xpath(".//td")
        if not tds:
            return None
        streak_date, streak_url = _process_date(tds[0])
        return Streak(
            # datetime.strptime(tds[0].text_content(), "%d %b %Y").date(),
            streak_date,
            streak_url,
            int(tds[1].text_content().replace(",", "")),
            int(tds[2].text_content().replace(",", "")),
        )

    try:
        tree = html.fromstring(html_content)
        table = tree.xpath("//table[@id='oWinStreaks']")[0]
        breadcrumbs = tree.xpath("//div[@id='breadcrumbs']")[0]
        gamertag = breadcrumbs.xpath(".//span/text()")[0]
    except IndexError:
        return "Unknown - No Such Gamer", []

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
    result = parse_it(page.content)

    # # Debugging code
    # import pickle

    # with open("streaks1.pkl", "wb") as fobj:
    #     pickle.dump(result, fobj)

    # with open("streaks1.pkl", "rb") as fobj:
    #     return pickle.load(fobj)
    return result


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

    return template.render(gamer1=gamer1, gamer2=gamer2, num_streaks=num_to_display)


def lambda_entrypoint(event, context):
    """Entrypoint for running this in AWS Lambda."""
    # TODO: map event/context to get gamer id's

    # We assume a lambda proxy integration with API Gateway, which means
    # the response must be a JSON object formatted as that below.  See
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-create-api-as-simple-proxy-for-lambda.html#api-gateway-proxy-integration-lambda-function-python
    # for details.

    gamerid1 = 20768
    gamerid2 = 337895

    # ?gamerid1=20768&gamerid2=11497
    if event:
        qspm = event.get("queryStringParameters", {})
        if qspm:
            gamerid1 = qspm.get("gamerid1", 20768)
            gamerid2 = qspm.get("gamerid2", 337895)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": process_gamers(gamerid1, gamerid2),
    }


def process_gamers(gamer_id1, gamer_id2, num_streaks=5):
    pool = ThreadPool(processes=2)

    gamer1 = pool.apply_async(process_streaks, args=(gamer_id1, num_streaks))
    gamer2 = pool.apply_async(process_streaks, (gamer_id2, num_streaks))

    return write_html(gamer1.get(), gamer2.get(), num_streaks)


def main():
    if len(sys.argv) != 3:
        print(f"Specify gamerid: {sys.argv[0]} <gamerid1> <gamerid2>")
        return 1
    html = process_gamers(int(sys.argv[1]), int(sys.argv[2]))
    with open("rendered.html", "w") as fobj:
        fobj.write(html)


if __name__ == "__main__":
    exit(main())
