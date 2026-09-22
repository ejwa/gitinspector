// Sample Groovy file used to check the metrics.
import groovy.transform.CompileStatic

/* A block comment
   spanning lines. */
/** A groovydoc comment describing the class. */
class Classifier {
    def elsewhere = "iffy"
    def returned = [:]

    int classify(List<Integer> values) {
        int score = 0
        for (value in values) {
            if(value > 10) {
                score += elsewhere.size()
            } else if (value < 0) {
                continue
            } else {
                score -= 1
            }
        }
        switch (score) {
            case "high":
                score += 10
                break
            case 1..5:
                score += 5
                break
            case [6, 7]:
                score += 3
                break
            default:
                score += 1
        }
        def label = switch (score) {
            case 0 -> "none"
            default -> "some"
        }
        int i = 0
        while(i < 3) {
            i++
        }
        try {
            returned.breakEven = score
        } catch (Exception e) {
            assert score != 0
        }
        return score
    }
}
