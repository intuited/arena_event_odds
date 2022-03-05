"""arena_event_odds.py

Calculations using formulae from Channel Fireball
https://strategy.channelfireball.com/all-strategy/mtg/channelmagic-articles/whats-the-best-mtg-arena-event-for-expected-value-and-can-you-go-infinite/
"""
from pprint import pprint
from functools import partial
pp = partial(pprint, sort_dicts=False)
from math import factorial
from tabulate import tabulate

pct = lambda x: round(x*100, ndigits=1)

def binomial(n, k):
    return factorial(n) / (factorial(k) * factorial(n-k))

def cf_record_prob_lose3(winrate, numwins):
    """Probability of winning `numwins` game in an event that stops at three losses.

    Assumes max wins is 7.

    >>> pct(cf_record_prob_lose3(0.6, 7))
    23.2
    >>> pct(cf_record_prob_lose3(0.45, 4))
    10.2
    """
    if numwins == 7:
        return pow(winrate, 7) + 7*pow(winrate, 6)*(1-winrate)*winrate + 28*pow(winrate, 6)*pow(1-winrate, 2)*winrate
    else:
        return pow(winrate, numwins) * pow(1-winrate, 2) * binomial(numwins+2, 2) * (1-winrate)

def cf_record_prob_lose2(winrate, numwins, maxwins=5):
    """Probability of winning `numwins` game in an event that stops at two losses.

    >>> pct(cf_record_prob_lose2(0.6, 5))
    23.3
    >>> pct(cf_record_prob_lose2(0.45, 3))
    11.0
    """
    if numwins == maxwins:
        return pow(winrate, numwins) + numwins*pow(winrate, numwins)*(1-winrate)
    else:
        return pow(winrate, numwins)*pow(1-winrate, 2)*(numwins+1)

def tabulate_roi(roi, winrates):
    """Tabulates ROI data for various winrates.  Used in doctests.

    `roi` is the roi method to be called
    `winrates` is a list of winrates as floats.
    """
    data = [roi(winrate) for winrate in winrates]
    column_headers = data[0].keys()
    data = [c.values() for c in data]
    data = [ [winrate] + list(row) for winrate, row in zip(winrates, data) ]
    return tabulate(data, headers=[''] + list(column_headers))

class Event:
    """Base class for event classes.

    Subclasses define
        - gem_rewards: list of gem reward amounts by games won
        - admission: price in gems for the event
        - pack_rewards: list of pack reward amounts by games won

    Subclasses also define either `wincount_probs` and `maxwins` or `wincount_odds`.
        - wincount_probs: binomial function used by default `wincount_odds`
        - maxwins: the maximum number of wins for the event
        - wincount_odds(winrate): returns list of odds of winning n games
    """
    rares = 3  # assume that an average of 3 rares are drafted

    @classmethod
    def weighted_rewards(cls, reward_scheme, winrate):
        return [odds * rewards
                for odds, rewards in zip(cls.wincount_odds(winrate), reward_scheme)]

    @classmethod
    def avg_gems(cls, winrate):
        """Average gem rewards per event."""
        return sum(cls.weighted_rewards(cls.gem_rewards, winrate))

    @classmethod
    def roi(cls, winrate):
        """Calculates total return on investment.

        Accounts for drafted rares and reward packs as well as rewarded gems.

        Rares are given a value of 200 gems (the price of a pack).

        This rate is probably quite inflated, since it does not account for
        the accumulation of wildcards that comes with opening packs.

        As well, the given of 3 picked rares is likely higher than typical.

        Admission prices are in gems.
        """
        average_wins = sum(wincount * p
                           for wincount, p in zip(range(8), cls.wincount_odds(winrate)))
        gems = cls.avg_gems(winrate)
        packs = sum(cls.weighted_rewards(cls.pack_rewards, winrate))
        reward = gems + 200*(packs + cls.rares)
        return {'admission': cls.admission,
                'avg wins': round(average_wins, ndigits=1),
                'avg gems': round(gems),
                'avg packs': round(packs, ndigits=1),
                'rares': cls.rares,
                'value': round(reward),
                'profit': round(reward - cls.admission),
                'roi ratio': round(float(reward) / cls.admission, ndigits=2),
                }

    @classmethod
    def wincount_odds(cls, winrate):
        return [cls.wincount_probs(winrate, numwins)
                for numwins in range(cls.maxwins+1)]

def gems_per_sealed(winrate):
    """Calculates average gems per Sealed Draft for a given winrate.

    >>> pprint([(winrate, round(gems_per_sealed(winrate)))
    ...         for winrate in (r/100 for r in range(30, 100, 5))])
    [(0.3, 524),
     (0.35, 621),
     (0.4, 732),
     (0.45, 860),
     (0.5, 1002),
     (0.55, 1159),
     (0.6, 1326),
     (0.65, 1499),
     (0.7, 1672),
     (0.75, 1834),
     (0.8, 1975),
     (0.85, 2086),
     (0.9, 2160),
     (0.95, 2194)]

    Win rate needed to break even at Sealed is 81.01%
    >>> round(gems_per_sealed(0.8101))
    2000
    """
    wincount_odds = [cf_record_prob_lose3(winrate, numwins) for numwins in range(8)]
    gem_rewards = [200, 400, 600, 1200, 1400, 1600, 2000, 2200]
    weighted_rewards = [odds * rewards for odds, rewards in zip(wincount_odds, gem_rewards)]
    return sum(weighted_rewards)

