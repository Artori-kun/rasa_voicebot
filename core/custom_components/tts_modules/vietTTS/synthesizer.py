import json
import pickle
import re
import unicodedata
from argparse import ArgumentParser
from pathlib import Path
import os

import requests
import sounddevice as sd
import wave as wv

import soundfile as sf

from .hifigan.mel2wave import mel2wave
from .nat.config import FLAGS
from .nat.text2mel import text2mel, load_lexicon
from .nat.data_loader import load_phonemes_set_from_lexicon_file

from scipy.io.wavfile import write
import numpy as np


# import tensorflow as tf
# gpus = tf.config.experimental.list_physical_devices('GPU')
# tf.config.experimental.set_memory_growth(gpus[0], True)
# import tensorflow.keras.backend as K

# parser = ArgumentParser()
# parser.add_argument('--text', type=str)
# parser.add_argument('--output', default='clip.wav', type=Path)
# parser.add_argument('--sample-rate', default=16000, type=int)
# parser.add_argument('--silence-duration', default=-1, type=float)
# parser.add_argument('--lexicon-file', default=None)
# args = parser.parse_args()
# os.environ['CUDA_VISIBLE_DEVICES'] = "0"


class Synthesizer:
    def __init__(self):
        # os.environ['CUDA_VISIBLE_DEVICES'] = "0"
        # gpu_options = tf.compat.v1.GPUOptions(allow_growth=True)
        # sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(gpu_options=gpu_options))
        # tf.compat.v1.keras.backend.set_session(sess)

        # tf.config.experimental.set_visible_devices([], "GPU")
        self.sample_rate = 16000
        self.silence_duration = 1
        self.lexicon_file = 'custom_components/tts_modules/assets/infore/lexicon.txt'

        self.phonemes = load_phonemes_set_from_lexicon_file(Path(self.lexicon_file))
        self.lexicon = load_lexicon(Path(self.lexicon_file))

        with open('custom_components/tts_modules/assets/infore/nat/duration_ckpt_latest.pickle', 'rb') as fr:
            self.duration_dic = pickle.load(fr)

        with open('custom_components/tts_modules/assets/infore/nat/acoustic_ckpt_latest.pickle', 'rb') as fr:
            self.acoustic_dic = pickle.load(fr)

        with open('custom_components/tts_modules/assets/infore/hifigan/hk_hifi.pickle', 'rb') as fr:
            self.hk_hifi_params = pickle.load(fr)

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
                if num_text[0] == '1':
                    num_text = synonyms[num_text[0]]['ty2'] + " " + synonyms[num_text[1]]['teen']
                elif num_text[0] == '0':
                    num_text = synonyms[num_text[1]]['single']
                else:
                    num_text = synonyms[num_text[0]]['ty2'] + " " + synonyms[num_text[1]]['ty1']
            elif len(num_text) == 3:
                if num_text[1] == '0':
                    num_text = synonyms[num_text[0]]['single'] + " trăm " + \
                               synonyms[num_text[1]]['ty2'] + " " + synonyms[num_text[2]]['single']
                elif num_text[1] == '1':
                    num_text = synonyms[num_text[0]]['single'] + " trăm " + \
                               synonyms[num_text[1]]['ty2'] + " " + synonyms[num_text[2]]['teen']
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
        text = text.replace('\n', '.')

        text = re.sub(re.compile(r'[•\-+():]'), '', text)

        return text

    def synthesize(self, input_text):
        input_text = self.prepare_text(input_text)
        input_text = self.nat_normalize_text(input_text)
        mel = text2mel(text=input_text,
                       phonemes=self.phonemes,
                       lexicon=self.lexicon,
                       duration_dic=self.duration_dic,
                       acoustic_dic=self.acoustic_dic,
                       silence_duration=self.silence_duration)

        wave = mel2wave(mel=mel,
                        model_params=self.hk_hifi_params)

        # print(wave)

        write("custom_components/wavs/output.wav", 16000, wave.astype(np.float32))

    def synthesize_uuid(self, input_text, uid, socketid):
        input_text = self.prepare_text(input_text)
        input_text = self.nat_normalize_text(input_text)

        print(input_text)

        mel = text2mel(text=input_text,
                       phonemes=self.phonemes,
                       lexicon=self.lexicon,
                       duration_dic=self.duration_dic,
                       acoustic_dic=self.acoustic_dic,
                       silence_duration=self.silence_duration)

        wave = mel2wave(mel=mel,
                        model_params=self.hk_hifi_params)

        # print(wave)

        write(f"custom_components/wavs/output-{socketid}-{uid}.wav", 16000, wave.astype(np.float32))

    def synthesize_api(self, input_text, uid, socketid):
        input_text = self.prepare_text(input_text)

        file = requests.post("tts-api", json={"text": input_text})

        with open(f"custom_components/wavs/output-{socketid}-{uid}.wav", 'wb') as fw:
            fw.write(file.content)
        fw.close()

    # def synthesize_fpt(self, input_text, uid, socketid):
    #     input_text = self.prepare_text(input_text)
    #     input_text = self.nat_normalize_text(input_text)

# text = nat_normalize_text(args.text)
# print('Normalized text input:', text)
# mel = text2mel(text, args.lexicon_file, args.silence_duration)
# wave = mel2wave(mel)
# print('writing output to file', args.output)
# sf.write(str(args.output), wave, samplerate=args.sample_rate)
