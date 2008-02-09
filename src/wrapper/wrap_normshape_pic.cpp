// Pyrticle - Particle in Cell in Python
// Python wrapper for PIC algorithm
// Copyright (C) 2007 Andreas Kloeckner
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or // (at your option) any later version.  // 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.





#include "wrap_pic.hpp"




void expose_shape_pic()
{
  expose_pic_algorithm<
      pic<
        pic_data<3,3>,
        normalized_shape_function_reconstructor,
        monomial_particle_pusher
        >
      >();
  expose_pic_algorithm<
      pic<
        pic_data<2,2>,
        normalized_shape_function_reconstructor,
        monomial_particle_pusher
        >
      >();
}
