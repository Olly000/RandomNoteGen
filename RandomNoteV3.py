#!/usr/bin/env PYTHON3

import mido
import pygame.midi as pym
import tkinter as tk
import random
import threading
from tkinter import messagebox
from time import sleep
from timeit import default_timer as dtime

mido.set_backend('mido.backends.pygame')

pym.init()


class Switcher:  # manages state
    def __init__(self):
        self.run_state = False

    def switch_on(self):
        self.run_state = True

    def switch_off(self):
        self.run_state = False


class Interface(tk.Frame):  # Creates the app's GUI and initiates processing through generate_output method
    def __init__(self, switch, master=None):
        super().__init__(master)
        self.master = master
        self.switch = switch
        self.num_fields = ['Port No', 'Channel', 'BPM', 'No. of Bars',
                           'Note Length', 'Octave Range', 'Gate Mod', 'Time Mod']
        self.defaults = [0, 1, 120, 8, 16, 2, 0, 0, 'c', 'maj']
        self.key_maps = {
            'maj': [0, 2, 4, 5, 7, 9, 11],
            'min': [0, 2, 3, 5, 7, 9, 10],
            'penta': [0, 3, 5, 7, 10],
            'whole': [0, 2, 4, 6, 8, 10],
            'chrom': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}
        self.numbers = self.create_num_fields()
        self.key = self.create_char_field()
        self.scale = self.create_scale_menu()
        self.quantise = self.create_quant_box()
        self.every_step = self.create_every_note()
        self.start_ext_seq = self.create_seq_start()
        self.buttons = self.create_buttons()

    def end_app(self) -> None:
        """ Callback from the quit button - ends note processing by setting run_state to false and
        destroys tk.frame
        """
        self.switch.switch_off()
        self.master.destroy()
        print('App terminated by user')

    def stop_seq(self) -> None:
        """ Stops a note sequence while it is running, sets button widgets states to allow another sequence
        to be started by user
        """
        self.switch.switch_off()
        self.buttons['stop'].config(state='disabled')
        self.buttons['play'].config(state='normal')

    def grab_entry_fields(self) -> dict:
        """ Gets data input from user entry/tickbox and menu widgets and returns it as a dict
        :return: a dict containing data entered into widgets by user
        """
        data = []
        fields = self.num_fields + ['Key', 'Scale', 'Every Step', 'Quantise', 'Start Ext Seq']
        for item in self.numbers:
            data.append(int(item[1].get()))
        data.append(self.key.get())
        data.append(self.scale.get('active'))
        data.append(self.every_step.get())
        data.append(self.quantise.get())
        data.append(self.start_ext_seq.get())
        return dict(zip(fields, data))

    def generate_output(self) -> None:
        """ Creates instances of the input handling class FormInputs and the note generating class
        RandomNote then runs the note generation method of RandomNote
        in a new thread"""
        self.switch.switch_on()
        self.buttons['play'].config(state='disabled')
        self.buttons['stop'].config(state='normal')
        user_input = FormInputs(self.grab_entry_fields())
        generate = RandomNote(user_input, self.switch)
        process_thread = threading.Thread(target=generate.loop_controller)
        process_thread.start()
        process_thread.join()
        self.buttons['stop'].config(state='disabled')
        self.buttons['play'].config(state='normal')

    def start_threads(self) -> None:
        """ Triggered as a callback from the play button - starts a new thread for generate_output - needed to
        handle button states without blocking interface thread"""
        generate_thread = threading.Thread(target=self.generate_output)
        generate_thread.start()

    @staticmethod
    def port_popup() -> None:
        """ Creates a messagebox pop-up window listing available MIDI ports. Triggered as a callback
        from the display port button
        """
        port_list = mido.get_output_names()
        text = 'Available MIDI ports are \n'
        for name in range(0, len(port_list)):
            text += ' %s %s\n' % (name, port_list[name])
        messagebox.showinfo('MIDI OUT', text)

    def clear_all(self) -> None:
        """ Clears all user input data and returns all widgets to default values. Triggered as a callback from the
        clear button
        """
        for field in self.numbers:
            field[1].delete(0, 'end')
        self.key.delete(0, 'end')
        self.quantise.set(False)
        self.every_step.set(False)
        self.populate_defaults()

    def populate_defaults(self) -> None:
        """ Inserts default data values stored in class variable self.defaults into widgets
        """
        index = 0
        for field in self.numbers:
            field[1].insert(0, self.defaults[index])
            index += 1
        self.key.insert(0, self.defaults[-2])

    def create_num_fields(self) -> list:
        """ Creates entry widgets for all of the numerical data required from user and returns the widget
        objects as a list
        :return: list of widgets
        """
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

    def create_char_field(self) -> object:
        """ Creates an entry widget for key, which requires a string as input
        :return: entry widget
        """
        lab = tk.Label(width=15, text="Key")
        key_field = tk.Entry(width=3)
        key_field.insert('0', self.defaults[-2])
        lab.grid(column=0, row=8, pady=5, sticky='w',)
        key_field.grid(column=1, row=8, pady=5, sticky='e')
        return key_field

    def create_scale_menu(self) -> object:
        """ Creates a listbox widget to allow user to enter musical scale of sequence
        :return: listbox widget
        """
        lab = tk.Label(width=15, text="Scale")
        ddown = tk.Listbox(root, height=len(self.key_maps))
        lab.grid(column=0, row=9, pady=5, sticky='w')
        ddown.grid(column=1, row=9, pady=5, sticky='e')
        for key in self.key_maps.keys():
            ddown.insert("end", key)
        return ddown

    @staticmethod
    def create_every_note() -> object:
        """ creates a tickbox to decide whether to play on every step, when out of scale note is generated
        :return: tickbox widget
        """
        label = 'Play Every Step?'
        step_var = tk.IntVar(root, label)
        step_var.set(False)
        every_step = tk.Checkbutton(root, text=label, var=step_var)
        every_step.grid(column=2, row=3, padx=30, sticky='w')
        return step_var

    @staticmethod
    def create_seq_start() -> object:
        """creates a tickbox to decide whether to send a start message to an external sequencer
        - used to record output
        :return: tickbox widget"""
        label = 'Start External Sequencer?'
        seq_var = tk.IntVar(root, label)
        seq_var.set(False)
        start_ext_seq = tk.Checkbutton(root, text=label, var=seq_var)
        start_ext_seq.grid(column=2, row=9, padx=30, sticky='nw')
        return seq_var

    @staticmethod
    def create_quant_box() -> object:
        """ Creates a tickbox widget to decide whether gate length modulation should be quantised
        :return: tickbox widget
        """
        label = 'Quantise Gate Length Modulation?'
        quant_state = tk.IntVar(root, label)
        quant_state.set(False)
        quantise = tk.Checkbutton(root, text=label, variable=quant_state)
        quantise.grid(column=2, row=6, padx=30)
        return quant_state

    def create_buttons(self) -> dict:
        """ Creates buttons to allow user to start and stop sequence and to clear data, display ports and
        quit the app
        :return: dict of labelled button widgets
        """
        clear = tk.Button(root, text='Return to Defaults', command=self.clear_all)
        play = tk.Button(root, text='Play Sequence', command=self.start_threads, bg='green')
        stop_seq = tk.Button(root, text='Stop Sequence', command=self.stop_seq, bg='yellow', state='disabled')
        display_ports = tk.Button(root, text='Display Ports', command=self.port_popup)
        quit_button = tk.Button(root, text="Quit", bg="red", command=self.end_app)
        clear.grid(column=3, row=0, padx=30, pady=5, sticky='n')
        play.grid(column=3, row=11, padx=10, pady=10, sticky='sw')
        stop_seq.grid(column=3, row=12, padx=10, pady=10, sticky='sw')
        display_ports.grid(column=2, row=0, padx=15, sticky='w')
        quit_button.grid(column=4, row=12, padx=30)
        return {'clear': clear, 'play': play, 'stop': stop_seq, 'display': display_ports, 'quit': quit_button}


