#!/usr/bin/env PYTHON3

import mido
import pygame.midi as pym
import tkinter as tk
from tkinter import messagebox
import random
from time import sleep
from timeit import default_timer as dtime

mido.set_backend('mido.backends.pygame')

pym.init()


class Interface(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.num_fields = ['Port No.', 'Channel', 'BPM', 'No. of Bars',
                           'Note Length', 'Octave Range', 'Gate Mod', 'Time Mod']
        self.defaults = [0, 1, 120, 16, 8, 2, 0, 0, 'c', 'maj']
        self.key_maps = {
            'maj': [0, 2, 4, 5, 7, 9, 11],
            'min': [0, 2, 3, 5, 7, 9, 10],
            'penta': [0, 3, 5, 7, 10],
            'whole': [0, 2, 4, 6, 8, 10],
            'chrom': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}
        self.numbers = self.create_num_fields()
        self.key = self.create_char_field()
        self.scale = self.create_scale_menu()
        self.create_buttons()
        self.quantise = self.create_quant_box()
        self.every_step = self.create_every_note()

    def grab_entry_fields(self):  # input is an object of the Inputs() class from orig script.
        #  statements that assign input class attributes to .get() for relevant fields
        data = []
        for item in self.numbers:
            data.append(int(item[1].get()))
        data.append(self.key.get())
        data.append(self.scale.get('active'))
        data.append(self.every_step.get())
        data.append(self.quantise.get())
        return data

    def generate_output(self):
        output = FormInputs(self.grab_entry_fields())
        generate = RandomNote(output)
        generate.note_processor()

    def port_popup(self):
        port_list = mido.get_output_names()
        text = 'Available MIDI ports are \n'
        for name in range(0, len(port_list)):
            text += ' %s %s\n' % (name, port_list[name])
        messagebox.showinfo('MIDI OUT', text)

    def clear_all(self):
        for field in self.numbers:
            field[1].delete(0, 'end')
        self.key.delete(0, 'end')
        self.quantise.set(False)
        self.every_step.set(False)
        self.populate_defaults()

    def populate_defaults(self):
        index = 0
        for field in self.numbers:
            field[1].insert(0, self.defaults[index])
            index += 1
        self.key.insert(0,self.defaults[-2])

    def create_num_fields(self):
        entries = []
        row = 0
        for field in self.num_fields:
            lab = tk.Label(width=15, text=field)
            ent = tk.Entry(width=3)
            ent.insert('0', str(self.defaults[row]))
            lab.grid(sticky='w', column=0, row=row)
            ent.grid(sticky='e', column=1, row=row)
            entries.append((field, ent))
            row += 1
        return entries

    def create_char_field(self):
        lab = tk.Label(width=15, text="Key")
        key_field = tk.Entry(width=3)
        key_field.insert('0', self.defaults[-2])
        lab.grid(column=0, row=8, pady=5, sticky='w',)
        key_field.grid(column=1, row=8, pady=5, sticky='e')
        return key_field

    def create_scale_menu(self):
        lab = tk.Label(width=15, text="Scale")
        ddown = tk.Listbox(root, height=len(self.key_maps))
        lab.grid(column=0, row=9, pady=5, sticky='w')
        ddown.grid(column=1, row=9, pady=5, sticky='e')
        for key in self.key_maps.keys():
            ddown.insert("end", key)
        return ddown

    def create_every_note(self):
        label = 'Play Every Step?'
        step_var = tk.IntVar(root, label)
        step_var.set(False)
        every_step = tk.Checkbutton(root, text=label,var=step_var)
        every_step.grid(column=2, row=3, padx=30, sticky='w')
        return step_var

    def create_quant_box(self):
        label = 'Quantise Gate Length Modulation?'
        quant_state = tk.IntVar(root, label)
        quant_state.set(False)
        quantise = tk.Checkbutton(root,text=label, variable=quant_state)
        quantise.grid(column=2, row=6, padx=30)
        return quant_state

    def create_buttons(self):
        clear = tk.Button(root, text='Return to Defaults', command=self.clear_all)
        play = tk.Button(root,text='Play Sequence', command=self.generate_output, bg='green')
        display_ports = tk.Button(root, text='Display Ports', command=self.port_popup)
        clear.grid(column=3, row=0, padx = 30, pady=5, sticky='n')
        play.grid(column=3, row=11, padx=10, pady=10, sticky='sw')
        display_ports.grid(column=2, row=0, padx=15, sticky='w')
        quit_button = tk.Button(root, text="Quit", bg="red",
                                command=self.master.destroy)
        quit_button.grid(column=4, row=11, padx=30)


class FormInputs:
    def __init__(self, user_data):  # user_data is a list returned by the Interface class when play burron
        self.key_values = {'c': 0, 'c#': 1, 'd': 2, 'd#': 3, 'e': 4,
                           'f': 5, 'f#': 6, 'g': 7, 'g#': 8, 'a': 9, 'a#': 10, 'b': 11}
        self.key_maps = {
            'maj': [0, 2, 4, 5, 7, 9, 11],
            'min': [0, 2, 3, 5, 7, 9, 10],
            'penta': [0, 3, 5, 7, 10],
            'whole': [0, 2, 4, 6, 8, 10],
            'chrom': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        }
        #  assign class variables to the inputs obtained from the Interface class
        self.port = user_data[0]
        self.channel = user_data[1] - 1
        self.bpm = user_data[2]
        self.bars = user_data[3]
        self.note_value = user_data[4]
        self.octave_range = user_data[5]
        self.gate_mod = user_data[6]
        self.time_mod = user_data[7]
        self.key = user_data[8]
        self.scale_type = user_data[9]
        self.every_step = user_data[10]
        self.quantise_gate = user_data[11]

        #  calculate further variables using data above and local class methods
        self.interval = self.get_timebase()
        self.scale = self.scale_gen()

    def get_port(self):  # requests user port
        port_list = mido.get_output_names()
        return port_list[self.port]

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

    def set_note_range(self):  # requests octave range and returns corresponding MIDI note number range
        octs = self.octave_range
        note_range = [60, 72]
        if octs == 1:
            return note_range
        else:
            note_range[0] -= (12 * int(octs / 2))
            note_range[1] = 60 + (12 * int(octs / 2))
            note_range[1] += (12 * (octs % 2))
        return note_range

    def scale_gen(self):  # method to organise note list generation, returns note list
        scale_offset = self.key_values[self.key.lower()]
        note_range = [n+scale_offset for n in (self.set_note_range())]
        note_key = self.key_maps[self.scale_type]
        return self.note_list_gen(note_key, note_range)

    def get_timebase(self):  # returns standard time interval between notes using user bpm and note value
        return (16/float(self.note_value)) * ((60.0 / float(self.bpm)) / 4.0)


class RandomNote:
    def __init__(self, inputs):
        self.params = inputs  # stores all the user input variables needed to define the sequence
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

    def micro_time(self):
        """ applies random timing variation to interval time and returns corrected interval length
            nb: this method currently has no reference to grid so use of timing modulation will
            result in the sequence playing in free time"""
        if random.getrandbits(1):
            return self.params.interval + (self.params.interval * (self.params.time_mod/100))
        else:
            return self.params.interval - (self.params.interval * (self.params.time_mod/100))

    def play_note(self, note):  # outputs note on and note off message for each iteration of note_processor loop
        msg = mido.Message('note_on', channel=self.params.channel, note=note)
        self.out_port.send(msg)
        sleep(self.gate_length())
        msg = mido.Message('note_off', channel=self.params.channel, note=note)
        self.out_port.send(msg)

    def note_processor(self):  # co-ordinates output of note messages
        loops = self.params.note_value * self.params.bars
        last_note = random.choice(self.params.scale)
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

    root = tk.Tk()
    app = Interface(master=root)
    app.master.title("Random Note Generator")
    app.mainloop()

