# encoding: utf-8
def m2_to_arp(area_m2):
    area_acres = area_m2 / 4046.8564

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
