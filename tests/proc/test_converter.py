import os
import time
import logging
import unittest
import zmq
import tables as tb
import numpy as np

from irrad_control import pid_file
from irrad_control.utils.tools import load_yaml
from irrad_control.analysis.utils import load_irrad_data
from irrad_control.processes.converter import IrradConverter 



class TestConverter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.context = zmq.Context()

        cls.fixture_path = os.path.join(os.path.dirname(__file__), '../fixtures')
        cls.test_base = os.path.join(cls.fixture_path, f'test_irradiation_multipart_part_1')

        # Load the data
        cls.data, cls.config = load_irrad_data(data_file=cls.test_base+'.h5',
                                               config_file=cls.test_base+'.yaml',
                                               subtract_raw_offset=False)
        
        # Make output dir
        cls.output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'output'))
        if not os.path.isdir(cls.output_dir):
            os.mkdir(cls.output_dir)

        # Create and start process
        cls.converter = IrradConverter(name='TestConverterProcess')
        cls.converter.start()    

        # Wait until process is created with irrad_control.pid file
        start = time.time()
        while not os.path.isfile(pid_file):
            time.sleep(1)

            # Wait max 30 seconds
            if time.time() - start > 30:
                break

        assert os.path.isfile(pid_file)

        cls.pid_content = load_yaml(pid_file)

        # Overwrite outfile in session
        cls.config['session']['outfile'] = os.path.join(cls.output_dir, 'test_converter_outfile')

        # Overwrite server ip to localhsot
        cls.config['server']['localhost'] = cls.config['server']['131.220.221.101']
        del cls.config['server']['131.220.221.101']

        # Open socket for reqests aka send commands
        cls.cmd_req = cls.context.socket(zmq.REQ)
        cls.cmd_req.connect(f"tcp://localhost:{cls.pid_content['ports']['cmd']}")
        cls.data_pub = cls.context.socket(zmq.PUB)
        cmd_port = cls.data_pub.bind_to_random_port(addr='tcp://*')
        # Add 'ports' to config so the converter knows where the data comes from 
        cls.config['server']['localhost']['ports'] = {'data': cmd_port}

    @classmethod
    def tearDownClass(cls):
        
        # Delete files
        for root, _, files in os.walk(cls.output_dir):
            for fname in files:
                os.remove(os.path.join(root, fname))
        os.rmdir(cls.output_dir)

        time.sleep(1)

    @classmethod
    def _send_cmd_get_reply(self, target, cmd, cmd_data=None,):
        
        # Send command dict and wait for reply
        self.cmd_req.send_json({'target': target, 'cmd': cmd, 'data': cmd_data})

        return self.cmd_req.recv_json()

    def test_raw_data_conversion(self):

        # Start converter interpretation loop
        converter_start_reply = self._send_cmd_get_reply(target='interpreter', cmd='start', cmd_data=self.config)
        
        # Allow some time for converter to setup sockets etc
        time.sleep(1)

        # Assert that PIDs are the same
        assert converter_start_reply['data'] == self.pid_content['pid']

        meta = {'timestamp': 0, 'name': 'localhost', 'type': 'raw_data'}
        data = {ch: None for ch in self.config['server']['localhost']['readout']['channels']}
        data_dtype_names = [n for n in self.data['Server_1']['Raw'].dtype.names if n != 'timestamp']

        # Loop over raw data
        for raw in self.data['Server_1']["Raw"]:
            meta['timestamp'] = float(raw['timestamp'])
            for dtname in data_dtype_names:
                data[dtname] = float(raw[dtname])
            self.data_pub.send_json({'meta': meta, 'data': data})
            
            time.sleep(0.005)  # Emulate ~200 Hz data rate

        # Send shutdown command
        self._send_cmd_get_reply(target='interpreter', cmd='shutdown')    
        
        # Wait for converter to finish
        self.converter.join()

        # Check pid file is gone
        assert not os.path.isfile(pid_file)

        # Open output file
        out_data, _ = load_irrad_data(data_file=self.config['session']['outfile']+'.h5',
                                      config_file=self.test_base+'.yaml',
                                      subtract_raw_offset=False)

        assert len(out_data['Server_1']) == len(self.data['Server_1'])
        assert len(out_data['Server_1']['Raw']) == len(self.data['Server_1']['Raw'])
        assert np.array_equal(out_data['Server_1']['Raw'], self.data['Server_1']['Raw'])
        
               
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - [%(levelname)-8s] (%(threadName)-10s) %(message)s")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConverter)
    unittest.TextTestRunner(verbosity=2).run(suite)