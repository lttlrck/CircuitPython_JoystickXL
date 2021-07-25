"""
Classes to simplify mapping GPIO pins and values to JoystickXL inputs and states.

This module provides a set of classes to aid in configuring GPIO pins and convert
their raw states to values that are usable by JoystickXL.
"""

# These typing imports help during development in vscode but fail in CircuitPython
try:
    from typing import Union
except ImportError:
    pass

# These are all CircuitPython built-ins
from analogio import AnalogIn  # type: ignore
from digitalio import DigitalInOut, Direction, Pull  # type: ignore
from microcontroller import Pin  # type: ignore


class VirtualInput:
    """Provide an object with a .value property to represent a remote input."""

    def __init__(self, value: Union[bool, int]) -> None:
        """
        Provide an object with a ``.value`` property to represent a remote input.

        :param value: Sets the initial .value property (Should be ``True`` for
           buttons, ``32768`` for axes).
        :type value: Union[bool, int]
        """
        self.value = value


def _initialize_digital_source(
    pin: Union[Pin, VirtualInput],
    active_low: bool,
) -> Union[DigitalInOut, VirtualInput]:
    """
    Configure a source as a GPIO digital input pin or VirtualInput.

    :param pin: CircuitPython pin identifier (i.e. ``board.D2``), or a ``VirtualInput``
       object.
    :type pin: Pin or VirtualInput
    :param active_low: Set to ``True`` if the input pin is active low (reads ``False``
       when the button is pressed), otherwise set to ``False``.
    :type active_low: bool
    :return: A fully configured digital source pin or virtual input.
    :rtype: DigitalInOut or VirtualInput
    """
    if isinstance(pin, Pin):
        source = DigitalInOut(pin)
        source.direction = Direction.INPUT
        if active_low:
            source.pull = Pull.UP
        else:
            source.pull = Pull.DOWN
        return source
    else:
        return VirtualInput(value=active_low)


def _initialize_analog_source(
    pin: Union[Pin, VirtualInput],
) -> Union[AnalogIn, VirtualInput]:
    """
    Configure a source as a GPIO analog input pin or VirtualInput.

    :param pin: CircuitPython pin identifier (i.e. ``board.A3``), or a ``VirtualInput``
       object.
    :type pin: Pin or VirtualInput
    :return: A fully configured analog source pin or virtual input.
    :rtype: AnalogIn or VirtualInput
    """
    if isinstance(pin, Pin):
        return AnalogIn(pin)
    else:
        return VirtualInput(value=32768)


class Button:
    """Data source storage and value processing for a button input."""

    @property
    def value(self) -> bool:
        """
        Get the current, fully processed value of this button input.

        :return: ``True`` if pressed, ``False`` if released.
        :rtype: bool
        """
        return self._source.value != self._active_low

    @property
    def source_value(self) -> bool:
        """
        Get the raw source input value.

        For ``VirtualInput`` sources, this property can also be set.
        """
        return self._source.value is True

    @source_value.setter
    def source_value(self, value: bool) -> None:
        """Set the raw source value for a VirtualInput button source."""
        if not isinstance(self._source, VirtualInput):
            raise TypeError("Only VirtualInput source values can be set manually.")
        self._source.value = value

    @property
    def active_low(self) -> bool:
        """Return ``True`` if the button is configured as active low."""
        return self._active_low

    def __init__(self, source: Pin = None, active_low: bool = True) -> None:
        """
        Provide data source storage and value processing for a button input.

        :param source: CircuitPython pin identifier (i.e. ``board.D2``).  (Defaults
           to ``None``, which will create a ``VirtualInput`` source instead.)
        :type source: Pin, optional
        :param active_low: Set to ``True`` if the input pin is active low
           (reads ``False`` when the button is pressed), otherwise set to ``False``.
           (defaults to ``True``)
        :type active_low: bool, optional
        """
        self._source = _initialize_digital_source(source, active_low)
        self._active_low = active_low


