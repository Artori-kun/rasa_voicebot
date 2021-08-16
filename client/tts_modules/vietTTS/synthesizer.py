import pickle
import re
import unicodedata
from argparse import ArgumentParser
from pathlib import Path
import os
import sounddevice as sd

import soundfile as sf

from .hifigan.mel2wave import mel2wave
from .nat.config import FLAGS
from .nat.text2mel import text2mel, load_lexicon
from .nat.data_loader import load_phonemes_set_from_lexicon_file

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
        os.environ['CUDA_VISIBLE_DEVICES'] = "0"
        self.sample_rate = 16000
        self.silence_duration = 1
        self.lexicon_file = 'tts_modules/assets/infore/lexicon.txt'

        self.phonemes = load_phonemes_set_from_lexicon_file(Path(self.lexicon_file))
        self.lexicon = load_lexicon(Path(self.lexicon_file))

        with open('tts_modules/assets/infore/nat/duration_ckpt_latest.pickle', 'rb') as fr:
            self.duration_dic = pickle.load(fr)

        with open('tts_modules/assets/infore/nat/acoustic_ckpt_latest.pickle', 'rb') as fr:
            self.acoustic_dic = pickle.load(fr)

        with open('tts_modules/assets/infore/hifigan/hk_hifi.pickle', 'rb') as fr:
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

    def synthesize(self, input_text):
        input_text = self.nat_normalize_text(input_text)
        mel = text2mel(text=input_text,
                       phonemes=self.phonemes,
                       lexicon=self.lexicon,
                       duration_dic=self.duration_dic,
                       acoustic_dic=self.acoustic_dic,
                       silence_duration=self.silence_duration)

        wave = mel2wave(mel=mel,
                        model_params=self.hk_hifi_params)

        sd.play(wave, samplerate=16000)

# text = nat_normalize_text(args.text)
# print('Normalized text input:', text)
# mel = text2mel(text, args.lexicon_file, args.silence_duration)
# wave = mel2wave(mel)
# print('writing output to file', args.output)
# sf.write(str(args.output), wave, samplerate=args.sample_rate)
