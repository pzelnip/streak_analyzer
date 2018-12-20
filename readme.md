# Xbox Live Achievement Streak Analyzer

<a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## What this is

I was bored one night and browsing <https://www.trueachievements.com> and noticed I was on
a decent achievement streak (ie an achievement streak is the number of consecutive days
getting at least one Xbox achievement each day).

I looked to see how that streak compared to other streaks I've had in the past.  This led
me to realize that some streaks I've had tend to be long (by number of days), but not very
many achievements.  Others were achievement heavy (ie I got a lot of achievements per day)
but didn't last long.

I wondered how my friends compared.  So I wrote a little Python to parse the page, and spit
out a comparison of two gamertags achievement streaks as read from TA.  This is that script.

## How To Use

### Setup

First get a Python env going (3.6 or better) and install the requirements:

```shell
pip install -r requirements.txt --upgrade
```

### Run the Script

```shell
python3 analyzer.py 20768 337895
```

To compare me ([Pedle
Zelnip](https://www.trueachievements.com/gamer/Pedle+Zelnip)) to the dude who
has the longest streak currently on TA
([winginor](https://www.trueachievements.com/winstreaks.aspx?gamerid=337895))

The values supplied are the `gamerid` values on TA.

The output of this is that it writes a file in your current directory called
`rendered.html` that does a quick comparison of the two gamers streaks.

## I Want to See It Running

Ok, go to: <https://om0ys5szh8.execute-api.ca-central-1.amazonaws.com/prod?gamerid1=20768&gamerid2=11497>
