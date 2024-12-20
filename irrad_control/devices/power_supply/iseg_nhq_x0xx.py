from irrad_control.devices.serial_device import SerialDevice


class IsegNHQx0xx(SerialDevice):

    # Command references from protocol
    CMDS = {
        'get_identifier': '#',
        'set_break_time': 'W={value}',
        'get_break_time': 'W',
        'get_voltage_meas': 'U{channel}',
        'get_current_meas': 'I{channel}',
        'get_v_lim': 'M{channel}',
        'get_i_lim': 'N{channel}',
        'get_voltage_set': 'D{channel}',
        'set_voltage': 'D{channel}={value}',
        'get_ramp_speed': 'V{channel}',
        'set_ramp_speed': 'V{channel}={value}',
        'start_voltage_change': 'G{channel}',
        'set_current_trip': 'L{channel}={value}',
        'get_current_trip': 'L{channel}',
        'get_status_word': 'S{channel}',
        'get_module_status': 'T{channel}',
        'set_autostart': 'A{channel}={value}',
        'get_autostart': 'A{channel}'
        }

    ERRORS = {
        '????': 'Syntax error in command',
        '?WCN': 'Wrong channel number',
        '?TOT': 'Timeout error (Unit will re-initialise)'
    }

    STATUS = {
        'ON': "Output voltage according to set voltage",
        'OFF': "Channel front panel switch off",
        'MAN': "Channel is on, set to manual mode",
        'ERR': "V_MAX or I_MAX was exceeded",
        'INH': "Inhibit signal was / is active",
        'QUA': "Quality of output voltage no guaranteed at present",
        'L2H': "Output voltage increasing",
        'H2L': "Output voltage decreasing",
        'LAS': "Look at status (only after G-command)",
        'TRP': "Current trip was active"
    }

    WRITE_TERMINATION = '\r\n'
    READ_TERMINATION = '\r\n'

    @property
    def identifier(self):
        """
        Read module identifier; return format is "UNIT_NUMBER;SOFTWARE_REL;V_MAX;I_MAX"

        Returns
        -------
        str
            Module identifier
        """
        return self._get_set_property(prop='get_identifier')

    @property
    def break_time(self):
        """
        Break time (better 'delay') in between two output characters from the power supply in milliseconds.
        Valid values are 1 up to and including 255 ms

        Returns
        -------
        int
            break time in ms (uint8)
        """
        return int(self._get_set_property(prop='get_break_time'))

    @break_time.setter
    def break_time(self, bt):
        if not 1 <= bt <= 255:
            raise ValueError("Break time must be 1 <= break_time <= 255 ms")
        self._get_set_property(prop='get_break_time', value=bt)

    @property
    def voltage(self):
        """
        Actual voltage at self.channel output in V

        Returns
        -------
        float
            Output voltage in V
        """
        return float(self._get_set_property(prop='get_voltage_meas'))

    @voltage.setter
    def voltage(self, voltage):
        if voltage > self.voltage_limit:
            raise ValueError(f"Value too high! Maximum allowed voltage is {self.voltage_limit} V")
        self._get_set_property(prop='set_voltage', value=voltage)

    @property
    def voltage_target(self):
        """
        Target voltage of self.channel output in V
        This is the voltage which is set using self.voltage property

        Returns
        -------
        float
            Target voltage in V
        """
        return float(self._get_set_property(prop='get_voltage_set'))

    @property
    def current(self):
        """
        Actual current flowing at output of self.channel in A

        Returns
        -------
        float
            Output current in A
        """
        return float(self._get_set_property(prop='get_current_meas'))

    @property
    def voltage_limit(self):
        """
        Return current voltage limit of self.channel in V

        Returns
        -------
        float
            Voltage limit in V
        """
        # Property get_v_lim returns voltage limit as percentage of max voltage 
        return int(self._get_set_property(prop='get_v_lim')) / 100.0 * float(self.V_MAX[:-1])

    @property
    def current_limit(self):
        """
        Return current limit of self.channel in A

        Returns
        -------
        float
            Current limit in A
        """
        # Property get_i_lim returns voltage limit as percentage of max current 
        return int(self._get_set_property(prop='get_i_lim')) / 100.0 * float(self.I_MAX[:-2])

    @property
    def ramp_speed(self):
        """
        Read the output voltage ramping speed in V/s.
        Valid values are 1 up to and including 255 V/s

        Returns
        -------
        int
            Ramp speed of output voltage
        """
        return int(self._get_set_property(prop='get_ramp_speed'))

    @ramp_speed.setter
    def ramp_speed(self, rs):
        if not 1 <= rs <= 255:
            raise ValueError("Ramp speed must be 1 <= ramp_speed <= 255 V/s")
        self._get_set_property(prop='set_ramp_speed', value=rs)

    @property
    def current_trip(self):
        """
        Read current trip, if 0 -> no trip

        Returns
        -------
        int
            Current trip
        """
        return int(self._get_set_property(prop='get_current_trip'))

    @current_trip.setter
    def current_trip(self, ct):
        self._get_set_property(prop='set_current_trip', value=ct)

    @property
    def status_word(self):
        """
        Read status word of self.channel
        See self.STATUS and self.status_description

        Returns
        -------
        str
            Status word
        """
        return self._get_set_property(prop='get_status_word')

    @property
    def status_description(self):
        """
        Read description corresponding to self.status_word

        Returns
        -------
        str
            Status description
        """
        status_word = self.status_word
        for status in self.STATUS:
            if status in status_word:
                return f"{status_word}: {self.STATUS[status]}"
        return 'No description'
        
    @property
    def module_status(self):
        """
        Read module status of self.channel
        Return value is uint8, use '{:08b}'.format(value) to get bits

        Returns
        -------
        int
            Value of status
        """
        return '{:08b}'.format(int(self._get_set_property(prop='get_module_status')))

    @property
    def module_description(self):
        """
        Read module status and print out desciptive string from it

        Returns
        -------
        str
            Module description string
        """
        module_msg = lambda bit, prefix, t_msg, f_msg='': f'{prefix} ' + (t_msg if bit == '1' else f_msg)
        _description = {
            0: lambda b: module_msg(bit=b, prefix='', t_msg="Quality of output voltage not given at present"),
            1: lambda b: module_msg(bit=b, prefix='', t_msg="V_MAX or I_MAX is / was exceeded"),
            2: lambda b: module_msg(bit=b, prefix='INHIBIT signal', t_msg="is / was active", f_msg="inactive"),
            3: lambda b: module_msg(bit=b, prefix="KILL_ENABLE is", t_msg="on", f_msg="off"),
            4: lambda b: module_msg(bit=b, prefix="Front-panel HV-ON switch is", t_msg="OFF", f_msg="ON"),
            5: lambda b: module_msg(bit=b, prefix="Polarity set to", t_msg="positive", f_msg="negative"),
            6: lambda b: module_msg(bit=b, prefix="Control via", t_msg="manual", f_msg="RS-232 interface"),
            7: lambda b: module_msg(bit=b, prefix="Display dialled to", t_msg="voltage measurement", f_msg="current measurement")
        }
        module_status = self.module_status
        module_description = ''
        for i, bit in enumerate(module_status):
            module_description += _description[i](bit) + '\n'
        return module_description

    @property
    def autostart(self):
        """
        Whether output voltage changes automatically after setting value via self.voltage property.
        Alternatively, call self.start_voltage_change method to initaite voltagte change manually.
        self._get_set_property(prop='get_autostart') -> 008: autostart is active
        self._get_set_property(prop='get_autostart') -> 000: autostart is inactive

        Returns
        -------
        bool
            Wheter autostart is active
        """
        return self._get_set_property(prop='get_autostart') == '008'

    @autostart.setter
    def autostart(self, state):
        self._get_set_property(prop='set_autostart', value=8 if state else 0)

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, ch):
        if not 1 <= ch <= self.n_channel:
            raise ValueError(f"Channel number must be 1 <= channel <= {self.n_channel}")
        self._channel = ch

    @property
    def UNIT_NUMBER(self):
        return self.identifier.split(';')[0]

    @property
    def SOFTWARE_REL(self):
        return self.identifier.split(';')[1]

    @property
    def V_MAX(self):
        return self.identifier.split(';')[2]
    
    @property
    def I_MAX(self):
        return self.identifier.split(';')[3]

    def __init__(self, port, n_channel, high_voltage=None):
        super().__init__(port=port, baudrate=9600)

        # Store current channel number; default to channel 1
        self._channel = None
        # Store number of channels
        self.n_channel = n_channel
        self.channel = 1

        # Important: The manual states that the default break time is 3 ms.
        # When querying the break_time property, it returns 0 although only values in between 1 and 255 ms are valid.
        # Queries take very long which leads to serial timeouts. I suspect the default value on firmware side is in fact 255 ms (not 3 ms).
        # Therefore, setting the break_time as first thing in the __init__ is absolutely REQUIRED
        self.break_time = 1  # ms
        
        # Add error response for attempting to set voltage too high
        self.ERRORS[f'? UMAX={self.voltage_limit}'] = "Set voltage exceeds voltage limit"

        # Voltage which is considered the high voltage
        self.high_voltage = high_voltage

    def _get_set_property(self, prop, value=None):
        
        if '{channel}' in self.CMDS[prop] and '{value}' in self.CMDS[prop]: 
            cmd = self.CMDS[prop].format(channel=self.channel, value=value)
        elif '{channel}' in self.CMDS[prop]: 
            cmd = self.CMDS[prop].format(channel=self.channel)
        elif '{value}' in self.CMDS[prop]:
            cmd = self.CMDS[prop].format(value=value)
        else:
            cmd = self.CMDS[prop]
        
        return self.query(cmd)

    def query(self, msg):
        """
        Queries a message *msg* and reads the answer

        Parameters
        ----------
        msg : str, bytes
            Message to be queried

        Returns
        -------
        str
            Decoded, stripped string, read from serial port
        """
        # TODO: Manual states that character by character have to be sent and echoed, check that
        echo = super().query(msg)
        if echo != msg:
            raise RuntimeError(f"Issued command ({msg}) and echoed command ({echo}) differ.")
        return self.read()

    def start_voltage_change(self):
        """
        Manually initiate the change of the voltage.
        Only needed if self.autostart is False
        """
        self._get_set_property(prop='start_voltage_change')

    def hv_on(self):
        try:
            _ = float(self.high_voltage)
            self.voltage = self.high_voltage
        except TypeError:
            raise ValueError("High voltage is not set. Set *high_voltage* attribute to numerical value")

    def hv_off(self):
        self.voltage = 0
