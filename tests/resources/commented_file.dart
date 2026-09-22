/*
 * A sample Dart file used to check the comment recognition.
 *
 * It exercises block comments, line comments and the documentation
 * comments that dart doc understands.
 */
import 'dart:io';

/// The dimensions of a rectangle.
class Dimensions {
  final double width;
  final double height;

  const Dimensions(this.width, this.height);
}

/**
 * A rectangle built from its dimensions.
 */
class Rectangle {
  final Dimensions dimensions;

  Rectangle(this.dimensions);

  void print() {
    /*
     * Print some stuff (testing comments)
     */
    stdout.writeln('\nCharacteristics of this rectangle');
    stdout.writeln('\nWidth  = ${dimensions.width}');
    stdout.writeln('\nHeight = ${dimensions.height}');
    stdout.writeln('\nArea   = ${dimensions.width * dimensions.height}'); // ^2
    stdout.writeln('See https://dart.dev/ for more');
  }
}

void main() {
  stdout.writeln('Provide the dimensions of a rectangle');
  stdout.write('Width: ');
  final width = double.parse(stdin.readLineSync()!);
  stdout.write('Height: ');
  final height = double.parse(stdin.readLineSync()!);

  // Create the rectangle and print it.
  Rectangle(Dimensions(width, height)).print();
}
