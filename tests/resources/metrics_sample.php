<?php
// A sample used for metrics.
require_once "vendor/autoload.php";

/* A block comment
   spanning lines. */
function classify(array $values): int {
	$score = 0;
	foreach ($values as $value) {
		if ($value > 10) {
			$score += $value;
		} elseif ($value < 0) {
			continue;
		} else {
			$score--;
		}
	}
	for ($i = 0; $i < 3; $i++) {
		$score++;
	}
	while ($score > 100) {
		$score -= 50;
	}
	switch ($score % 3) {
		case "zero":
			$score++;
			break;
		case "one":
			$score += 2;
			break;
		default:
			$score += 3;
	}
	return $score;
}

echo classify([1, 20, -5]);
