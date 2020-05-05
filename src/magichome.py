import colorsys
import io
import socket
import logging
from dataclasses import dataclass
from typing import Optional, Set, Union, Tuple


@dataclass
class MagicHomeControllerColorState:
    """ The color state """
    r: int
    g: int
    b: int
    w: int

    def __init__(self, r: int, g: int, b: int, w: int):
        self.r = r
        self.g = g
        self.b = b
        self.w = w

    @property
    def stream(self) -> bytearray:
        """ Return the colors as a bytearray """
        return bytearray([self.r, self.g, self.b, self.w])

    @property
    def tuple(self) -> Tuple[bytes, bytes, bytes, bytes]:
        """
        The color state in byte format
        :return:
        """
        return bytes([self.r]), bytes([self.g]), bytes([self.b]), bytes([self.w])

    @property
    def int(self) -> Tuple[int, int, int, int]:
        """
        The color state in integer format
        :return:
        """
        return self.r, self.g, self.b, self.w

    def change_brightness(self, delta: float, percentage: bool = False) -> 'MagicHomeControllerColorState':
        """
        Change the brightness using the HLS representation, and the DELTA is applied on the luminance attribute.
        :param delta:
        :param percentage: When True, the original luminance is multiplied by the delta
        :return:
        """
        if delta == 0 or delta is None:
            return self
        h, l, s = colorsys.rgb_to_hls(self.r, self.g, self.b)
        if percentage:
            l *= delta
        else:
            l += delta
        if l < 0:
            l = 0
        elif l > 255:
            l = 255
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)
        return self

    def __repr__(self) -> str:
        return f"{self.int}"


@dataclass
class MagicHomeControllerState:
    """ The controller state """

    is_on: Optional[bool]
    color: MagicHomeControllerColorState