def gems_per_trad_sealed(winrate):
    """Average gems per Traditional Sealed event.

    Note that this uses winrate per match, rather than per game.

    >>> pprint([(winrate, round(gems_per_trad_sealed(winrate)))
    ...         for winrate in (r/100 for r in range(30, 100, 5))])
    [(0.3, 567),
     (0.35, 668),
     (0.4, 781),
     (0.45, 904),
     (0.5, 1038),
     (0.55, 1179),
     (0.6, 1326),
     (0.65, 1475),
     (0.7, 1624),
     (0.75, 1768),
     (0.8, 1902),
     (0.85, 2019),
     (0.9, 2113),
     (0.95, 2177)]

    Win rate needed to break even at Trad Sealed is 84.12%
    >>> round(gems_per_trad_sealed(0.8412))
    2000
    """
    wincount_odds = [cf_record_prob_lose2(winrate, numwins, maxwins=4) for numwins in range(5)]
    gem_rewards = [200, 500, 1200, 1800, 2200]
    weighted_rewards = [odds * rewards for odds, rewards in zip(wincount_odds, gem_rewards)]
    return sum(weighted_rewards)

class QuickDraft(Event):
    """Analysis of Quick Draft events.

    >>> pprint([(winrate, round(QuickDraft.avg_gems(winrate)))
    ...         for winrate in (r/100 for r in range(30, 105, 5))])
    [(0.3, 153),
     (0.35, 188),
     (0.4, 232),
     (0.45, 285),
     (0.5, 347),
     (0.55, 419),
     (0.6, 499),
     (0.65, 585),
     (0.7, 672),
     (0.75, 755),
     (0.8, 830),
     (0.85, 889),
     (0.9, 928),
     (0.95, 947),
     (1.0, 950)]

    Win rate needed to break even at Quick Draft is 74.69%
    >>> round(QuickDraft.avg_gems(0.7469))
    750

    >>> pp(QuickDraft.roi(0.6))
    {'admission': 750,
     'avg wins': 4.0,
     'avg gems': 499,
     'avg packs': 1.2,
     'rares': 3,
     'value': 1345,
     'profit': 595,
     'roi ratio': 1.79}

    >>> winrates = [i / 100 for i in range(0, 105, 5)]
    >>> print(tabulate_roi(QuickDraft.roi, winrates))
            admission    avg wins    avg gems    avg packs    rares    value    profit    roi ratio
    ----  -----------  ----------  ----------  -----------  -------  -------  --------  -----------
    0             750         0            50          1          3      850       100         1.13
    0.05          750         0.2          59          1          3      859       109         1.14
    0.1           750         0.3          70          1          3      870       120         1.16
    0.15          750         0.5          84          1          3      884       134         1.18
    0.2           750         0.7         102          1          3      902       152         1.2
    0.25          750         1           125          1          3      925       175         1.23
    0.3           750         1.3         153          1          3      954       204         1.27
    0.35          750         1.6         188          1          3      991       241         1.32
    0.4           750         2           232          1          3     1037       287         1.38
    0.45          750         2.4         285          1          3     1095       345         1.46
    0.5           750         2.9         347          1.1        3     1165       415         1.55
    0.55          750         3.4         419          1.1        3     1249       499         1.67
    0.6           750         4           499          1.2        3     1345       595         1.79
    0.65          750         4.5         585          1.3        3     1452       702         1.94
    0.7           750         5.1         672          1.5        3     1564       814         2.09
    0.75          750         5.7         755          1.6        3     1676       926         2.23
    0.8           750         6.2         830          1.7        3     1777      1027         2.37
    0.85          750         6.6         889          1.9        3     1861      1111         2.48
    0.9           750         6.9         928          1.9        3     1918      1168         2.56
    0.95          750         7           947          2          3     1945      1195         2.59
    1             750         7           950          2          3     1950      1200         2.6
    """
    gem_rewards = [50, 100, 200, 300, 450, 650, 850, 950]
    admission = 750  #admission price in gems
    pack_rewards = [1, 1, 1, 1, 1, 1, 1, 2]
    wincount_probs = cf_record_prob_lose3
    maxwins = 7

