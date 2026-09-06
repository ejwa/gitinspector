// Package main is a sample used for metrics.
package main

import "fmt"

/* A block comment
   spanning lines. */
func classify(values []int) int {
	score := 0
	for i, v := range values {
		if v > 10 {
			score += i
		} else if v < 0 {
			continue
		} else {
			score--
		}
	}
	for j := 0; j < 3; j++ {
		switch j {
		case 0:
			score++
		case 1:
			score += 2
		default:
			score += 3
		}
	}
	defer fmt.Println("done")
	if score > 100 {
		goto end
	}
	return score
end:
	return -1
}

func main() {
	fmt.Println(classify([]int{1, 20, -5}))
}
