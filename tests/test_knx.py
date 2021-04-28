"""unittest for KNX implementation ``bof.layers.knx``

- KNX UDP connection
- KNX packet exchange (send/receive) and init
- Frame creation and parsing
- Frame fuzzing
"""

import unittest
from subprocess import Popen
from bof.layers import knx
from bof.base import BOFProgrammingError

UDP_ECHO_SERVER_CMD = "ncat -e /bin/cat -k -u -l 3671"

class Test01KNXConnection(unittest.TestCase):
    """Test class for KNX connection features."""
    @classmethod
    def setUpClass(self):
        self.echo_server = Popen(UDP_ECHO_SERVER_CMD.split())
    @classmethod
    def tearDownClass(self):
        self.echo_server.terminate()
        self.echo_server.wait()

    def test_0101_knxnet_instantiate(self):
        knxnet = knx.KNXnet()

    def test_0102_knxnet_connect(self):
        knxnet = knx.KNXnet()
        knxnet.connect("localhost")
        self.assertEqual(knxnet.source_address, "127.0.0.1")
        knxnet.disconnect()

class Test02KNXExchange(unittest.TestCase):
    """Test class for KNX datagram exchange.
    Prerequisites: KNXnet class instantiated, connect and disconnect OK.
    """
    @classmethod
    def setUpClass(self):
        self.knxnet = knx.KNXnet()
        self.echo_server = Popen(UDP_ECHO_SERVER_CMD.split())
    def setUp(self):
        self.knxnet.connect("localhost")
    def tearDown(self):
        self.knxnet.disconnect()
    @classmethod
    def tearDownClass(self):
        self.echo_server.terminate()
        self.echo_server.wait()

    def test_0201_knxnet_send_knxpacket(self):
        """Test that we can send frames in BOF format."""
        frame_bof = knx.KNXPacket()
        sent = self.knxnet.send(frame_bof)
        self.assertEqual(sent, 6)

    def test_0202_knxnet_send_knxpacket(self):
        """Test that we can send frames in Scapy format."""
        from bof.layers.raw_scapy.knx import KNX, KNXDescriptionRequest
        frame_sca = KNX()/KNXDescriptionRequest()
        recv = self.knxnet.send(frame_sca)
        self.assertEqual(recv, 14)

    def test_0203_knxnet_send_raw(self):
        """Test that we can send frames in bytes directly."""
        frame = b'\x06\x10\x02\x03\x00\x0e\x08\x01\x00\x00\x00\x00\x00\x00'
        recv = self.knxnet.sr(frame)
        self.assertEqual(bytes(recv[0]), frame)

    def test_0204_knxnet_receive(self):
        """Test that received bytes are converted to ``KNX``s."""
        frame = b'\x06\x10\x02\x03\x00\x0e\x08\x01\x00\x00\x00\x00\x00\x00'
        recv = self.knxnet.sr(frame)
        self.assertTrue(isinstance(recv[0], knx.KNXPacket))

