"""Little bits of usefulness for Pyrticle"""

__copyright__ = "Copyright (C) 2007, 2008 Andreas Kloeckner"

__license__ = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see U{http://www.gnu.org/licenses/}.
"""



import pyrticle._internal as _internal
import pylinear.array as num
import pylinear.computation as comp




ZeroVector = _internal.ZeroVector




class NumberShiftSignaller:
    def __init__(self):
        from weakref import WeakKeyDictionary
        self.subscribers = WeakKeyDictionary()

    def subscribe(self, shiftable):
        self.subscribers[shiftable] = None

    def change_size(self, new_size):
        for subscriber in self.subscribers.iterkeys():
            subscriber.change_size(new_size)

    def move(self, orig, dest, size):
        for subscriber in self.subscribers.iterkeys():
            subscriber.move(orig, dest, size)

    def reset(self, start, size):
        for subscriber in self.subscribers.iterkeys():
            subscriber.reset(start, size)



class NumberShiftForwarder(_internal.NumberShiftListener, NumberShiftSignaller):
    def __init__(self):
        _internal.NumberShiftListener.__init__(self)
        NumberShiftSignaller.__init__(self)

    def note_change_size(self, new_size):
        self.change_size(new_size)

    def note_move(self, orig, dest, size):
        self.move(orig, dest, size)

    def note_reset(self, start, size):
        self.reset(start, size)




class NumberShiftableVector(object):
    """A vector that may be notified of shifts in the DOFs it contains.

    This solves the following problem: Particles in 
    L{pyrticle.cloud.ParticleCloud} may die at any time, including
    during a Runge-Kutta timestep. The state vector inside Runge-Kutta,
    needs to be notified that degrees of freedom may have shifted and/or
    been deleted. This class, together with the corresponding
    L{NumberShiftSignaller}, fulfills that purpose.
    """

    __slots__ = ["vector", "multiplier", "signaller", "__weakref__"]

    def __init__(self, vector, multiplier, signaller):
        self.vector = vector
        self.multiplier = multiplier
        self.signaller = signaller
        signaller.subscribe(self)

    @staticmethod
    def unwrap(instance):
        if isinstance(instance, NumberShiftableVector):
            return instance.vector
        else:
            return instance

    # arithmetic --------------------------------------------------------------
    def __add__(self, other):
        if len(self.vector) != len(self.unwrap(other)):
            print len(self.vector), len(self.unwrap(other)), type(other)
            print self.signaller, other.signaller
            print other in other.signaller.subscribers
            print "---------------------------------------------"
        return NumberShiftableVector(
                self.vector + self.unwrap(other),
                self.multiplier,
                self.signaller)

    __radd__ = __add__
        
    def __iadd__(self, other):
        self.vector += self.unwrap(other)
        return self

    def __mul__(self, other):
        result = NumberShiftableVector(
                self.vector * self.unwrap(other),
                self.multiplier,
                self.signaller)
        return result

    __rmul__ = __mul__

    # shiftiness --------------------------------------------------------------
    def change_size(self, new_size):
        old_size = len(self.vector)
        new_size *= self.multiplier

        if new_size > old_size:
            self.vector = num.hstack((
                    self.vector, 
                    num.zeros((new_size-len(self.vector),), 
                        dtype=self.vector.dtype)))
        elif new_size < old_size:
            self.vector = self.vector[:new_size]

    def move(self, orig, dest, size):
        m = self.multiplier
        self.vector[m*dest:m*(dest+size)] = self.vector[m*orig:m*(orig+size)]

    def reset(self, start, size):
        m = self.multiplier
        self.vector[start*m:(start+size)*m] = 0
