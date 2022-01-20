import json
import os
import datetime as dt
import os
import math

# Zone specific modifications, this is to determine double rolls
zonegroupsize = {"29":2, "604":10, "700":5, "701":3, "702":3}
# Zone groupsize exceptions, for CW where we don't really know the mult
zonegroupsizeexclude = {"29":[2]}
# Some scrolls are weird (info apparently)
zonescrolloverride = {"604":1}
# Scroll areas 605 - 614. Only areas where scroll mutipliers work
scrollAreas = [
    609,            # Cluster Cluck
    608,            # Goblins
    605,            # BK Trial
    611,            # Taproot
    610,            # Demonic Trial
    607,            # Corroded
    606,            # Giants
    612,            # I have no clue
    613,            # Shapeless Scroll
    614             # Stormier Seas
]
# Dungeon Areas 700 - 702. Only areas (besides CW and Info) where groups change the drop properties
dungeonAreas = [
    701,            # Goblin Village
    702,            # BK Fortress
    700             # Keep
]


## filters corrupted data
def isValid(zone: str, th: int, scroll: int, grouplead: int, groupsize: int):
    valid = True
    # Scroll only in scroll areas
    if (scroll > 0) and (not zone in scrollAreas):
        valid = False
    # Group Lead must be boolean
    if not grouplead in [0, 1]:
        valid = False
    # Groups can only participate in Dungeons
    if (groupsize > 1) and (not zone in dungeonAreas):
        valid = False
    # If we are missing at least 2 other people the person with highest dps gets 2 rolls aswell
    # Not captures -> we remove these cases
    if (groupsize < zonegroupsize.get(zone, 1) - 1) and (groupsize != 1):
        valid = False
    # We also do not know how loot in Cw is distributed -> ignore if 2 persons
    if groupsize in zonegroupsizeexclude.get(zone, []):
        valid = False
    return valid


## Computes the average multiplications of loot by loot: lx stat
# Formula: Math.floor(Math.random() * (maxRoll - minRoll + 1) * multiplier + minRoll) (c) Kugan
def scrollMult(scroll: int):
    l = 1 + 0.1 * scroll
    n = math.floor(l)
    # gives i items with likelyhood 1/l where the whole interval is covered. Last term is the rest.
    avg = n*(n+1)/(2*l) + (n + 1) * (l - n) / l
    return avg


## Calculates the multiplier to get back to TH 0, assuming the entry is valid
def killMult(zone: str, th: int, scroll: int, grouplead: int, groupsize: int):
    thMult = 1 + 0.03*(th + scroll)
    leadboost = 1 + (zonegroupsize.get(zone, 1) - groupsize) * grouplead
    return thMult * scrollMult(scroll) * leadboost


# Read the data directory and create a single final table
# Read data in order:
# Zone, TH, Scroll, GroupLead, GroupSize, MonsterID
def createTables(**kwargs):
    # Here, using what we know about scaling, create a base table for each zone
    baseDict = {}
    pathToFile = os.path.abspath(os.path.dirname(__file__))
    infile = kwargs.get("infile", f"{pathToFile}/summary.json")
    outfile = kwargs.get("outfile", f"{pathToFile}/compiledTables.json")
    with open(infile) as jj:
        data = json.load(jj)['log']
        for (Zone, A) in data.items():
            if Zone not in baseDict:
                baseDict[Zone] = {}
            for (TH, B) in A.items():
                for (Scroll, C) in B.items():
                    for (GroupSize, D) in C.items():
                        for (GroupLead, E) in D.items():
                            for (Monster, F) in E.items():
                                th = eval(TH)
                                scroll = eval(Scroll)
                                groupsize = eval(GroupSize)
                                grouplead = eval(GroupLead)
                                if isValid(Zone, th, scroll, grouplead, groupsize):
                                    if Monster not in baseDict[Zone]:
                                        baseDict[Zone][Monster] = {"kills":0, "loot":{}}
                                    # Find out scroll and group math
                                    bigmonster = baseDict[Zone][Monster]
                                    kills =  F["kills"] * killMult(Zone, th, scroll, grouplead, groupsize)
                                    bigmonster["kills"] += kills
                                    for (name, count) in F["loot"].items():
                                        if name not in bigmonster["loot"]:
                                            bigmonster["loot"][name] = count["total"]
                                        else:
                                            bigmonster["loot"][name] += count["total"]
    with open(outfile, "w") as jj:
        json.dump(baseDict, jj, indent=2)


if __name__ == '__main__':
    createTables()
