/*
 * A sample Rust file used to check the comment recognition.
 *
 * It exercises block comments, line comments and the documentation
 * comments that rustdoc understands.
 */
//! Documentation for the rectangle sample.
use std::io::stdin;

/// The dimensions of a rectangle.
struct Dimensions {
    width: f64,
    height: f64,
}

/*
 * A rectangle built from its dimensions.
 */
struct Rectangle {
    dimensions: Dimensions,
}

impl Rectangle {
    /** Builds a rectangle. */
    fn new(dimensions: Dimensions) -> Rectangle {
        Rectangle { dimensions }
    }

    fn print(&self) {
        /*
         * Print some stuff (testing comments)
         */
        println!("\nCharacteristics of this rectangle");
        println!("\nWidth  = {}", self.dimensions.width);
        println!("\nHeight = {}", self.dimensions.height);
        println!("\nArea   = {}", self.dimensions.width * self.dimensions.height); // ^2
    }
}

fn main() {
    let mut input = String::new();

    println!("Provide the dimensions of a rectangle");
    print!("Width: ");
    stdin().read_line(&mut input).unwrap();
    let width = input.trim().parse().unwrap();
    input.clear();
    print!("Height: ");
    stdin().read_line(&mut input).unwrap();
    let height = input.trim().parse().unwrap();

    // Create the rectangle and print it.
    let rectangle = Rectangle::new(Dimensions { width, height });
    rectangle.print();
}
