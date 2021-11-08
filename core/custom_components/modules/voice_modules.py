import urllib

import requests
import json
import urllib.request
import re
import unicodedata
import pyaudio
import wave

from custom_components.tts_modules.vietTTS.nat.config import FLAGS


class VoiceModules:
    def __init__(self):
        with open(r"custom_components/modules/config.json", 'r') as fr:
            self.config = json.load(fr)

        self.api_key = self.config['api_key']

        self.speech_to_text_url = self.config['stt_url']
        self.input_wav_path = self.config['stt_input_path']

        self.text_to_speech_url = self.config['tts_url']
        self.output_path = self.config['tts_output_path']

        self.stt_mini_url = "http://192.168.14.2:5555/recog"

    @staticmethod
    def nat_normalize_text(input_text):
        input_text = unicodedata.normalize('NFKC', input_text)
        input_text = input_text.lower().strip()
        sp = FLAGS.special_phonemes[FLAGS.sp_index]
        input_text = re.sub(r'[\n.,:]+', f' {sp} ', input_text)
        input_text = input_text.replace('"', " ")
        input_text = re.sub(r'\s+', ' ', input_text)
        input_text = re.sub(r'[.,:;?!]+', f' {sp} ', input_text)
        input_text = re.sub('[ ]+', ' ', input_text)
        input_text = re.sub(f'( {sp}+)+ ', f' {sp} ', input_text)
        return input_text.strip()

    @staticmethod
    def prepare_text(text):
        text = text.lower()
        # text = unicodedata.normalize("NFKD", text)

        with open("custom_components/tts_modules/vietTTS/synonyms.json", "r", encoding="utf-8") as fr:
            synonyms = json.load(fr)

        with open("custom_components/tts_modules/vietTTS/acronyms.json", "r", encoding="utf-8") as fr:
            acronyms = json.load(fr)

        def convert_number_lte_3digits(num_text):
            if len(num_text) == 1:
                num_text = synonyms[num_text]['single']
            elif len(num_text) == 2:
                # if num_text[0] == '1':
                #     num_text = "mười"
                if num_text[0] == '0':
                    num_text = synonyms[num_text[1]]['single']
                else:
                    num_text = synonyms[num_text[0]]['ty2'] + " " + synonyms[num_text[1]]['ty1']
            elif len(num_text) == 3:
                if num_text[1] == '0':
                    num_text = synonyms[num_text[0]]['single'] + " trăm " + \
                               synonyms[num_text[1]]['ty2'] + " " + synonyms[num_text[2]]['single']
                else:
                    num_text = synonyms[num_text[0]]['single'] + " trăm " + \
                               synonyms[num_text[1]]['ty2'] + " " + synonyms[num_text[2]]['ty1']
            return num_text

        def convert_number_to_text(num_text):
            final_text = ''
            iteration = int(len(num_text) / 3)

            for i in range(1, iteration + 1):
                triple_digit = num_text[-3:]
                num_text = num_text[:-3]
                if len(num_text) == 0:
                    final_text = convert_number_lte_3digits(triple_digit) + " " + final_text
                else:
                    final_text = synonyms['unit'][i] + " " + convert_number_lte_3digits(triple_digit) + " " + final_text

            final_text = convert_number_lte_3digits(num_text) + " " + final_text

            return final_text.strip()

        pattern_date = re.compile(r'\b((3[0-1]|[1-2][0-9]|0[1-9])[/-](1[0-2]|0[1-9]|[1-9])[/-](\d{4}|\d{2}))|((3[0-1]|['
                                  r'0-2][0-9]|[1-9])[/-](1[0-2]|0[1-9]|[1-9]))\b')
        pattern_time = re.compile(r'((2[0-4]|[0-1][0-9]|[0-9]):([0-5][0-9]|[1-9])(:([0-5][0-9]|[1-9]))?)')
        pattern_digits = re.compile(r"\d+")

        # replace acronyms with full text
        for k in acronyms.keys():
            text = re.sub(r'\b' + k + r'\b', acronyms[k], text)

        # convert time format to text

        for match in re.finditer(pattern_time, text):
            time_text = match.group(0)
            time_text = time_text.split(':')

            if time_text[1] == '00':
                time_text = time_text[0] + ' giờ '
            else:
                time_text = time_text[0] + ' giờ ' + time_text[1]

            text = text.replace(match.group(0), time_text)

        # convert date format to text

        for match in re.finditer(pattern_date, text):
            # print(match.group(0))
            date_text = match.group(0)

            if len(date_text.split('/')) == 1:
                date_text = date_text.split('-')
            else:
                date_text = date_text.split('/')

            if date_text[0].startswith('0'):
                date_text[0] = date_text[0][1:]
            if date_text[1].startswith('0'):
                date_text[1] = date_text[1][1:]

            if len(date_text) == 2:
                date_text = date_text[0] + ' tháng ' + date_text[1]
            else:
                date_text = date_text[0] + ' tháng ' + date_text[1] + ' năm ' + date_text[2]

            # print(date_text)
            text = text.replace(match.group(0), date_text)

        # convert numbers to text
        for match in re.finditer(re.compile(r'\d+.\d+'), text):
            text = text.replace(match.group(0), match.group(0).replace('.', ''))

        for match in re.finditer(pattern_digits, text):
            print(match.group(0))
            text = text.replace(match.group(0), convert_number_to_text(match.group(0)))

        text = text.replace('/', ' trên ')

        text = re.sub(re.compile(r'[•\-+():]'), '', text)

        return text

    def speech_to_text_mini(self, input_wav_path):
        wav = open(input_wav_path, "rb")

        files = {"the_file": wav}

        response = requests.post(self.stt_mini_url, files=files)

        return response.text

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

    def text_to_speech(self, input_text, uid, socketid):
        input_text = self.prepare_text(input_text)
        # input_text = self.nat_normalize_text(input_text)

        print(input_text)

        payload = input_text.encode('utf-8')
        # print(payload)
        headers = {
            'api-key': self.api_key,
            'speed': '-0.5',
            'voice': 'banmaiace',
            'format': 'wav'
        }

        response = requests.post(url=self.text_to_speech_url,
                                 data=payload, headers=headers)

        response = response.json()
        print(response)

        if response['error'] == 0:
            # file = requests.get(response['async'])
            # req = urllib.request.Request(response['async'], headers={'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) "
            #                                                                        "AppleWebKit/537.36 (KHTML, "
            #                                                                        "like Gecko) Chrome/92.0.4515.159 "
            #                                                                        "Safari/537.36 "})
            # audio = urllib.request.urlretrieve(response['async'], f"custom_components/wavs/output-{socketid}-{uid}.wav")

            # with open(f"custom_components/wavs/output-{socketid}-{uid}.wav", 'wb') as fw:
            #     # fw.write(audio.read())
            #     fw.write(file.content)
            # fw.close()

            return response['async']

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
            return 0