class Test03KNXFrameConstructor(unittest.TestCase):
    """Test class for KNX datagram building using BOF's KNX classes.
    KNX implementation classes inherit from ``BOFPacket`` and make a
    correspondence between BOF content and protocol implementation in Scapy.
    """
    def test0301_knx_empty_packet(self):
        """Test that we can instantiate an empty KNX packet."""
        frame = knx.KNXPacket()
        header_fields = ['header_length', 'protocol_version',
                        'service_identifier', 'total_length']
        self.assertEqual([x.name for x in frame.fields], header_fields)

    def test0302_knx_req_type_from_construct_dict(self):
        """Test that we can create a KNX packet with its type from a dict."""
        frame = knx.KNXPacket(type=knx.SID.description_request)
        self.assertEqual(frame.service_identifier, 0x0203)

    def test0303_knx_req_type_from_construct_str(self):
        """Test that we can create a KNX packet with its type as a string."""
        frame = knx.KNXPacket(type="DESCRIPTION REQUEST")
        self.assertEqual(frame.service_identifier, 0x0203)

    def test0304_knx_req_type_from_construct_bytes(self):
        """Test that we can create a KNX packet with its type as value in bytes."""
        frame = knx.KNXPacket(type=b"\x02\x03")
        self.assertEqual(frame.type, "DESCRIPTION_REQUEST")

    def test0305_knx_req_type_from_construct_scapy(self):
        """Test that we can create a KNX packet with its type in scapy."""
        from bof.layers.raw_scapy.knx import KNX, KNXDescriptionRequest
        frame = knx.KNXPacket(scapy_pkt=KNX()/KNXDescriptionRequest())
        self.assertEqual(bytes(frame),
                         b'\x06\x10\x02\x03\x00\x0e\x08\x01\x00\x00\x00\x00\x00\x00')

    def test0306_knx_req_type_from_construct_invalid_str(self):
        """Test that we cannot create a KNX packet with invalid type as string."""
        with self.assertRaises(BOFProgrammingError):
            frame = knx.KNXPacket(type="NUL")

    def test0307_knx_req_type_from_construct_invalid_bytes(self):
        """Test that we cannot create a KNX packet with invalid type as bytes."""
        with self.assertRaises(BOFProgrammingError):
            frame = knx.KNXPacket(type=b"\x00\x01")

    def test0308_knx_req_type_from_construct_empty(self):
        """Test that we can create a KNX packet with empty type."""
        frame = knx.KNXPacket(type="")
        self.assertEqual(frame.service_identifier, None)

    def test_0309_knx_packet_header_attribute(self):
        """Test that we can create KNX packet and set value to a reachable field."""
        frame = knx.KNXPacket(type=knx.SID.description_request, service_identifier=0x0201)
        self.assertEqual(frame.service_identifier, 0x0201)

    def test_0310_knx_packet_deeper_attribute(self):
        """Test that we can create KNX packet and set value to any field."""
        frame = knx.KNXPacket(type=knx.SID.description_request, ip_address="192.168.1.1")
        self.assertEqual(frame.scapy_pkt.control_endpoint.ip_address, "192.168.1.1")
        self.assertEqual(frame.control_endpoint.ip_address, "192.168.1.1")

    def test_0311_knx_packet_scapy_attribute(self):
        """Test that we can create KNX packet and set a Scapy packet as attr."""
        from bof.layers.raw_scapy.knx import HPAI
        my_hpai = HPAI(ip_address="192.168.1.2")
        frame = knx.KNXPacket(type=knx.SID.description_request, control_endpoint=my_hpai)
        self.assertEqual(frame.ip_address, "192.168.1.2")
        self.assertEqual(frame["ip_address"], b"\xc0\xa8\x01\x02")

class Test04KNXCEMIFrameConstructor(unittest.TestCase):
    """Test class for KNX datagram building with cEMI included.
    KNX implementation classes inherit from ``BOFPacket`` and make a
    correspondence between BOF content and protocol implementation in Scapy.
    We must make sure that cEMI-related content is correctly relayed.
    """
    def test0401_knx_packet_empty_cemi(self):
        """Test that we can instantiate a KNX packet with no cEMI."""
        from bof.layers.raw_scapy.knx import LcEMI
        frame = knx.KNXPacket(type=knx.SID.tunneling_request)
        self.assertTrue(isinstance(frame.cemi.cemi_data, LcEMI))

    def test0402_knx_req_cemi_from_construct_dict(self):
        """Test that we can create a KNX packet using cEMI from a dict."""
        frame = knx.KNXPacket(type=knx.SID.configuration_request,
                              cemi=knx.CEMI.propread_req)
        self.assertEqual(frame.cemi.message_code, 0xfc)

    def test0403_knx_req_cemi_from_construct_str(self):
        """Test that we can create a KNX packet using cEMI type as a string."""
        frame = knx.KNXPacket(type="CONFIGURATION REQUEST",
                              cemi="PropWrite.req")
        self.assertEqual(frame.cemi.message_code, 0xf6)

    def test0404_knx_req_cemi_from_construct_bytes(self):
        """Test that we can create a KNX packet using cEMI as value in bytes."""
        frame = knx.KNXPacket(type=b"\x04\x20", cemi=b"\x2e")
        self.assertEqual(frame.cemi.message_code, knx.CEMI.l_data_con)

    def test0405_knx_req_cemi_with_other_type(self):
        """Test that we cannot create a KNX packet if cEMI not in type."""
        with self.assertRaises(BOFProgrammingError):
            frame = knx.KNXPacket(type=knx.SID.description_response,
                              cemi=knx.CEMI.propread_con)

    def test0406_knx_req_cemi_from_construct_invalid_str(self):
        """Test that we cannot create a KNX packet with invalid cemi as string."""
        with self.assertRaises(BOFProgrammingError):
            frame = knx.KNXPacket(type=knx.SID.tunneling_request, cemi="nul")

    def test0407_knx_req_cemi_from_construct_invalid_bytes(self):
        """Test that we cannot create a KNX packet with invalid cemi as bytes."""
        with self.assertRaises(BOFProgrammingError):
            frame = knx.KNXPacket(type=knx.SID.tunneling_request, cemi=b"\x80")

    def test0308_knx_req_type_from_construct_empty(self):
        """Test that we can create a KNX packet with empty type and cemi."""
        frame = knx.KNXPacket(type="", cemi="")
        self.assertEqual(frame.service_identifier, None)
        with self.assertRaises(AttributeError):
            raw(frame.cemi)

    def test_0309_knx_packet_header_attribute(self):
        """Test that we can create KNX packet and set value to a cemi field."""
        frame = knx.KNXPacket(type=knx.SID.configuration_request,
                              cemi=knx.CEMI.l_data_req, data=4)
        self.assertEqual(frame.cemi.cemi_data.data, 4)
        raw(frame) # Should raise if wrong

