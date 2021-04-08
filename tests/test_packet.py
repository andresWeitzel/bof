"""unittest for ``bof.packet``

- BOFPacket and BOFPacket child class initialization
- Link between BOFPacket classes and Scapy objects below
- BOFPacket-inherited objects handling and usage
"""

import unittest

from scapy.layers.inet import TCP
from scapy.fields import PacketField, ByteField
from scapy.contrib.modbus import ModbusADURequest

from bof.packet import *


class Test01PacketConstruct(unittest.TestCase):
    """Test class for raw BOFPacket initialization.
    BOFPacket are not supposed to be instantiated directly.
    """

    def test_0101_bofpacket_construct(self):
        """Test empty constructor."""
        pkt = BOFPacket()
        self.assertEqual(pkt.name, "BOFPacket")

    def test_0102_bofpacket_child_construct(self):
        """Test that we can build an object inheriting from BOFPacket."""

        class OtterPacket(BOFPacket):
            pass

        pkt = OtterPacket()
        self.assertEqual(pkt.name, "OtterPacket")


class Test02ScapyLayers(unittest.TestCase):
    """Test class to make sure that we access Scapy layer content."""

    def test_0201_bofpacket_scapylayer_integrated(self):
        """Test that we can build BOFPacket from layer in scapy library."""
        class Modbus(BOFPacket):
            def __init__(self):
                self.scapy_pkt = ModbusADURequest()

        modbus_pkt = Modbus()
        self.assertEqual(modbus_pkt.name, "ModbusADU")

    def test_0202_bofpacket_scapylayer_standalone(self):
        """Test that we can build BOFPacket from layer as standalone file.
        The standalone file shall have a protocol written with scapy format.
        """
        from bof.layers.raw_scapy import knx
        class KNX(BOFPacket):
            def __init__(self):
                self.scapy_pkt = knx.KNXnetIP()

        knx_pkt = KNX()
        self.assertEqual(knx_pkt.scapy_pkt.name, "KNXnet/IP")

    def test_0203_bofpacket_scapylayer_addpayload_base_scapy(self):
        """Test that we can add a Scapy layer as a payload for a BOFPacket."""
        # We want ModbusADURequest as payload for TCP, which are bound by
        # default in Scapy
        pkt = BOFPacket()
        pkt.scapy_pkt = TCP()
        pkt.add_payload(ModbusADURequest())
        # See if there is a better way to test than existence in show2..
        show = pkt.scapy_pkt.show2(dump=True)
        self.assertEqual("transId   = 0x0" in show, True)  # could be done with regex..

    def test_0204_bofpacket_scapylayer_addpayload_base_bof(self):
        """Test that we can add a BOFPacket as payload for another BOFPacket."""
        # we want ModbusADURequest as payload for TCP, which are bound by
        # default in Scapy
        pkt = BOFPacket()
        pkt.scapy_pkt = TCP()
        pkt.add_payload(ModbusADURequest())
        # see if there is a better way to test than existence in show2..
        show = pkt.show2(dump=True)
        self.assertEqual("transId   = 0x0" in show, True)  # could be done with regex..

    def test_0205_bofpacket_scapylayer_addpayload_automatic_scapy(self):
        """Test that we can bind an unbound Scapy packet as payload."""
        from scapy.layers.inet import UDP
        # we want TCP as payload for ModbusADURequest, which are not bound by
        # default in Scapy
        pkt = BOFPacket()
        pkt.scapy_pkt = UDP()
        pkt.add_payload(TCP(), automatic_binding=True)
        # see if there is a better way to test than existence in show2..
        show = pkt.show2(dump=True)
        self.assertEqual("ack       = 0" in show, True)  # could be done with regex..

    def test_0206_bofpacket_scapylayer_addpayload_automatic_guess_scapy(self):
        """Test that we can bind an unbound Modbus Scapy packet as payload.
        In this specific case guess_payload_class is redefined in
        ModbusADURequest so won't work by default.
        """
        # we want TCP as payload for ModbusADURequest, which are not bound by
        # default in Scapy
        pkt = BOFPacket()
        pkt.scapy_pkt = ModbusADURequest()
        pkt.add_payload(TCP(sport=12345), automatic_binding=True)
        # see if there is a better way to test than existence in show2..
        show = pkt.show2(dump=True)
        self.assertIn("sport   = 12345", show)


class Test03PacketBuiltins(unittest.TestCase):
    """Test class for raw BOFPacket builtin function overload."""

    @classmethod
    def setUpClass(self):
        self.pkt = BOFPacket()

    def test_0301_bofpacket_bytes(self):
        """Test that bytes() prints Scapy packet bytes."""
        self.assertEqual(bytes(self.pkt), b"")  # TODO

    def test_0302_bofpacket_len(self):
        """Test that len() prints Scapy packet length."""
        self.assertEqual(len(self.pkt), 0)  # TODO

    def test_0302_bofpacket_str(self):
        """Test that str() prints Scapy packet string."""
        self.assertEqual(str(self.pkt), "BOFPacket: BOFPacket")

    def test_0302_bofpacket_iter(self):
        """Test that str() prints Scapy packet fields."""
        self.assertEqual([x.name for x in self.pkt], [])  # TODO


class Test04PacketManipulations(unittest.TestCase):
    """Test class for dynamically manipulate packet content.
    (ex : add fields).
    """

    @classmethod
    def setUpClass(self):
        self.bof_pkt = BOFPacket()

    def test_0401_bofpacket_scapylayer_addfield(self):
        """Test that we can add a new field at the end of existing BOFPacket."""
        self.bof_pkt.add_field(ByteField("new_field", 0x01))
        self.assertEqual(self.bof_pkt.scapy_pkt.new_field, 0x01)

    def test_0402_bofpacket_scapylayer_addfield_value(self):
        """Test that we can add a new field to BOFPacket with a specified value."""
        self.bof_pkt.add_field(ByteField("new_field", 0x01), 0x02)
        self.assertEqual(self.bof_pkt.scapy_pkt.new_field, 0x02)

    def test_0403_bofpacket_scapylayer_addfield_packet(self):
        """Test that we can add a Packet Field at the end of existing BOFPacket."""
        self.bof_pkt.add_field(PacketField("new_packet_field", TCP(sport=12345), TCP))
        self.assertEqual(self.bof_pkt.scapy_pkt.new_packet_field.sport, 12345)
