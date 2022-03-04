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
    """Base class for event classes."""
    pass

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

    gem_rewards = [50, 100, 200, 300, 450, 650, 850, 950]
    admission = 750  #admission price in gems
    pack_rewards = [1, 1, 1, 1, 1, 1, 1, 2]
    rares = 3  # assume that an average of 3 rares are drafted
    wincount_odds = lambda winrate: [cf_record_prob_lose3(winrate, numwins) for numwins in range(8)]

    @classmethod
    def weighted_rewards(cls, reward_scheme, winrate):
        return [odds * rewards
                for odds, rewards in zip(cls.wincount_odds(winrate), reward_scheme)]

    @classmethod
    def avg_gems(cls, winrate):
        """Average gem rewards per Quick Draft event.

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
        """
        return sum(cls.weighted_rewards(cls.gem_rewards, winrate))

    @classmethod
    def roi(cls, winrate):
        """Calculates total return on investment.

        Accounts for drafted rares and reward packs as well as rewarded gems.
        Rares are given a value of 200 gems (the price of a pack).
        Admission is assumed to be in gems.

        >>> pp(QuickDraft.roi(0.6))
        {'admission': 750,
         'avg wins': 4.0,
         'avg gems': 499,
         'avg packs': 1.2,
         'rares': 3,
         'value': 1345,
         'profit': 595,
         'roi ratio': 1.79}

        >>> winrates = [i / 100 for i in range(30, 105, 5)]
        >>> print(tabulate_roi(QuickDraft.roi, winrates))
                admission    avg wins    avg gems    avg packs    rares    value    profit    roi ratio
        ----  -----------  ----------  ----------  -----------  -------  -------  --------  -----------
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

def gems_per_trad_draft(winrate):
    """Average gems per Traditional Draft event.

    Note that this uses winrate per match, rather than per game.

    >>> pprint([(winrate, round(gems_per_trad_draft(winrate)))
    ...         for winrate in (r/100 for r in range(30, 105, 5))])
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
    >>> round(gems_per_trad_draft(0.707))
    1500
    """
    # This event is unlike the others because we play three matches regardless.
    # Different win counts have different cases:
    #   - 0 wins: LLL
    #   - 1 win:  WLL, LWL, LLW
    #   - 2 wins: WWL, WLW, LWW
    #   - 3 wins: WWW
    case_counts = [1, 3, 3, 1]
    wincount_odds = [cc*pow(1-winrate, 3-wincount)*pow(winrate, wincount)
                     for cc, wincount in zip(case_counts, range(4))]
    gem_rewards = [0, 0, 1000, 3000]
    weighted_rewards = [odds*reward for odds, reward in zip(wincount_odds, gem_rewards)]
    return sum(weighted_rewards)

def gems_per_premier_draft(winrate):
    """Average gems per Premier Draft event.

    >>> pprint([(winrate, round(gems_per_premier_draft(winrate)))
    ...         for winrate in (r/100 for r in range(30, 105, 5))])
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
    >>> round(gems_per_premier_draft(0.678))
    1500
    """
    wincount_odds = [cf_record_prob_lose3(winrate, numwins) for numwins in range(8)]
    gem_rewards = [50, 100, 250, 1000, 1400, 1600, 1800, 2200]
    weighted_rewards = [odds * rewards for odds, rewards in zip(wincount_odds, gem_rewards)]
    return sum(weighted_rewards)
