# encoding: utf-8
import re
from datetime import date

def m2_to_arp(area_m2):
    area_acres = area_m2 / 4046.85642

    acres = int(area_acres)
    subacres = area_acres - acres

    roods = int(subacres * 4)
    perches = int((subacres * 4 - roods) * 40)

    return (acres, roods, perches)

def remove_prefixes(string, prefixes):
    for i in range(1000):
        for prefix in prefixes:
            if string.startswith(prefix):
                string = string[len(prefix):]
                continue
        else:
            break

    return string

def remove_accents(string):
    for a, b in [ (u"Á", "A"), (u"É", "E"), (u"Í", "I"), (u"Ó", "O"), (u"Ú", "U"),
                 (u"á", "a"), (u"é", "e"), (u"í", "i"), (u"ó", "o"), (u"ú", "u") ]:

        string = string.replace(a, b)

    return string

def parse_period(key):
    historic_key_regex = re.compile("^((?P<startyear>[0-9u]{4})\??~?)?--((?P<endyear>[0-9u]{4})\??~?)?$")
    match = historic_key_regex.match(key)
    if not match:
        # FIXME support dates
        return None
    else:
        p = Period()
        p.startyear = match.group('startyear')
        p.endyear = match.group('endyear')
        p.startdate = date(int(p.startyear), 1, 1) if p.startyear else None
        p.enddate = date(int(p.endyear), 1, 1) if p.endyear else None


    return p

class Period(object):
    def __unicode__(self):
        # FIXME i18n this
        if self.startyear is not None and self.endyear is not None:
            date_string = "{} to {}".format(self.startyear, self.endyear)
        elif self.startyear is None and self.endyear is not None:
            date_string = "Before {}".format(self.endyear)
        elif self.startyear is not None and self.endyear is None:
            date_string =  "{} to present".format(self.startyear)
        elif self.startyear is None and self.endyear is None:
            # Should be impossible
            raise NotImplementedError()

        return date_string

    def __cmp__(self, other):
        if self.startdate is not None and other.startdate is not None:
            return cmp(self.startdate, other.startdate)
        elif self.startdate is None and other.startdate is not None:
            return -1
        elif self.startdate is not None and other.startdate is None:
            return 1
        elif self.startdate is None and other.startdate is None:
            raise NotImplementedError()

def historic_names(tags):
    table = []
    for k, v in tags.items():
        if not k.startswith("name:"):
            continue
        k = k[5:]

        period = parse_period(k)
        if period is None:
            continue

        # FIXME include source, and source url link

        table.append((period, v))

    table.sort()

    table = {'header': ['When', 'Name'], 'body': table, 'has_results': len(table) > 0 }

    # TODO add other tags, not just 'name'
    return table