class MagicHomeController:
    """ A controller, an easy way to interact with it. """

    __logger = logging.getLogger(__name__)

    __port: int = 5577
    """ The port used to connect to """

    __timeout = 1
    """ Wait time (seconds) for response. """

    def __init__(self, addr: str, id: Optional[str] = None, model: Optional[str] = None):
        self._addr = addr
        self._id = id
        self._model = model

    def __hash__(self):
        return hash(self._addr)

    def __repr__(self):
        res = io.StringIO("Controller")
        if self._id is not None:
            res.write(f":{self._id}")
        if self._model is not None:
            res.write(f"({self._model})")
        res.write(f"@[{self._addr}]")
        return res.getvalue()

    @property
    def addr(self) -> str:
        return self._addr.decode('utf-8')

    @property
    def id(self) -> str:
        return self._id.decode('utf-8')

    @property
    def model(self) -> str:
        return self._model.decode('utf-8')


    def __stream_checksum(self, stream: bytearray) -> bytes:
        """
        Generate the checksum for a given stream.

        :param stream:
        :return:
        """
        return bytes([sum(stream) & 0xff])

    def __str2hex(self, data: bytes) -> str:
        """
        Return the bytes in a string with their hexadecimal representations.

        :param data:
        :return:
        """
        return ''.join('\\x{:02x}'.format(x) for x in data)

    def _send(self, data: Union[bytes, bytearray], get_response: bool = False) -> Optional[bytes]:
        """
        Interact with the controller.
        It will connect, send, get an answer (when requested for) and close the connection.

        :param data: The data to be sent
        :param get_response: The controller's response
        :return: None when no response was requested or when not received in a specified time.
        Otherwise the controller's response.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._addr, self.__port))
        s.settimeout(self.__timeout)
        s.send(data)
        if not get_response:
            s.close()
            return
        try:
            response = s.recv(1024)
            self.__logger.debug(f"Response: {self.__str2hex(response)}")
        except socket.timeout:
            self.__logger.debug(f"No response. TimeOut ({self.__timeout})")
            response = None
        s.close()
        return response

    def turn_on(self) -> None:
        """
        Turn the bulb on.
        :return:
        """
        self._send(b'\x71\x23\x94')

    def turn_off(self) -> None:
        """
        Turn the bulb off.
        :return:
        """
        self._send(b'\x71\x24\x95')

    def is_on(self) -> Optional[bool]:
        """
        Is the bulb on?
        :return: None when the state wasn't possible to be determined
        """
        return self.state.is_on

    @staticmethod
    def __int2byte(i: int) -> bytes:
        """
        Convert an integer to its binary representation
        :param i:
        :return:
        """
        if i < 0:
            return b'\x00'
        if i > 255:
            return b'\xff'
        return bytes([i])

    def power_toggle(self):
        """
        Toggle the power on/off.

        :return:
        """
        is_on = self.state.is_on
        if is_on is True:
            self.turn_off()
        else:
            self.turn_on()

    def color(self, r: int, g: int, b: int, w: int) -> None:
        """
        Set the controller color output.

        :param r: Red
        :param g: Green
        :param b: Blue
        :param w: White (some controllers only)
        :return:
        """
        command = bytearray(b'\x31' +
                            self.__int2byte(r) + self.__int2byte(g) + self.__int2byte(b) + self.__int2byte(w)
                            + b'\x0f')
        command += self.__stream_checksum(command)
        self._send(command)

    @property
    def state(self) -> MagicHomeControllerState:
        """
        Get the current state
        :return:
        """
        # sleep(0.5)
        response = self._send(b'\x81\x8a\x8b\x96', True)
        if self.__logger.isEnabledFor(logging.DEBUG):
            self.__logger.debug(self.__str2hex(response))
        if bytes([response[2]]) == b'\x23':
            is_on = True
        elif bytes([response[2]]) == b'\x23':
            is_on = False
        else:
            is_on = None
        r = response[6]
        g = response[7]
        b = response[8]
        w = response[9]
        res = MagicHomeControllerState(is_on, MagicHomeControllerColorState(r, g, b, w))
        self.__logger.debug(res)
        return res

    @state.setter
    def state(self, s: MagicHomeControllerState) -> None:
        """
        Set the controller state

        :param s:
        :return:
        """
        if not s.is_on:
            self.turn_off()
            return
        self.color(*s.color.int)


class MagicHomeDeviceNotFound(Exception):
    pass


class MagicHome:
    """ A class  to """

    __logger = logging.getLogger(__name__)

    __broadcast_message: bytes = b"HF-A11ASSISTHREAD"
    __default_port: int = 48899
    __broadcast_wait_time: int = 1

    @classmethod
    def discover(cls) -> Set[MagicHomeController]:
        # from https://github.com/ninedraft/python-udp/blob/master/client.py
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception as e1:
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except Exception as e2:
                raise e2 from e1

        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(cls.__broadcast_wait_time)
        s.bind(("", cls.__default_port))

        s.sendto(cls.__broadcast_message, ("<broadcast>", cls.__default_port))
        cls.__logger.debug(f"Message '{cls.__broadcast_message}' broadcasted.")

        found = set()
        while True:
            try:
                data, addr = s.recvfrom(1024)
            except socket.timeout:
                break
            cls.__logger.debug(f"received message: {data} - {addr}")
            if data == cls.__broadcast_message:
                continue
            try:
                found.add(MagicHomeController(*data.split(b',')))
            except Exception as e:
                cls.__logger.warning(f'Invalid answer for broadcasted message {data}')
                cls.__logger.debug(e, exc_info=e)

        for controller in found:
            yield controller

    @classmethod
    def connect(cls, addr: str) -> MagicHomeController:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception as e1:
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except Exception as e2:
                raise e2 from e1

        # s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(cls.__broadcast_wait_time)
        s.bind(("", cls.__default_port))

        s.sendto(cls.__broadcast_message, (addr, cls.__default_port))
        cls.__logger.debug(f"Message '{cls.__broadcast_message}' sent to: {addr}.")

        try:
            data, addr = s.recvfrom(1024)
        except socket.timeout as e:
            raise MagicHomeDeviceNotFound(f"Address {addr} does not respond.") from e
        cls.__logger.debug(f"received message: {data} - {addr}")
        try:
            controller = MagicHomeController(*data.split(b','))
        except Exception as e:
            cls.__logger.warning(f'Invalid answer for message {data}')
            cls.__logger.debug(e, exc_info=e)
            raise MagicHomeDeviceNotFound(f"Address {addr} does not respond as expected.") from e

        return controller


if __name__ == '__main__':
    import cli