class FormInputs:
    def __init__(self, user_data: dict) -> None:
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
        self.port = user_data['Port No']
        self.channel = user_data['Channel'] - 1
        self.bpm = user_data['BPM']
        self.bars = user_data['No. of Bars']
        self.note_value = user_data['Note Length']
        self.octave_range = user_data['Octave Range']
        self.gate_mod = user_data['Gate Mod']
        self.time_mod = user_data['Time Mod']
        self.key = user_data['Key']
        self.scale_type = user_data['Scale']
        self.every_step = user_data['Every Step']
        self.quantise_gate = user_data['Quantise']
        self.start_ext_seq = user_data['Start Ext Seq']

        #  calculate further variables using data above and local class methods
        self.interval = self.get_timebase()
        self.scale = self.scale_gen()

    def get_port(self) -> str:
        """ Checks available MIDI ports and returns the name of the port chosen as a string
        No longer called in GUI version of the app
        :return: name of MIDI port to be used
        """
        port_list = mido.get_output_names()
        return port_list[self.port]

    @staticmethod
    def note_list_gen(note_key: int, note_range: list) -> list:
        """ Takes in the key offset value and the highest and lowest notes to be output
        amd returns a list of notes as ints to be played
        :param note_key:
        :param note_range:
        :return:
        """
        note_list = []
        for n in note_key:
            note_list.append(note_range[0] + n)
        while note_list[-1] < note_range[1]:
            note_key = [n + 12 for n in note_key]
            for n in note_key:
                if note_list[-1] < note_range[1]:
                    note_list.append(note_range[0] + n)
        return note_list

    def set_note_range(self) -> list:
        """ Uses the octave range specified by user to calculate the highest and lowest note numbers to
        be played
        :return: highest and lowest note numbers to be played
        """
        note_range = [60, 72]
        if self.octave_range == 1:
            return note_range
        else:
            note_range[0] -= (12 * int(self.octave_range / 2))
            note_range[1] = 60 + (12 * int(self.octave_range / 2))
            note_range[1] += (12 * (self.octave_range % 2))
        return note_range

    def scale_gen(self) -> list:
        """ Organises note list generation by calling various class methods, returns note list
        :return: list of notes to be played by sequencer
        """
        scale_offset = self.key_values[self.key.lower()]
        note_range = [n+scale_offset for n in (self.set_note_range())]
        note_key = self.key_maps[self.scale_type]
        return self.note_list_gen(note_key, note_range)

    def get_timebase(self) -> float:
        """ Calculates standard time interval between notes using user bpm and note value specified by user
        :return: interval between note on messages
        """
        return (16/float(self.note_value)) * ((60.0 / float(self.bpm)) / 4.0)


