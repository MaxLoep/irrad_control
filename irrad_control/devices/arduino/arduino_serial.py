from time import sleep
from irrad_control.devices.serial_device import SerialDevice


class ArduinoSerial(SerialDevice):
    
    CMD_DELIMITER = ':'
    
    CMDS = {
        'communication_delay': 'D'
    }

    ERRORS = {
        'error': "An error occured"
    }

    @property
    def communication_delay(self):
        """
        The communication delay between two commands to the Arduino

        Returns
        -------
        int
            Communication delay in milliseconds
        """
        return int(self.query(self.create_command(self.CMDS['communication_delay'])))

    @communication_delay.setter
    def communication_delay(self, comm_delay):
        """
        Sets the communication delay property

        Parameters
        ----------
        comm_delay : int
            Communication delay in milliseconds
        """
        self._set_and_retrieve(cmd='set_delay', val=comm_delay)

    def __init__(self, port, baudrate=115200, timeout=1):
        super().__init__(port=port, baudrate=baudrate, timeout=timeout) 
        sleep(1)  # Allow Arduino to reboot; serial connection resets the Arduino
        self.CMDS.update(ArduinoSerial.CMDS)
        self.ERRORS.update(ArduinoSerial.ERRORS)

    def read(self):
        """
        Overwrites read method to check whether the read value is contained in self.ERRORS.
        If so, raise a RuntimeError. If not just return read value

        Returns
        -------
        str
            Value read from serial bus

        Raises
        ------
        RuntimeError
            Value read from serial bus is an error
        """
        read_value = super().read()
        
        if read_value in self.ERRORS:
            raise RuntimeError(self.ERRORS[read_value])
        
        return read_value

    def _set_and_retrieve(self, cmd, val, exception_=RuntimeError):
        """
        Sets and retrieves a value on the Arduino firmware, represented by self.CMDS[cmd]
        The firmware is expected to return the value which was set.

        Parameters
        ----------
        cmd : str
            Command string in self.CMDS
        val : int, float, str
            The value to set
        exception_ : Exception, optional
            The exception to raise if the set and retrieved value differ, by default RuntimeError

        Raises
        ------
        exception_
            Exception is raised when set and retrieved values differ
        """
        # The self.CMDS['cmd'].lower() invokes the setter, self.CMDS['cmd'] the getter 
        ret_val = self.query(self.create_command(self.CMDS[cmd].lower(), val))
        if ret_val != str(val):
            raise exception_(f"Retrieved value for command {cmd} ({ret_val}) different from set value ({val})")

    
    def create_command(self, *args):
        """
        Create command string according to specified format.
        Arguments to this function are formatted and separated using self._DELIM
        
        Examples:
        
        self.create_command('W', 0x03, 0xFF) -> 'W:3:255:'
        self.create_command('R', 0x03) -> 'R:3:'

        Returns
        -------
        str
            Formatted command string
        """
        return f'{self.CMD_DELIMITER.join(str(a) for a in args)}{self.CMD_DELIMITER}'.encode()
