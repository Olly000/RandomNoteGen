#!/usr/env/bin python3

import mido
import pygame.midi as pym
import random
from time import sleep
from timeit import default_timer as dtime

mido.set_backend('mido.backends.pygame')

pym.init()


class Inputs:
    def __init__(self):
        self.key_values = {'c': 0, 'c#': 1, 'd': 2, 'd#': 3, 'e': 4,
                           'f': 5, 'f#': 6, 'g': 7, 'g#': 8, 'a': 9, 'a#': 10, 'b': 11}
        self.key_maps = {
            'maj': [0, 2, 4, 5, 7, 9, 11],
            'min': [0, 2, 3, 5, 7, 9, 10],
            'penta': [0, 3, 5, 7, 10],
            'whole': [0, 2, 4, 6, 8, 10],
            'chrom': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        }

        self.channel = self.get_channel()
        self.scale = self.scale_gen()
        self.note_value = self.get_note_value()
        self.interval = self.get_timebase()
        self.bars = self.get_no_of_bars()
        self.gate_mod = self.get_gate_mod()
        self.quantise_gate = self.get_quantise()
        self.time_mod = self.get_time_mod()
        self.every_step = self.play_every_step()

    @staticmethod
    def get_port():  # requests user port
        port_list = mido.get_output_names()
        print('Available MIDI ports are \n')
        for name in range(0, len(port_list)):
            print('%s' % name, port_list[name])
        return port_list[int(input('\n Choose port by number: '))]

    @staticmethod
    def get_note_value():
        return int(input('Select note value: '))

    @staticmethod
    def get_no_of_bars():
        return int(input('Select number of bars to run for: '))

    @staticmethod
    def get_bpm():  # requests user bpm, returns length in secs of 16th note
        return (60.0 / float(input('Select bpm: '))) / 4.0

    @staticmethod
    def get_gate_mod():  # returns user defined note length mod  percentage as decimal
        return float(input('What percentage should gate length be modded by?: '))

    @staticmethod
    def get_quantise():
        response = input('Quantise gate modulation? (y/n): ').lower()
        if response == 'y':
            return True

    @staticmethod
    def get_time_mod():  # returns user defined timing mod percentage as decimal
        return float(input('What percentage should note timing by modded by?: ')) / 100.0

    @staticmethod
    def get_channel():  # requests user channel
        return int(input('Select MIDI Output Channel: ')) - 1

    @staticmethod
    def get_root_note():  # requests user key
        return input('Select root note to use: ')

    @staticmethod
    def get_scale():  # requests user scale
        return input('Select output scale type (maj/min/penta/whole/chrom: ')

    @staticmethod
    def play_every_step():  # if yes returned program will repeat previous note when non-scale note is generated
        response = input('Play note on every step (y/n): ').lower()
        if response == 'y':
            return True

    @staticmethod
    def note_list_gen(note_key, note_range):  # returns list of note numbers to be output
        note_list = []
        for n in note_key:
            note_list.append(note_range[0] + n)
        while note_list[-1] < note_range[1]:
            note_key = [n + 12 for n in note_key]
            for n in note_key:
                if note_list[-1] < note_range[1]:
                    note_list.append(note_range[0] + n)
        return note_list

    @staticmethod
    def set_note_range():  # requests octave range and returns corresponding MIDI note number range
        octs = int(input('Select Octave Range (<= 10): '))
        note_range = [60, 72]
        if octs == 1:
            return note_range
        else:
            note_range[0] -= (12 * int(octs / 2))
            note_range[1] = 60 + (12 * int(octs / 2))
            note_range[1] += (12 * (octs % 2))
        return note_range

    def scale_gen(self):  # method to organise note list generation, returns note list
        scale_offset = self.key_values[self.get_root_note().lower()]
        note_range = [n+scale_offset for n in (self.set_note_range())]
        note_key = self.key_maps[self.get_scale()]
        return self.note_list_gen(note_key, note_range)

    def get_timebase(self):  # returns standard time interval between notes using user bpm and note value
        return (16/float(self.note_value)) * self.get_bpm()


class RandomNote:
    def __init__(self):
        self.params = Inputs()  # stores all the user input variables needed to define the sequence
        self.out_port = mido.open_output(self.params.get_port())

    def note_gen(self):  # generate a random number within the note range defined by Inputs.scale variable
        return random.randint(self.params.scale[0], (self.params.scale[-1]+1))

    def scale_check(self, note):
        if note in self.params.scale:
            return note
        else:
            return False

    def gate_length(self):  # applies gate length modulation to note, returns corrected gate length
        mod_amount = (random.random() * self.params.gate_mod)/100
        if random.getrandbits(1):
            return (self.params.interval/2.0) + ((self.params.interval/2)*mod_amount)
        else:
            return (self.params.interval/2.0) - ((self.params.interval/2)*mod_amount)

    def gate_length_quant(self):  # as gate_length but quantised to 16ths
        mod_options = [-0.75, -0.5, -0.25, -0.125, 0.125, 0.25, 0.5, 0.75]
        for mod in mod_options:
            if abs(mod * 100) > self.params.gate_mod:
                mod_options.remove(mod)
        for n in range(0, int(len(mod_options) / 2)):
            mod_options.append(0)
        return (self.params.interval/2) + (random.choice(mod_options) * (self.params.interval/2))

    def micro_time(self):  # applies random timing variation to interval time and returns corrected interval length
        if random.getrandbits(1):
            return self.params.interval + (self.params.interval * self.params.time_mod)
        else:
            return self.params.interval - (self.params.interval * self.params.time_mod)

    def play_note(self, note):
        msg = mido.Message('note_on', channel=self.params.channel, note=note)
        self.out_port.send(msg)
        sleep(self.gate_length())
        msg = mido.Message('note_off', channel=self.params.channel, note=note)
        self.out_port.send(msg)

    def note_processor(self):  # co-ordinates output of note messages
        loops = self.params.note_value * self.params.bars
        last_note = self.params.scale[0]
        while loops > 0:
            loops -= 1
            start = dtime()
            note = self.scale_check(self.note_gen())
            rest = self.micro_time()
            if note:
                self.play_note(note)
                last_note = note
            elif self.params.every_step:
                self.play_note(last_note)
            end = dtime()
            sleep(rest - (end - start))
        print('End of Pattern')
        self.out_port.close()


if __name__ == '__main__':

    generate = RandomNote()
    generate.note_processor()