class RandomNote:
    def __init__(self, inputs, switch):
        self.params = inputs  # stores all the user input variables needed to define the sequence
        self.switch = switch
        self.out_port = mido.open_output(self.params.get_port())

    def note_gen(self) -> int:
        """ generate a random number within the note range defined by Inputs.scale variable
        :return: a MIDI note number as an int
        """
        return random.randint(self.params.scale[0], (self.params.scale[-1]+1))

    def scale_check(self, note: int) -> int:
        """ checks whether note generated by note_gen is in the params.scale variable
        returns false if note is not found
        :param note:
        :return: note or False
        """
        if note in self.params.scale:
            return note
        else:
            return False

    def gate_length(self) -> float:
        """ applies gate length modulation to note, returns corrected gate length
        :return: adjusted time between note on and note off
        """
        mod_amount = (random.random() * self.params.gate_mod)/100
        if random.getrandbits(1):
            return (self.params.interval/2.0) + ((self.params.interval/2)*mod_amount)
        else:
            return (self.params.interval/2.0) - ((self.params.interval/2)*mod_amount)

    def gate_length_quant(self) -> float:
        """ as gate_length but quantised to 16ths
        :return: adjusted time between note on a nd note off
        """
        mod_options = [-0.75, -0.5, -0.25, -0.125, 0.125, 0.25, 0.5, 0.75]
        for mod in mod_options:
            if abs(mod * 100) > self.params.gate_mod:
                mod_options.remove(mod)
        for n in range(0, int(len(mod_options) / 2)):
            mod_options.append(0)
        return (self.params.interval/2) + (random.choice(mod_options) * (self.params.interval/2))

    def micro_time(self) -> float:
        """ applies random timing variation to interval time and returns corrected interval length
            nb: this method currently has no reference to grid so use of timing modulation will
            result in the sequence playing in free time
            :return: length of rest between note off and next note on"""
        if random.getrandbits(1):
            return self.params.interval + (self.params.interval * (self.params.time_mod/100))
        else:
            return self.params.interval - (self.params.interval * (self.params.time_mod/100))

    def play_note(self, note: int) -> None:
        """ Outputs note on and off messages for each iteration of note_processor loop
        :param note: MIDI note number
        """
        msg = mido.Message('note_on', channel=self.params.channel, note=note)
        self.out_port.send(msg)
        sleep(self.gate_length())
        msg = mido.Message('note_off', channel=self.params.channel, note=note)
        self.out_port.send(msg)

    def note_processor(self, last_note: int) -> int:
        """ takes the last note played, generates a new random note, checks it is in note_list then
        plays generated note or last note.  Returns the note played
        :param last_note: the note played by the previous iteration of loop_controller
        :return: note sent to play_note method
        """
        note = self.scale_check(self.note_gen())
        if note:
            self.play_note(note)
            return note
        elif self.params.every_step:
            self.play_note(last_note)
            return last_note

    def clock_out(self):
        """ sends start/clock/stop messages to external sequencer
        """
        interval = 60/(24 * self.params.bpm)
        self.out_port.send(mido.Message('start'))
        while self.switch.run_state:
            self.out_port.send(mido.Message('clock'))
            sleep(interval)

    def start_sequencer(self) -> None:
        """ checks status of start_ext_seq parameter and initiates clock_out method in a new
        thread
         """
        if self.params.start_ext_seq:
            clock_thread = threading.Thread(target=self.clock_out)
            clock_thread.start()

    def end_of_loop_process(self) -> None:
        """ Informs user of reason for loop ending and closes the active MIDI port
        """
        if self.switch.run_state:
            print('End of pattern')
            self.switch.switch_off()
        else:
            print('Sequence ended by user')
        self.out_port.close()

    def loop_controller(self) -> None:
        """ organises note output - iterates through the number of loops specified by user, checking
        end of seq has not been indicated by change in run_state
        """
        loops = self.params.note_value * self.params.bars
        last_note = random.choice(self.params.scale)
        self.start_sequencer()
        while loops > 0 and self.switch.run_state:
            loops -= 1
            start = dtime()
            rest = self.micro_time()
            last_note = self.note_processor(last_note)
            end = dtime()
            sleep(rest - (end - start))
        self.end_of_loop_process()


if __name__ == '__main__':

    root = tk.Tk()
    state_manager = Switcher()
    gui = Interface(state_manager, master=root)
    gui.master.title("Random Note Generator")
    gui.mainloop()
