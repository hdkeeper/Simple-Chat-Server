import asyncio
import re
import logging

SERVER_PORT = 10000
MAX_MESSAGE_LEN = 180
CLIENT_SLEEP_TIME = 1
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

control_seq = re.compile(r'\x1b\[([0-9]+~|[A-Z])|[\x00-\x1f\x7f]')
writers = []


def addrToStr(addr):
    return '%s:%d' % addr

async def clientHandler(reader, writer):
    clientAddr = writer.get_extra_info('peername')
    logging.info('Connection from %s', addrToStr(clientAddr))
    writers.append(writer)

    while not reader.at_eof():
        try:
            bdata = await reader.readline()
            msg = bdata.decode()
            msg = control_seq.sub('', msg).strip()[:MAX_MESSAGE_LEN]
            if len(msg) == 0:
                continue

            for w in writers:
                if w != writer:
                    w.write(f'{msg}\r\n'.encode())
        
        except Exception as ex:
            logging.error('Exception: %s', str(ex))
        
        await asyncio.sleep(CLIENT_SLEEP_TIME)

    logging.info('%s disconnected', addrToStr(clientAddr))
    writers.remove(writer)
    writer.close()


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt=LOG_DATE_FORMAT)

    server = await asyncio.start_server(clientHandler, '0.0.0.0', SERVER_PORT)
    serverAddr = server.sockets[0].getsockname()
    logging.info('Listening on %s', addrToStr(serverAddr))
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    if hasattr(asyncio, 'run'):
        asyncio.run(main())
    else:
        print('Python 3.7+ is required')
