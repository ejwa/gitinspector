// A sample used for metrics.
import { readFileSync } from "fs";

/* A block comment
   spanning lines. */
export function classify(values: number[]): number {
	let score = 0;
	for (let i = 0; i < values.length; i++) {
		if (values[i] > 10) {
			score += i;
		} else if (values[i] < 0) {
			continue;
		} else {
			score--;
		}
	}
	while (score > 100) {
		score -= 50;
	}
	switch (score % 3) {
		case 0:
			score++;
			break;
		case 1:
			score += 2;
			break;
		default:
			score += 3;
	}
	return score;
}

console.log(classify([1, 20, -5]), readFileSync.name);
