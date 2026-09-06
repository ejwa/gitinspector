// Sample JavaScript file contrasting nested and flat code.
function count(a, b, c) {
    var total = 0;
    var nums = [a, b, c];

    for (var i = 0; i < nums.length; i++) {
        total += nums[i];
    }

    return total;
}

function countFlat(a, b, c) {
    var total = 0;

    total += a;
    total += b;
    total += c;

    return total;
}

function classify(values) {
    var score = 0;

    for (var i = 0; i < values.length; i++) {
        if (values[i] > 10) {
            while (score > 0) {
                score -= 1;
            }
        } else if (values[i] < 0) {
            score += 1;
        } else {
            score = 0;
        }
    }

    switch (score) {
        case 1:
            break;
        default:
            score = 2;
    }

    try {
        report(score);
    } catch (error) {
        score = -1;
    }

    return score;
}
