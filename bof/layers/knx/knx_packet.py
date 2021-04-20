"""
KNXPacket
---------

This class inheriting from ``BOFPacket`` is the interface between BOF's usage
of KNX by the end user and an actual Scapy packet built using KNX's
implementation in Scapy format.

In BOFPacket and KNXPacket, several builtin methods and attributes are just
relayed to the Scapy Packet underneath. We also want to let the user interact
directly with the Scapy packet if she wants, using ``scapy_pkt`` attribute.

Example::

    >>> from bof.layers.knx import *
    >>> packet = KNXPacket(type=SID.description_request)
    >>> packet
    <bof.layers.knx.knx_packet.KNXPacket object at 0x7ff74224add8>
    >>> packet.scapy_pkt
    <KNX  service_identifier=DESCRIPTION_REQUEST |<KNXDescriptionRequest  \
    control_endpoint=<HPAI  |> |>>
"""

# Scapy
from scapy.packet import Packet
# Internal
from bof.layers.raw_scapy import knx as scapy_knx
from bof.packet import BOFPacket
from bof.base import BOFProgrammingError, to_property

###############################################################################
# CONSTANTS                                                                   #
###############################################################################

# Converts Scapy KNX's SERVICE_IDENTIFIER_CODES dict with format
# {byte value: service name} to the opposite, so that the end user can call
# services by their names instead of their values.
SID = type('SID', (object,),
           {to_property(v):k.to_bytes(2, byteorder='big') \
            for k,v in scapy_knx.SERVICE_IDENTIFIER_CODES.items()})()

TYPE_FIELD = "service_identifier"

###############################################################################
# KNXPacket class                                                             #
###############################################################################

class KNXPacket(BOFPacket):
    """Builds a KNXPacket packet from a byte array or from attributes.

    :param _pkt: KNX frame as byte array to build KNXPacket from.
    :param scapy_pkt: Instantiated Scapy Packet to use as a KNXPacket.
    :param type: Type of frame to build. Ignored if ``_pkt`` set.
                 Should be a value from ``SID`` dict imported from KNX Scapy
                 implementation as a dict key, a string or as bytes.

    Example of initialization::

        pkt = KNXPacket(b"\x06\x10[...]") # From frame as a byte array
        pkt = KNXPacket(type=SID.description_request) # From service id dict
        pkt = KNXPacket(type="DESCRIPTION REQUEST") # From service id name
        pkt = KNXPacket(type=b"\x02\x03") # From service id value
        pkt = KNXPacket(scapy_pkt=KNX()/KNXDescriptionRequest()) # With Scapy Packet
        pkt = KNXPacket() # Empty packet (just a KNX header)
    """

    def __init__(self, _pkt:bytes=None, scapy_pkt:Packet=None, type:object=None, **kwargs) -> None:
        # Initialize Scapy object from bytes or as an empty KNX packet
        if _pkt or (not type and not scapy_pkt):
            self._scapy_pkt = scapy_knx.KNX(_pkt=_pkt)
        elif scapy_pkt:
            self.scapy_pkt = scapy_pkt
        else:
            self.set_type(type)
        self._set_fields(**kwargs)

    def set_type(self, ptype:object) -> None:
        """Format packet according to the specified type (service identifier).

        :param ptype: Type of frame to build. Ignored if ``_pkt`` set.
                      Should be a value from ``SID`` dict imported from KNX Scapy
                      implementation as a dict key, a string or as bytes.
        :raises BOFProgrammingError: if type is unknown or invalid.
        """
        # If type given as a string, we get the corresponding value
        if isinstance(ptype, str):
            for key, value in scapy_knx.SERVICE_IDENTIFIER_CODES.items():
                if to_property(ptype) == to_property(value):
                    ptype = key.to_bytes(2, byteorder='big')
                    break
        # Now, let's guess Packet class from received bytes.
        if not isinstance(ptype, bytes):
            raise BOFProgrammingError("Invalid type for KNXPacket ({0})".format(ptype))
        itype = int.from_bytes(ptype, byteorder="big")
        try:
            packet, = [p for f, p in scapy_knx.KNX.payload_guess if f[TYPE_FIELD] == itype]
        except ValueError:
            raise BOFProgrammingError("Unknown type for KNXPacket ({0})".format(ptype))
        self._scapy_pkt = scapy_knx.KNX(service_identifier=itype)/packet()

    @property
    def type(self) -> str:
        if self._scapy_pkt.payload:
            return self._scapy_pkt.payload.name
        if self._scapy_pkt:
            return self._scapy_pkt.name
        return self.__class__.__name__
