# Sample Python file contrasting nested and flat code.


def count(a, b, c):
    total = 0

    for value in (a, b, c):
        total += value

    return total


def count_flat(a, b, c):
    total = 0

    total += a
    total += b
    total += c

    return total


def classify(values):
    score = 0

    for value in values:
        if value > 10:
            while score > 0:
                score -= 1
        elif value < 0:
            score += 1
        else:
            score = 0

    try:
        report(score)
    except ValueError:
        score = -1

    return score
