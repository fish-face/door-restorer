NW, NE, SW, SE = range(4)
SUBTILE_CHECKS = ((3, 1, 0), (1, 5, 2), (3, 7, 6), (7, 5, 8))
SUBTILE_SOURCES = ((5, 1, 3, 4, 2), (4, 1, 5, 2, 3), (3, 1, 5, 2, 4), (2, 1, 3, 4, 5))

def get_adjacency_sources(connections):
    subtiles = []
    for corner in (NW, NE, SW, SE):
        checks = SUBTILE_CHECKS[corner]
        sources = SUBTILE_SOURCES[corner]
        if connections[checks[0]]:
            if connections[checks[1]]:
                if connections[checks[2]]:
                    subtiles.append(sources[0])
                else:
                    subtiles.append(sources[1])
            else:
                subtiles.append(sources[2])
        else:
            if connections[checks[1]]:
                subtiles.append(sources[3])
            else:
                subtiles.append(sources[4])

    return subtiles
