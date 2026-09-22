// Sample Dart file used to check the metrics.
import 'dart:math';

/* A block comment
   spanning lines. */
/// A doc comment describing the class.
class Classifier {
  final elsewhere = 'iffy';
  final returned = <String, int>{};

  int doubled(int value) => value * 2;

  int classify(List<int> values) {
    var score = 0;
    for (final value in values) {
      if(value > 10) {
        score += elsewhere.length;
      } else if (value < 0) {
        continue;
      } else {
        score -= 1;
      }
    }
    switch (elsewhere) {
      case 'high':
        score += 10;
        break;
      case 'low' || 'none':
        score += 5;
      default:
        score += 1;
    }
    final label = switch (score) {
      0 => 'none',
      _ => 'some',
    };
    var i = 0;
    while(i < 3) {
      i++;
    }
    try {
      returned['breakEven'] = score;
    } on FormatException catch (e) {
      assert(score != 0);
    }
    return score + label.length;
  }
}
