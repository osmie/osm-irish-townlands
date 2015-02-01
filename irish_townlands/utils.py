def m2_to_arp(area_m2):
    area_acres = area_m2 / 4046.8564

    acres = int(area_acres)
    subacres = acres_float - acres

    roods = int(subacres * 4)
    perches = int((subacres * 4 - roods) * 40)

    return (acres, roods, perches)
