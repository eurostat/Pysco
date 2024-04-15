
def cartesian_product(nb1, nb2):
    pairs = []
    for i in range(nb1 + 1):
        for j in range(nb2 + 1): pairs.append([i, j])
    return pairs
