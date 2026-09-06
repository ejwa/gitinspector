// Sample Swift file used to check the metrics.
import Foundation

/* A block comment
   spanning lines. */
func classify(values: [Int]) -> Int {
    var score = 0
    let formatted = String(format: "%d", score)
    let identifier = formatted.count
    for value in values {
        if value > 10 {
            score += identifier
        } else if value < 0 {
            continue
        } else {
            score -= 1
        }
    }
    guard score > 0 else {
        return -1
    }
    switch score {
    case 1, 2:
        score += 10
    case let x where x > 100:
        break
    default:
        score += 3
    }
    var i = 0
    repeat {
        i += 1
    } while i < 3
    while i > 0 {
        i -= 1
    }
    return score
}
