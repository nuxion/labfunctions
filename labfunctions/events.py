import json
from typing import List, Union

from redis.asyncio import Redis

from labfunctions.types.events import EventSSE
from labfunctions.utils import secure_filename

BLOCK_MS = 15 * 1000
DEFAULT_TTL = 60 * 60


class EventManager:
    def __init__(self, redis: Redis, block_ms=BLOCK_MS, ttl_secs=DEFAULT_TTL):
        """
        It manages the interaction with Redis Streams data structure
        Also it format data into SSE format.

        :param redis: A redis instance
        :param block_ms: wait x time in milliseconds for a new message
        in the stream channel
        :param ttl_secs: because each stream should be temporal for each execution,
        it should be deleted after `ttl_secs`
        """
        self.redis = redis
        self._block_ms = block_ms
        self._ttl = ttl_secs

    async def read(self, channel, msg_id, block_ms=None) -> Union[List[EventSSE], None]:

        block_ms = block_ms or self._block_ms
        stream = {channel: msg_id}
        rsp = await self.redis.xread(stream, block=block_ms)
        if rsp:
            events = []
            for msg in rsp[0][1]:
                _id = msg[0]
                _data = msg[1]
                # _jdata = json.dumps(_data)
                _evt = EventSSE(id=_id, data=_data["msg"], event=_data["event"])

                events.append(_evt)

            return events
        return None

    async def publish(self, channel, evt: EventSSE, ttl_secs=None):
        ttl_secs = ttl_secs or self._ttl

        async with self.redis.pipeline() as pipe:
            event_type = evt.event or ""
            res = (
                await pipe.xadd(channel, fields={"msg": evt.data, "event": event_type})
                .expire(channel, ttl_secs)
                .execute()
            )
        return res

    @staticmethod
    def generate_channel(projectid, execid):
        pid = secure_filename(projectid)
        eid = secure_filename(execid)
        return f"{pid}.{eid}"

    @staticmethod
    def format_sse(evt: EventSSE) -> str:
        """
        It transforms an EventSSE object into a compliant EventSource string
        https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format
        https://maxhalford.github.io/blog/flask-sse-no-deps/
        """

        msg = f"data: {evt.data}\n\n"
        if evt.event is not None:
            msg = f"event: {evt.event}\n{msg}"
        if evt.id is not None:
            msg = f"id: {evt.id}\n{msg}"
        return msg

    @staticmethod
    def from_sse2event(msg: str) -> EventSSE:
        event = None
        id = None
        data = None
        for line in msg.split("\n"):
            if line.startswith("data:"):
                data = line.split(":", maxsplit=1)[1].strip()
            elif line.startswith("event:"):
                event = line.split(":", maxsplit=1)[1].strip()
            elif line.startswith("id:"):
                id = line.split(":", maxsplit=1)[1].strip()
        return EventSSE(id=id, event=event, data=data)
