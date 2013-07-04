/*
 * Copyright © 2013 Ejwa Software. All rights reserved.
 *
 * This file is part of gitinspector.
 *
 * gitinspector is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * gitinspector is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with gitinspector. If not, see <http://www.gnu.org/licenses/>.
 */
#include <iostream>
#include <stdio.h>

struct Dimensions {
	double width;
	double height;
};

/*
 * A class for a rectangle
 */
class Rectangle {
	private:
		Dimensions dimensions;
	public:
		Rectangle(Dimensions dimensions);
		void print();
};

Rectangle::Rectangle(Dimensions dimensions) {
	this->dimensions = dimensions;
}

void Rectangle::print() {
	/*
	 * Print some stuff (testing comments)
	 */
	std::cout << "\nCharacteristics of this rectangle";
	std::cout << "\nWidth  = " << this->dimensions.width;
	std::cout << "\nHeight = " << this->dimensions.height;
	std::cout << "\nArea   = " << this->dimensions.width * this->dimensions.height << "\n"; // ^2
}

int main(int argc, char *argv[]) {
	Dimensions dimensions;

	std::cout << "Provide the dimensions of a rectangle\n";
	std::cout << "Width: ";
	std::cin >> dimensions.width;
	std::cout << "Height: ";
	std::cin >> dimensions.height;

	// Create rectanlge and wait for user-input.
	Rectangle rectangle(dimensions);
	rectangle.print();
	getchar();

	return 0;
}
