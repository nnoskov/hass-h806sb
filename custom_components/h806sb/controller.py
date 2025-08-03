import asyncio
import socket
import logging
from ipaddress import ip_address

_LOGGER = logging.getLogger(__name__)

class LedController:
    """LED control device by using UDP for Home Assistant."""
    
    def __init__(self, host: str, port: int = 4626):
        self._host = host
        self._port = port
        self._command_counter = 0
        self._udp_socket = None
        self._serial_number = bytearray([0]*4)
        
        # base packet
        self._base_packet = bytearray([
            0xFB, 0xC1,              # Command bytes
            0x00,                    # Counter (will be increased)
            0x20,                    # Speed (by default 80)
            0x00,                    # Brightness (by default 0)
            0x01,                    # Single file playback
            0x00, 0xAE,              # Unknown bytes
            0x00, 0x00, 0x00, 0x00,  # Constants as serial number
            0x00, 0x00, 0x00, 0x00   # Serial number (will be filling after discovery)
        ])

    @staticmethod
    def compare_ips(ip1: str, ip2: str) -> bool:
        try:
            return ip_address(ip1) == ip_address(ip2)
        except ValueError:
            return ip1 == ip2

    async def async_initialize(self):
        """Initialization of socket (during start process)."""
        try:
            if hasattr(self, '_udp_socket') and self._udp_socket:
                try:
                    self._udp_socket.close()
                except:
                    pass
            loop = asyncio.get_event_loop()        
            self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            #settings of socket
            self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
            #self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._udp_socket.setblocking(False)
            try:
                self._udp_socket.bind(('0.0.0.0', 4882))
                _LOGGER.debug("Socket bound to port 4882")

            except OSError as e:
                # Если не получилось - используем случайный порт
                _LOGGER.warning(f"Could not bind to port 4882: {e}, using random port")
                try:
                    self._udp_socket.bind(('0.0.0.0', 0))
                    _LOGGER.debug(f"Socket bound to random port: {self._udp_socket.getsockname()[1]}")
                except OSError as e:
                    _LOGGER.error(f"Failed to bind socket: {e}")
                    self._udp_socket.close()
                    self._udp_socket = None
                    raise
        except Exception as e:
            _LOGGER.error(f"Socket initialization failed: {e}")
            raise

    async def async_send_packet(self, brightness: int, speed: int, is_on: bool):
        """Send control packet to device."""
        if not self._udp_socket:
            await self.async_initialize() 
        packet = bytearray(self._base_packet)
        packet[2] = (self._command_counter + 1) % 256
        packet[3] = max(1, min(100, speed))  # speed 1-100
        packet[4] = max(0, min(31, brightness))  # brightness 0-31
        packet[5] = 1 if is_on else 0
        packet[12:15] = self._serial_number
        
        try:
            await asyncio.get_event_loop().sock_sendto(
                self._udp_socket,
                packet,
                (self._host, self._port)
            )
            self._command_counter += 1
            _LOGGER.debug("Sent to %s:%s - %s", self._host, self._port, packet.hex())
            return True
        except Exception as err:
            _LOGGER.error("Error sending UDP packet: %s", err)
            return False

    async def async_check_availability(self, timeout: float = 2.0) -> bool:
        """Check availability of led controller"""
        try:
            # Reinitialize socket if needed
            if not hasattr(self, '_udp_socket') or self._udp_socket is None or getattr(self._udp_socket, '_closed', True):
                await self.async_initialize()  # Создаем новый сокет
            
            # Формат пакета из дампа
            check_packet = bytearray([
                0xAB, 0x01, 0x00, 0x02,  # Header
                0x00, 0x00, 0x00, 0x00,  # Reserved bytes
                0x00, 0x00, 0x00, 0x00   # Serial number
            ])

            _LOGGER.debug(f"Sending alive check: {check_packet.hex()} to {self._host}:4626")

            # Отправка на порт 4626
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(self._udp_socket, check_packet, (self._host, 4626))

            # Ожидание ответа
            try:
                data, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(self._udp_socket, 128),
                    timeout=timeout
                )
                _LOGGER.debug(f"Received from {addr[0]}:{addr[1]}: {data.hex()}")
                
                # Проверка только первых 2 байт
                if len(data) >= 2 and data[0] == 0xAB and data[1] == 0x02:
                    return True
                    
            except (asyncio.TimeoutError, socket.timeout):
                _LOGGER.debug("No response received within timeout")
            except OSError as e:
                _LOGGER.warning(f"Socket error: {e}")
                # Закрываем сокет при ошибке
                self._udp_socket.close()
                self._udp_socket = None

            return False

        except Exception as e:
            _LOGGER.error(f"Availability check failed: {e}", exc_info=True)
            return False

    async def async_close(self):
        """Cleaning of resources."""
        if self._udp_socket:
            self._udp_socket.close()

    def calculate_checksum(data):
        """Calculate UDP checksum manually"""
        if len(data) % 2 != 0:
            data += b'\x00'
        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i+1]
            checksum += word
        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum = ~checksum & 0xffff
        return checksum

    def set_serial_number(self, serial_number: str):
        """Setting the serial number with zero filling and reverse..
        
        Example:
            "0с3951" (3 bytes) -> filling to 4 bytes - "00 0с 39 51" -> revers to "51 39 0с 00"
        """
        try:
            # Converting hex-string to bytes
            serial_as_bytes = bytes.fromhex(serial_number)
            _LOGGER.debug(f"Original serial: {serial_as_bytes.hex(' ')}")
            
            # Filling by zero on left 
            if len(serial_as_bytes) < 4:
                padding = bytes(4 - len(serial_as_bytes))
                serial_as_bytes = padding + serial_as_bytes
                _LOGGER.debug(f"Padded serial: {serial_as_bytes.hex(' ')}")

            # Revesr of bytes (little-endian)
            reversed_serial = bytearray(reversed(serial_as_bytes))
            _LOGGER.debug(f"Final serial: {bytes(reversed_serial).hex(' ')}")
            self._serial_number[:] = reversed_serial
            
            _LOGGER.info(f"Serial number set: {self._serial_number.hex()}")
            
        except ValueError as ve:
            _LOGGER.error(f"Invalid serial number format: {ve}")
            raise
        except Exception as e:
            _LOGGER.error(f"Error setting serial: {e}")
            raise