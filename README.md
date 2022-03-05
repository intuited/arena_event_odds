## Arena Event Odds
Just some Python code that calculates average reward for various Arena Draft and Sealed events.

Average rewards for various win rates for each type of event are incorporated into doctests in the main code file,
as is the winrate needed to break even in gem investment for each event type.

Overall ROI analysis has also been added for the three draft formats, however this analysis may be based on some false assumptions
of average number of rares picked and of the value of rares relative to that of packs and other purchaseables.

Mathematical formulae from a [Channel Fireball article][1] were used.
However, some of the information in that article is somewhat out of date, as event structures have changed over the past few years.

Please see `arena_event_odds.py` for the probability data.

[1]: https://strategy.channelfireball.com/all-strategy/mtg/channelmagic-articles/whats-the-best-mtg-arena-event-for-expected-value-and-can-you-go-infinite/
