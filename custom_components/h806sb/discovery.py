import asyncio
import socket
from typing import Optional, Tuple
import logging
import time

_LOGGER = logging.getLogger(__name__)

class H806SBDiscovery:
    DEVICE_PORT = 4626
    LISTEN_PORT = 4882 
    DISCOVERY_PACKET = bytes([0xAB, 0x01])
    RESPONSE_HEADER = bytes([0xAB, 0x02])

    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.bind(("0.0.0.0", self.LISTEN_PORT))
        self._sock.setblocking(False) 
        self._local_port = self._sock.getsockname()[1]
        _LOGGER.debug(f"Discovery socket created on port: {self._local_port}")

    async def discover_device(self, timeout: int = 2) -> Optional[Tuple[str, bytes, str]]:
        """Finding a compatible device on the network."""
        try:
            loop = asyncio.get_running_loop()
            
            # Отправка широковещательного запроса
            await loop.sock_sendto(
                self._sock, 
                self.DISCOVERY_PACKET, 
                ("255.255.255.255", self.DEVICE_PORT)
            )
            _LOGGER.debug(f"Discovery packet sent from port {self._local_port}")

            # Ожидание ответа с таймаутом
            start_time = time.monotonic()
            while (time.monotonic() - start_time) < timeout:
                try:
                    # Асинхронное получение данных
                    data, addr = await loop.sock_recvfrom(self._sock, 128)
                    _LOGGER.debug(f"Received response from {addr}: {data.hex()}")
                    
                    if data.startswith(self.RESPONSE_HEADER):
                        # Извлечение имени устройства
                        name_data = data[2:]
                        name = name_data.split(b'\x00')[0].decode("ascii", errors="ignore")
                        
                        # Парсинг серийного номера
                        if "_" in name:
                            _, hex_part = name.split("_", 1)
                            try:
                                serial_number = bytes.fromhex(hex_part)
                                return (addr[0], serial_number, name)
                            except ValueError:
                                _LOGGER.warning(f"Invalid serial format: {hex_part}")
                except BlockingIOError:
                    await asyncio.sleep(0.1)
                except OSError as e:
                    _LOGGER.error(f"Socket error: {e}")
                    break
                    
        except Exception as e:
            _LOGGER.error(f"Discovery failed: {e}", exc_info=True)
        return None

    def close(self):
        if self._sock:
            _LOGGER.debug("Closing socket for discovery")
            self._sock.close()
            self._sock = None