class Test05FrameAttributes(unittest.TestCase):
    """Test class for KNX objects acess to subpackets a fields with attributes."""
    def test_0501_knx_attr_direct_read(self):
        """Test that we can directly access the attribute of a packet."""
        frame = knx.KNXPacket(type=knx.SID.search_request)
        self.assertEqual(frame.service_identifier, 0x0201)

    def test_0502_knx_attr_direct_read(self):
        """Test that we can directly change the attribute of a packet."""
        frame = knx.KNXPacket()
        frame.service_identifier = b"\x02\x01"
        self.assertEqual(frame.service_identifier, b"\x02\x01")

    def test_0503_knx_attr_deeper_read(self):
        """Test that we can directly access the attribute of a packet."""
        frame = knx.KNXPacket(type=knx.SID.description_request, port=60000)
        self.assertEqual(frame.scapy_pkt.control_endpoint.port, 60000)
        self.assertEqual(frame.port, 60000)
        self.assertEqual(frame["port"], b"\xea\x60")

    def test_0504_knx_attr_deeper_write(self):
        """Test that we can directly change the attribute of a packet."""
        frame = knx.KNXPacket(type=knx.SID.description_request)
        frame.control_endpoint.ip_address = "192.168.1.1"
        self.assertEqual(frame.control_endpoint.ip_address, "192.168.1.1")
        self.assertEqual(frame.scapy_pkt.control_endpoint.ip_address, "192.168.1.1")
        self.assertEqual(frame["ip_address"], b'\xc0\xa8\x01\x01')

    def test_0505_knx_attr_deeper_write_scapyrejected(self):
        """Test that we can directly change the attribute of a packet."""
        frame = knx.KNXPacket(type=knx.SID.description_request)
        frame.ip_address = "hi mark!"
        self.assertEqual(frame.control_endpoint.ip_address, "hi mark!")
        self.assertEqual(frame.scapy_pkt.control_endpoint.ip_address, "hi mark!")
        self.assertEqual(frame["ip_address"], b"hi mark!")

    def test_0506_knx_attr_as_bytes(self):
        """Test that we can set a value directly as bytes using bof_pkt[field]"""
        frame = knx.KNXPacket(type=knx.SID.description_request)
        frame["ip_address"] = b'\xc0\xa8\x01\x2a'
        self.assertEqual(frame.control_endpoint.ip_address, "192.168.1.42")
        self.assertEqual(frame.scapy_pkt.control_endpoint.ip_address, "192.168.1.42")
        self.assertEqual(frame["ip_address"], b'\xc0\xa8\x01\x2a')
        raw(frame) # Should raise if wrong
