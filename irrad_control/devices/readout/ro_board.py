from threading import Thread, Event

# Package imports
from . import ro_board_config
from ..ic.TCA9555.tca9555 import TCA9555


class IrradDAQBoard(object):

    def __init__(self, version='v0.1', address=0x20):

        # Check for version support
        if version not in ro_board_config:
            raise ValueError("{} not supported. Supported versions are {}".format(version, ', '.join(ro_board_config.keys())))

        # Initialize the interface to the board via I2C
        self._intf = TCA9555(address=address)

        # Store the board config
        self.config = ro_board_config[version]

        # Related to temperature channel cycling
        self.temp_channel = None
        self._temp_channel_cycle_thread = None
        self._stop_temp_channel_cycle_flag = Event()

        # Setup the initial state of the board
        self._setup_defaults()

    def _setup_defaults(self):

        # Set the direction (in or output) of the pins
        self._intf.set_direction(direction=0, bits=self.config['defaults']['output'])
        self._intf.set_direction(direction=1, bits=self.config['defaults']['input'])

        # Set the input current scale IFS
        self.set_ifs(group='sem', ifs=self.config['defaults']['sem_ifs'])
        # Set the input current scale
        self.set_ifs(group='ch12', ifs=self.config['defaults']['ch12_ifs'])

        self.set_temp_channel(channel=self.config['defaults']['temp_ch'])

    @property
    def jumper_scale(self):
        return self.config['jumper_scale']

    @jumper_scale.setter
    def jumper_scale(self, js):
        if js not in (1, 10):
            raise ValueError('The input jumper scales the full-scale current range (IFS) either by 1 or 10.')
        self.config['jumper_scale'] = js

    @property
    def gpio_value(self):
        return self._intf.int_from_bits(bits=self.config['pins']['gpio'])

    @gpio_value.setter
    def gpio_value(self, val):
        self._intf.int_to_bits(bits=self.config['pins']['gpio'], val=val)

    def set_mux_value(self, group, val):

        self._intf.int_to_bits(self.config['pins'][group], val=val)

    def get_mux_value(self, group):

        return self._intf.int_from_bits(bits=self.config['pins'][group])

    def get_temp_channel(self, cached=False):

        if self.temp_channel is None or not cached:
            self.temp_channel = self._intf.int_from_bits(bits=self.config['pins']['temp'])

        return self.temp_channel

    def set_temp_channel(self, channel):

        self._intf.int_to_bits(bits=self.config['pins']['temp'], val=channel)

        self.temp_channel = channel

    def set_ifs(self, group, ifs):

        ifs_idx = self.config['ifs_scales'].index(ifs / self.config['jumper_scale'])

        self._intf.int_to_bits(self.config['pins'][group], val=ifs_idx)

    def get_ifs(self, group):

        ifs_idx = self._intf.int_from_bits(bits=self.config['pins'][group])

        return self.config['ifs_scales'][ifs_idx] * self.config['jumper_scale']

    def get_ifs_label(self, group):

        ifs_idx = self._intf.int_from_bits(bits=self.config['pins'][group])

        return self.config['ifs_labels'][ifs_idx] if self.config['jumper_scale'] == 1 else self.config['ifs_labels_10'][ifs_idx]

    def _check_and_map_gpio(self, pins):

        pins = [pins] if isinstance(pins, int) else pins

        if any(not 0 <= p < len(self.config['pins']['gpio']) for p in pins):
            raise IndexError("GPIO pins are indexed from {} to {}".format(0, len(self.config['pins']['gpio']) - 1))

        return [self.config['pins']['gpio'][p] for p in pins]

    def set_gpio_pins(self, pins):

        self._intf.set_bits(bits=self._check_and_map_gpio(pins=pins))

    def unset_gpio_pins(self, pins):

        self._intf.unset_bits(bits=self._check_and_map_gpio(pins=pins))

    def is_cycling_temp_channels(self):
        return False if self._temp_channel_cycle_thread is None else self._temp_channel_cycle_thread.is_alive()

    def stop_cycle_temp_channels(self):
        if not self.is_cycling_temp_channels():
            return
        self._stop_temp_channel_cycle_flag.set()
        self._temp_channel_cycle_thread.join()

    def cycle_temp_channels(self, channels, timeout=None):

        self._temp_channel_cycle_thread = Thread(target=self._cycle_temp_channels, args=(channels, timeout))
        self._temp_channel_cycle_thread.start()

    def _cycle_temp_channels(self, channels, timeout=None):

        n_channels = len(channels)
        ch_idx = 0
        while not self._stop_temp_channel_cycle_flag.wait(timeout=timeout):

            if not self._intf.accessing_state:
                self.set_temp_channel(channel=channels[ch_idx])
                ch_idx = ch_idx + 1 if ch_idx != n_channels - 1 else 0
