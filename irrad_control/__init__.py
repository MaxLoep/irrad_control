# Different errrors are raised in Python2/3
try:
    ModuleNotFoundError  # Python >= 3.6
except NameError:
    ModuleNotFoundError = ImportError  # Python < 3.6

try:
    import yaml
    _YAML = True  # irrad_control on DAQ / Host PC
except ModuleNotFoundError:
    _YAML = False  # irrad_control on server

if _YAML:

    # Imports
    import os
    from collections import OrderedDict

    # Paths
    package_path = os.path.dirname(__file__)
    config_path = os.path.join(package_path, 'config')

    # Shell script to config server
    config_server_script = os.path.join(package_path, 'configure_server.sh')

    # Load network and data acquisition config
    with open(os.path.join(config_path, 'network_config.yaml'), 'r') as _nc:
        network_config = yaml.safe_load(_nc)

    with open(os.path.join(config_path, 'daq_config.yaml'), 'r') as _dc:
        daq_config = yaml.safe_load(_dc)

    # Keep track of xy stage travel and known positions
    if not os.path.isfile(os.path.join(package_path, 'devices/stage/xy_stage_config.yaml')):
        # Open xy stats template and safe a copy
        with open(os.path.join(config_path, 'xy_stage_config.yaml'), 'r') as _xys_l:
            _xy_stage_config_tmp = yaml.safe_load(_xys_l)

        with open(os.path.join(package_path, 'devices/stage/xy_stage_config.yaml'), 'w') as _xys_s:
            yaml.safe_dump(_xy_stage_config_tmp, _xys_s)

    with open(os.path.join(package_path, 'devices/stage/xy_stage_config.yaml'), 'r') as _xys:
        xy_stage_config = yaml.safe_load(_xys)
