#!/usr/bin/env groovy
/*
 * A sample Groovy script used to check the comment recognition.
 *
 * It exercises block comments, line comments and the documentation
 * comments that groovydoc understands.
 */
import groovy.transform.Canonical

/** The dimensions of a rectangle. */
@Canonical
class Dimensions {
    double width
    double height
}

/**
 * A rectangle built from its dimensions.
 */
class Rectangle {
    Dimensions dimensions

    void print() {
        /*
         * Print some stuff (testing comments)
         */
        println "\nCharacteristics of this rectangle"
        println "\nWidth  = ${dimensions.width}"
        println "\nHeight = ${dimensions.height}"
        println "\nArea   = ${dimensions.width * dimensions.height}" // ^2
        println "See https://groovy-lang.org/ for more"
    }
}

def input = System.in.newReader()

println "Provide the dimensions of a rectangle"
print "Width: "
def width = input.readLine() as double
print "Height: "
def height = input.readLine() as double

// Create the rectangle and print it.
new Rectangle(dimensions: new Dimensions(width, height)).print()