class Axis:
    """Data source storage and scaling/deadband processing for an axis input."""

    """Alias for the X-axis index."""
    X = 0

    """Alias for the Y-axis index."""
    Y = 1

    """Alias for the Z-axis index."""
    Z = 2

    """Alias for the RX-axis index."""
    RX = 3

    """Alias for the RY-axis index."""
    RY = 4

    """Alias for the RZ-axis index."""
    RZ = 5

    """Alias for the S0-axis index."""
    S0 = 6

    """Alias for the S1-axis index."""
    S1 = 7

    @property
    def value(self) -> int:
        """
        Get the current, fully processed value of this axis.

        :return: ``-127`` to ``127``, ``0`` if at rest/centered.
        :rtype: int
        """
        return self._update()

    @property
    def source_value(self) -> int:
        """
        Get the raw source input value.

        For ``VirtualInput`` sources, this property can also be set.
        """
        return self._source.value

    @source_value.setter
    def source_value(self, value: int) -> None:
        """Set the raw source value for a VirtualInput axis source."""
        if isinstance(self._source, VirtualInput):
            self._source.value = value
        else:
            raise TypeError("Only VirtualInput source values can be set manually.")

    @property
    def min(self) -> int:
        """Get the configured minimum raw ``analogio`` input value."""
        return self._min

    @property
    def max(self) -> int:
        """Get the configured maximum raw ``analogio`` input value."""
        return self._max

    @property
    def deadband(self) -> int:
        """Get the raw, absolute value of the configured deadband."""
        return self._deadband

    @property
    def invert(self) -> bool:
        """Return ``True`` if the raw `analogio` input value is inverted."""
        return self._invert < 0

    def __init__(
        self,
        source: Pin = None,
        deadband: int = 0,
        min: int = 0,
        max: int = 65535,
        invert: bool = False,
    ) -> None:
        """
        Provide data source storage and scaling/deadband processing for an axis input.

        :param source: CircuitPython pin identifier (i.e. ``board.A0``).  (Defaults
           to ``None``, which will create a ``VirtualInput`` source instead.)
        :type source: Pin, optional
        :param deadband: Raw, absolute value of the deadband to apply around the
           midpoint of the raw source value.  The deadband is used to prevent an axis
           from registering minimal values when it is centered.  Setting the deadband
           value to ``250`` means raw input values +/- 250 from the midpoint will all
           be treated as the midpoint.  (defaults to ``0``)
        :type deadband: int, optional
        :param min: The raw input value that corresponds to a scaled axis value of -127.
           Any raw input value <= to this value will get scaled to -127.  Useful if the
           component used to generate the raw input never actually reaches 0.
           (defaults to ``0``)
        :type min: int, optional
        :param max: The raw input value that corresponds to a scaled axis value of +127.
           Any raw input value >= to this value will get scaled to +127.  Useful if the
           component used to generate the raw input never actually reaches 65535.
           (defaults to ``65535``)
        :type max: int, optional
        :param invert: Set to ``True`` to invert the scaled axis value.  Useful if the
           physical orientation of the component used to generate the raw axis input
           does not match the logical direction of the axis input.
           (defaults to ``False``)
        :type invert: bool, optional
        """
        self._source = _initialize_analog_source(source)
        self._deadband = deadband
        self._min = min
        self._max = max
        if invert:
            self._invert = -1
        else:
            self._invert = 1
        self._value = 0
        self._last_source_value = 0

        # calculate raw input midpoint and scaled deadband range
        self._raw_midpoint = self._min + ((self._max - self._min) // 2)
        self._db_range = self._max - self._min - (self._deadband * 2)

        self._update()

    def _update(self) -> int:
        """Read raw input data and convert it to a joystick-compatible value.

        :return: ``-127`` to ``127``, ``0`` if at rest/centered.
        :rtype: int
        """
        if self._source.value == self._last_source_value:
            return self._value

        # clamp raw input value to specified min/max
        new_value = min(max(self._source.value, self._min), self._max)

        # account for deadband
        if new_value < (self._raw_midpoint - self._deadband):
            new_value -= self._min
        elif new_value > (self._raw_midpoint + self._deadband):
            new_value -= self._min - (self._deadband * 2)
        else:
            new_value = self._db_range // 2

        # calculate scaled joystick-compatible value and clamp to +/- 127
        self._value = (
            min(max(new_value * 255 // self._db_range - 127, -127), 127) * self._invert
        )

        return self._value


class Hat:
    """Data source storage and value conversion for hat switch inputs."""

    """Alias for the `UP` switch position."""
    U = 0

    """Alias for the ``UP + RIGHT`` switch position."""
    UR = 1

    """Alias for the ``RIGHT`` switch position."""
    R = 2

    """Alias for the ``DOWN + RIGHT`` switch position."""
    DR = 3

    """Alias for the ``DOWN`` switch position."""
    D = 4

    """Alias for the ``DOWN + LEFT`` switch position."""
    DL = 5

    """Alias for the ``LEFT`` switch position."""
    L = 6

    """Alias for the ``UP + LEFT`` switch position."""
    UL = 7

    """Alias for the ``IDLE`` switch position."""
    IDLE = 8

    @property
    def value(self) -> int:
        """
        Get the current, fully processed value of this hat switch.

        :return: Current position value, as follows:

              * ``0`` = UP
              * ``1`` = UP + RIGHT
              * ``2`` = RIGHT
              * ``3`` = DOWN + RIGHT
              * ``4`` = DOWN
              * ``5`` = DOWN + LEFT
              * ``6`` = LEFT
              * ``7`` = UP + LEFT
              * ``8`` = IDLE

        :rtype: int
        """
        return self._update()

    @property
    def active_low(self) -> bool:
        """Return ``True`` if the hat switch inputs are set to active low."""
        return self._active_low

    @property
    def up(self) -> bool:
        """
        Get the current, fully processed value of the up input.

        :return: ``True`` if pressed, ``False`` if released.
        :rtype: bool
        """
        return self._up.value != self._active_low

    @property
    def up_source_value(self) -> bool:
        """
        Get the raw ``up`` input source value.

        For ``VirtualInput`` sources, this property can also be set.
        """
        return self._up.value is True

    @up_source_value.setter
    def up_source_value(self, value: bool) -> None:
        """Allow setting the logical up input state for VirtualInputs."""
        if not isinstance(self._up, VirtualInput):
            raise TypeError("Only VirtualInput source values can be set manually.")
        self._up.value = value

    @property
    def down(self) -> bool:
        """
        Get the current, fully processed value of the down input.

        :return: ``True`` if pressed, ``False`` if released.
        :rtype: bool
        """
        return self._down.value != self._active_low

    @property
    def down_source_value(self) -> bool:
        """
        Get the raw ``down`` input source value.

        For ``VirtualInput`` sources, this property can also be set.
        """
        return self._down.value is True

    @down_source_value.setter
    def down_source_value(self, value: bool) -> None:
        """Allow setting the logical down input state for VirtualInputs."""
        if not isinstance(self._down, VirtualInput):
            raise TypeError("Only VirtualInput source values can be set manually.")
        self._down.value = value

    @property
    def left(self) -> bool:
        """
        Get the current, fully processed value of the left input.

        :return: ``True`` if pressed, ``False`` if released.
        :rtype: bool
        """
        return self._left.value != self._active_low

    @property
    def left_source_value(self) -> bool:
        """
        Get the raw ``left`` input source value.

        For ``VirtualInput`` sources, this property can also be set.
        """
        return self._left.value is True

    @left_source_value.setter
    def left_source_value(self, value: bool) -> None:
        """Allow setting the logical left input state for VirtualInputs."""
        if not isinstance(self._left, VirtualInput):
            raise TypeError("Only VirtualInput source values can be set manually.")
        self._left.value = value

    @property
    def right(self) -> bool:
        """
        Get the current, fully processed value of the right input.

        :return: ``True`` if pressed, ``False`` if released.
        :rtype: bool
        """
        return self._right.value != self._active_low

    @property
    def right_source_value(self) -> bool:
        """
        Get the raw ``right`` input source value.

        For ``VirtualInput`` sources, this property can also be set.
        """
        return self._right.value is True

    @right_source_value.setter
    def right_source_value(self, value: bool) -> None:
        """Allow setting the logical right input state for VirtualInputs."""
        if not isinstance(self._right, VirtualInput):
            raise TypeError("Only VirtualInput source values can be set manually.")
        self._right.value = value

    def __init__(
        self,
        up: Pin = None,
        down: Pin = None,
        left: Pin = None,
        right: Pin = None,
        active_low: bool = True,
    ) -> None:
        """
        Provide data source storage and value processing for a hat switch input.

        :param up: CircuitPython pin identifier (i.e. ``board.D2``).  (Defaults
           to ``None``, which will create a ``VirtualInput`` source instead.)
        :type up: Pin, optional
        :param down: CircuitPython pin identifier (i.e. ``board.D2``).  (Defaults
           to ``None``, which will create a ``VirtualInput`` source instead.)
        :type down: Pin, optional
        :param left: CircuitPython pin identifier (i.e. ``board.D2``).  (Defaults
           to ``None``, which will create a ``VirtualInput`` source instead.)
        :type left: Pin, optional
        :param right: CircuitPython pin identifier (i.e. ``board.D2``).  (Defaults
           to ``None``, which will create a ``VirtualInput`` source instead.)
        :type right: Pin, optional
        :param active_low: Set to ``True`` if the input pins are active low
           (read ``False`` when buttons are pressed), otherwise set to ``False``.
           (defaults to ``True``)
        :type active_low: bool, optional
        """
        self._up = _initialize_digital_source(up, active_low)
        self._down = _initialize_digital_source(down, active_low)
        self._left = _initialize_digital_source(left, active_low)
        self._right = _initialize_digital_source(right, active_low)
        self._active_low = active_low
        self._value = Hat.IDLE
        self._update()

    def _update(self) -> int:
        """Update the angular position value based on discrete input states."""
        U = self.up
        D = self.down
        L = self.left
        R = self.right

        if U and R:
            self._value = Hat.UR
        elif U and L:
            self._value = Hat.UL
        elif U:
            self._value = Hat.U
        elif D and R:
            self._value = Hat.DR
        elif D and L:
            self._value = Hat.DL
        elif D:
            self._value = Hat.D
        elif L:
            self._value = Hat.L
        elif R:
            self._value = Hat.R
        else:
            self._value = Hat.IDLE
        return self._value