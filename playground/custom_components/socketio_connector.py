import logging
import os
import uuid
from urllib.request import urlretrieve
import sys
import numpy as np
from sanic import Blueprint, response
from sanic.request import Request
from socketio import AsyncServer
from typing import Optional, Text, Any, Dict, Iterable

from rasa.core.channels.channel import InputChannel, UserMessage, OutputChannel

from custom_components.tts_modules.vietTTS.synthesizer import Synthesizer
from custom_components.modules.voice_modules import VoiceModules

logger = logging.getLogger(__name__)


class SocketBluePrint(Blueprint):
    def __init__(self, sio: AsyncServer, socketio_path, *args, **kwargs):
        self.sio = sio
        self.socketio_path = socketio_path
        super(SocketBluePrint, self).__init__(*args, **kwargs)

    def register(self, app, options):
        self.sio.attach(app, self.socketio_path)
        super(SocketBluePrint, self).register(app, options)


class SocketIoOutput(OutputChannel):
    @classmethod
    def name(cls):
        return "socketio"

    def __init__(self, sio, sid, bot_message_evt, message):
        self.sio = sio
        self.sid = sid
        self.bot_message_evt = bot_message_evt
        self.message = message

        self.tts = Synthesizer()

    async def _send_message(self, socket_id, response_message, **kwargs: Any):

        uid = uuid.uuid4()

        print("Start synthesizing")
        print(f"Message: {response_message['text']}")
        self.tts.synthesize_uuid(response_message['text'], uid, socket_id)
        print("Synthesized")

        await self.sio.emit(self.bot_message_evt,
                            {"text": response_message['text'],
                             "link": f"http://192.168.191.178:8888/output-{socket_id}-{uid}.wav"},
                            room=socket_id)
        print("emitted")

    async def send_text_message(
            self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        await self._send_message(self.sid, {"text": text})


class SocketIoInput(InputChannel):
    @classmethod
    def name(cls):
        return "socketio"

    @classmethod
    def from_credentials(cls, credentials):
        credentials = credentials or {}
        return cls(credentials.get("user_message_evt", "user_uttered"),
                   credentials.get("bot_message_evt", "bot_uttered"),
                   credentials.get("namespace"),
                   credentials.get("session_persistence", False),
                   credentials.get("socketio_path", "/socket.io"),
                   )

    def __init__(self,
                 user_message_evt: Text = "user_uttered",
                 bot_message_evt: Text = "bot_uttered",
                 namespace: Optional[Text] = None,
                 session_persistence: bool = False,
                 socketio_path: Optional[Text] = '/socket.io'):
        self.user_message_evt = user_message_evt
        self.bot_message_evt = bot_message_evt
        self.namespace = namespace
        self.session_persistence = session_persistence
        self.socketio_path = socketio_path

        self.stt = VoiceModules()

    def blueprint(self, on_new_message):
        sio = AsyncServer(async_mode="sanic", cors_allowed_origins='*')
        socketio_webhook = SocketBluePrint(sio,
                                           self.socketio_path,
                                           "socketio_webhook",
                                           __name__)

        @socketio_webhook.route("/", methods=['GET'])
        async def health(request):
            return response.json({"status": "ok"})

        @sio.on('connect', namespace=self.namespace)
        async def connect(sid, environ):
            logger.debug("User {} connected to socketIO endpoint.".format(sid))
            print('Connected!')

        @sio.on('disconnect', namespace=self.namespace)
        async def disconnect(sid):
            logger.debug("User {} disconnected from socketIO endpoint."
                         "".format(sid))

        @sio.on('session_request', namespace=self.namespace)
        async def session_request(sid, data):
            print('This is session request')
            # print(data)
            # print(data['session_id'])
            if data is None:
                data = {}
            if 'session_id' not in data or data['session_id'] is None:
                data['session_id'] = uuid.uuid4().hex
            await sio.emit("session_confirm", data['session_id'], room=sid)
            logger.debug("User {} connected to socketIO endpoint."
                         "".format(sid))

        # @sio.on('recorder stopped', namespace=self.namespace)
        # async def get_audio(sid, data):
        #    print('This is what I got')
        #    print(data)

        @sio.on('user_uttered', namespace=self.namespace)
        async def handle_message(sid, data):

            output_channel = SocketIoOutput(sio, sid, self.bot_message_evt, data['message'])
            if data['message'] == "/get_started":
                message = data['message']
            else:
                # receive audio as .ogg
                received_file = "custom_components/wavs/input_raw.wav"

                urlretrieve(data['message'], received_file)
                path = os.path.dirname(__file__)
                # print(path)
                # print(sid)
                # convert .ogg file into int16 wave file by ffmpeg
                # -ar 44100
                os.system("ffmpeg -y -i {0} -ar 16000 custom_components/wavs/input.wav".format(received_file))
                # os.system("ffmpeg -y -i {0} -c:a pcm_s161e output_{1}.wav".format(received_file,sid))

                message = self.stt.speech_to_text().lower()
                print(f"Message in: {message}")

                # await self.sio.emit(self.bot_message_evt, response, room=socket_id)
                await sio.emit("user_uttered", {"text": message}, room=sid)
                # ffmpeg -i input.flv -f s16le -acodec pcm_s16le output.raw

            if self.session_persistence:
                # if not data.get("session_id"):
                #    logger.warning("A message without a valid sender_id "
                #                   "was received. This message will be "
                #                   "ignored. Make sure to set a proper "
                #                   "session id using the "
                #                   "`session_request` socketIO event.")
                #    return
                # sender_id = data['session_id']
                # else:
                sender_id = sid

            message_rasa = UserMessage(message, output_channel, sender_id,
                                       input_channel=self.name())
            await on_new_message(message_rasa)

        return socketio_webhook
