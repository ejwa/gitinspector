// Sample Rust file used to check the metrics.
use std::collections::HashMap;

/* A block comment
   spanning lines. */
/// A doc comment describing the function.
fn classify(values: &[i32]) -> i32 {
    let mut score = 0;
    let formatter = format!("{}", score);
    let identifier = formatter.len() as i32;
    let mut returned = HashMap::new();
    returned.insert("iffy", identifier);
    for value in values {
        if *value > 10 {
            score += identifier;
        } else if *value < 0 {
            continue;
        } else {
            score -= 1;
        }
    }
    match score {
        1 | 2 => score += 10,
        x if x > 100 => break_even(&mut score),
        _ => score += 3,
    }
    let mut i = 0;
    loop {
        i += 1;
        if i > 3 {
            break;
        }
    }
    while let Some(value) = values.iter().next() {
        if *value == 0 {
            break;
        }
        i -= 1;
    }
    while i > 0 {
        i -= 1;
    }
    assert!(score != 0);
    return score;
}

fn break_even(score: &mut i32) {
    *score = 0;
}
