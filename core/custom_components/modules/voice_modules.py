import urllib

import requests
import json
import urllib.request
import pyaudio
import wave


class VoiceModules:
    def __init__(self):
        with open(r"custom_components/modules/config.json", 'r') as fr:
            self.config = json.load(fr)

        self.api_key = self.config['api_key']

        self.speech_to_text_url = self.config['stt_url']
        self.input_wav_path = self.config['stt_input_path']

        self.text_to_speech_url = self.config['tts_url']
        self.output_path = self.config['tts_output_path']

    def speech_to_text(self, input_wav_path):
        payload = open(input_wav_path, 'rb').read()
        headers = {
            'api-key': self.api_key
        }

        response = requests.post(url=self.speech_to_text_url, data=payload, headers=headers)

        response = response.json()

        status = response["status"]

        if status == 0:
            return response["hypotheses"][0]["utterance"]
        else:
            print("stt failed")
            return None

    def text_to_speech(self, text):
        payload = text.encode('utf-8')
        headers = {
            'api-key': self.api_key,
            'speed': '',
            'voice': 'banmai',
            'format': 'wav'
        }

        response = requests.post(url=self.text_to_speech_url,
                                 data=payload, headers=headers)

        response = response.json()

        if response['error'] == 0:
            audio = urllib.request.urlopen(response['async'])

            with open(self.output_path, 'wb') as fw:
                fw.write(audio.read())
            fw.close()

            # wr = wave.open(self.output_path, 'rb')
            #
            # pa = pyaudio.PyAudio()
            #
            # stream = pa.open(format=pa.get_format_from_width(wr.getsampwidth()),
            #                  channels=wr.getnchannels(),
            #                  rate=wr.getframerate(),
            #                  output=True)
            #
            # data = wr.readframes(1024)
            #
            # while True:
            #     if data != '':
            #         stream.write(data)
            #         data = wr.readframes(1024)
            #     if data == b'':
            #         break
            #
            # stream.stop_stream()
            # stream.close()
            # pa.terminate()
            # print("stream closed")
        else:
            print("tts failed")
            print(response)
            return None
