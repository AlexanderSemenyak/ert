import asyncio
from asyncio.queues import Queue
import websockets
from ert_shared.ensemble_evaluator.ws_util import wait_for_ws
import queue
import logging
import threading
from cloudevents.http import from_json
from cloudevents.http.event import CloudEvent
from cloudevents.http import to_json
import ert_shared.ensemble_evaluator.entity.identifiers as identifiers

logger = logging.getLogger(__name__)


class _Monitor:
    def __init__(self, host, port):
        self._base_uri = f"ws://{host}:{port}"
        self._client_uri = f"{self._base_uri}/client"

        self._loop = asyncio.new_event_loop()
        self._incoming = asyncio.Queue(loop=self._loop)
        self._receive_future = None
        self._event_index = 1

    def event_index(self):
        index = self._event_index
        self._event_index += 1
        return index

    def exit_server(self):
        logger.debug("asking server to exit...")

        async def _send_terminated_req():
            async with websockets.connect(self._client_uri) as websocket:
                out_cloudevent = CloudEvent(
                    {
                        "type": identifiers.EVTYPE_EE_TERMINATE_REQUEST,
                        "source": "/ert/monitor/0",
                        "id": self.event_index(),
                    }
                )
                message = to_json(out_cloudevent)
                await websocket.send(message)

        asyncio.run_coroutine_threadsafe(_send_terminated_req(), self._loop).result()
        logger.debug("asked server to exit")

    async def _receive(self):
        logger.debug("starting monitor receive")
        async with websockets.connect(
            self._client_uri, max_size=2 ** 26, max_queue=500
        ) as websocket:
            async for message in websocket:
                logger.debug(f"monitor receive: {message}")
                event = from_json(message)
                self._incoming.put_nowait(event)
                if event["type"] == identifiers.EVTYPE_EE_TERMINATED:
                    logger.debug("client received terminated")
                    break

        logger.debug("monitor disconnected")

    def _run(self, done_future):
        asyncio.set_event_loop(self._loop)
        self._receive_future = self._loop.create_task(self._receive())
        try:
            self._loop.run_until_complete(self._receive_future)
        except asyncio.CancelledError:
            logger.debug("receive cancelled")
        self._loop.run_until_complete(done_future)

    def track(self):
        wait_for_ws(self._base_uri)

        done_future = asyncio.Future(loop=self._loop)

        thread = threading.Thread(
            name="ert_monitor_loop", target=self._run, args=(done_future,)
        )
        thread.start()

        event = None
        try:
            while event is None or event["type"] != identifiers.EVTYPE_EE_TERMINATED:
                logger.debug("wait for incoming")
                event = asyncio.run_coroutine_threadsafe(
                    self._incoming.get(), self._loop
                ).result()
                logger.debug(f"got incoming: {event}")
                yield event
            self._loop.call_soon_threadsafe(done_future.set_result, None)
        except GeneratorExit:
            logger.debug("generator exit")
            self._loop.call_soon_threadsafe(self._receive_future.cancel)
            if not done_future.done():
                self._loop.call_soon_threadsafe(done_future.set_result, None)
        thread.join()


def create(host, port):
    return _Monitor(host, port)