class TradDraft(Event):
    """Analysis of Traditional Draft events.

    Note that this uses winrate per match, rather than per game.

    >>> winrates = [i / 100 for i in range(30, 105, 5)]
    >>> pprint([(winrate, round(TradDraft.avg_gems(winrate)))
    ...         for winrate in winrates])
    [(0.3, 270),
     (0.35, 368),
     (0.4, 480),
     (0.45, 608),
     (0.5, 750),
     (0.55, 908),
     (0.6, 1080),
     (0.65, 1268),
     (0.7, 1470),
     (0.75, 1688),
     (0.8, 1920),
     (0.85, 2168),
     (0.9, 2430),
     (0.95, 2707),
     (1.0, 3000)]

    Break-even win rate for Trad Draft is 70.7%.
    >>> round(TradDraft.avg_gems(0.707))
    1500

    >>> print(tabulate_roi(TradDraft.roi, winrates))
            admission    avg wins    avg gems    avg packs    rares    value    profit    roi ratio
    ----  -----------  ----------  ----------  -----------  -------  -------  --------  -----------
    0.3          1500         0.9         270          1.7        3     1210      -290         0.81
    0.35         1500         1.1         368          1.9        3     1354      -146         0.9
    0.4          1500         1.2         480          2.2        3     1517        17         1.01
    0.45         1500         1.4         608          2.5        3     1699       199         1.13
    0.5          1500         1.5         750          2.8        3     1900       400         1.27
    0.55         1500         1.7         908          3.1        3     2119       619         1.41
    0.6          1500         1.8        1080          3.4        3     2355       855         1.57
    0.65         1500         2          1268          3.7        3     2608      1108         1.74
    0.7          1500         2.1        1470          4          3     2878      1378         1.92
    0.75         1500         2.2        1688          4.4        3     3162      1662         2.11
    0.8          1500         2.4        1920          4.7        3     3462      1962         2.31
    0.85         1500         2.5        2168          5          3     3777      2277         2.52
    0.9          1500         2.7        2430          5.4        3     4105      2605         2.74
    0.95         1500         2.9        2707          5.7        3     4446      2946         2.96
    1            1500         3          3000          6          3     4800      3300         3.2

    """
    gem_rewards = [0, 0, 1000, 3000]
    admission = 1500
    pack_rewards = [1, 1, 4, 6]
    def wincount_odds(winrate):
        """Calculate odds of winning n games for each possible value of n.

        This event is unlike the others because we play three matches regardless.
        Because of this, we calculate wincount odds using case count probability
        rather than binomial distribution calculation.
        Different win counts have different cases:
          - 0 wins: LLL
          - 1 win:  WLL, LWL, LLW
          - 2 wins: WWL, WLW, LWW
          - 3 wins: WWW
        """
        case_counts = [1, 3, 3, 1]
        return [cc*pow(1-winrate, 3-wincount)*pow(winrate, wincount)
                for cc, wincount in zip(case_counts, range(4))]

class PremierDraft(Event):
    """Analysis of Premier Draft events.

    >>> winrates = [i / 100 for i in range(30, 105, 5)]
    >>> pprint([(winrate, round(PremierDraft.avg_gems(winrate)))
    ...         for winrate in winrates])
    [(0.3, 295),
     (0.35, 396),
     (0.4, 517),
     (0.45, 658),
     (0.5, 820),
     (0.55, 998),
     (0.6, 1189),
     (0.65, 1388),
     (0.7, 1586),
     (0.75, 1773),
     (0.8, 1938),
     (0.85, 2067),
     (0.9, 2153),
     (0.95, 2193),
     (1.0, 2200)]

    Break-even win rate for Premier Draft is 67.8
    >>> round(PremierDraft.avg_gems(0.678))
    1500

    >>> print(tabulate_roi(PremierDraft.roi, winrates))
            admission    avg wins    avg gems    avg packs    rares    value    profit    roi ratio
    ----  -----------  ----------  ----------  -----------  -------  -------  --------  -----------
    0.3          1500         1.3         295          1.5        3     1188      -312         0.79
    0.35         1500         1.6         396          1.6        3     1325      -175         0.88
    0.4          1500         2           517          1.9        3     1492        -8         0.99
    0.45         1500         2.4         658          2.2        3     1690       190         1.13
    0.5          1500         2.9         820          2.5        3     1918       418         1.28
    0.55         1500         3.4         998          2.9        3     2175       675         1.45
    0.6          1500         4          1189          3.3        3     2456       956         1.64
    0.65         1500         4.5        1388          3.8        3     2752      1252         1.83
    0.7          1500         5.1        1586          4.3        3     3051      1551         2.03
    0.75         1500         5.7        1773          4.8        3     3337      1837         2.22
    0.8          1500         6.2        1938          5.3        3     3590      2090         2.39
    0.85         1500         6.6        2067          5.6        3     3791      2291         2.53
    0.9          1500         6.9        2153          5.9        3     3925      2425         2.62
    0.95         1500         7          2193          6          3     3989      2489         2.66
    1            1500         7          2200          6          3     4000      2500         2.67
    """
    gem_rewards = [50, 100, 250, 1000, 1400, 1600, 1800, 2200]
    wincount_probs = cf_record_prob_lose3
    maxwins = 7
    admission = 1500
    pack_rewards = [1, 1, 2, 2, 3, 4, 5, 6]
