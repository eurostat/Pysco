
def cartesian_product(nb1, nb2):
    pairs = []
    for i in range(nb1 + 1):
        for j in range(nb2 + 1): pairs.append([i, j])
    return pairs


def cartesian_product_comp(minx, miny, maxx, maxy, step):
    pairs = []
    for x in range(minx, maxx, step):
        for y in range(miny, maxy, step): pairs.append([x, y])
    return pairs
