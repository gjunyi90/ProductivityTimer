import platform
from datetime import datetime
import os

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

FONT_NAME = 'Courier'

LABEL_SIZE = 5
TIME_SIZE = 20
DELETE_SIZE = 15
ADD_SIZE = 0

GRIP_COLOUR = '#0E1170'
TIMER_ACTIVE_COLOUR = 'black'
TIMER_INACTIVE_COLOUR = 'gray'

# from tkinter import *
# root = Tk()

cwd = os.getcwd()


class FauxEvent(object):
    def __init__(self, num):
        self.num = num


CLICK_EVENT = FauxEvent(1)


def scroll_type(event):
    if event.num == 5 or event.delta == -120:
        return -1
    if event.num == 4 or event.delta == 120:
        return 1
    raise RuntimeError('Unknown scroll event, file bugreport: %s' % event)


def bind_scroll(obj, listener):
    def fire_listener(event):
        return listener(event, scroll_type(event))

    if platform.system() == 'Windows':
        obj.bind('<MouseWheel>', fire_listener)
    else:
        obj.bind('<Button-4>', fire_listener)
        obj.bind('<Button-5>', fire_listener)


def convert(seconds):
    """
    Convert seconds to (seconds, minutes, hours, remainder_seconds)
    """
    r = seconds

    s = r % 60
    m = (r - s) % (60 * 60)
    h = (r - s - m) % (60 * 60 * 60)

    return s, int(m / 60), int(h / (60 * 60)), r - (s + m + h)


class Toggle(object):
    def __init__(self, init, other):
        self._init = (init, other)
        self.other = other
        self.value = init

    def flip(self):
        self.value, self.other = self.other, self.value

    def reset(self):
        self.value, self.other = self._init


class Timer(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.wm_title(r'(:')
        # TODO build in time correction
        self.counters = []

        self.iconbitmap(os.path.join(cwd, 'favicon2.ico'))
        # self.mainloop()

        # Draggable window
        # self.overrideredirect(True)
        self.grip = tk.Label(self, bg=GRIP_COLOUR, width=1)
        self.grip.grid(sticky='NESW', column=2, row=0)

        self.grip.bind("<ButtonPress-1>", self.StartMove)
        self.grip.bind("<ButtonRelease-1>", self.StopMove)
        self.grip.bind("<B1-Motion>", self.OnMotion)

        # set initial position
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # self.configure(bg='black')
        self.wm_attributes('-alpha', 0.7, '-toolwindow', False, "-topmost", 1)
        h = 150
        w = 100

        x = screen_width - (w)
        self.max_y = screen_height - (h - 24)

        # calculate position x and y coordinates
        self.geometry('+%d+%d' % (x, self.max_y))
        self.resizable(False, True)

        self.frame = tk.Frame(self)
        self.frame.grid(row=0, column=0, sticky='WE')

        # self.frame.configure(bg='black')
        # Control Buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(column=0, row=1, columnspan=2, sticky='WE')

        self.button_add = tk.Label(self.button_frame, text='+', font=(FONT_NAME, ADD_SIZE), bg='black', fg='white')
        self.button_add.grid(column=0, row=0, sticky='WE')
        self.button_add.bind("<Button-1>", self.create_counter)

        self.button_start = tk.Label(self.button_frame, text='Start', font=(FONT_NAME, ADD_SIZE), bg='black',
                                     fg='white')
        self.button_start.grid(column=1, row=0, sticky='WE')
        self.button_start.bind("<Button-1>", self.start_all)

        self.button_stop = tk.Label(self.button_frame, text='Pause', font=(FONT_NAME, ADD_SIZE), bg='black', fg='white')
        self.button_stop.grid(column=2, row=0, sticky='WE')
        self.button_stop.bind("<Button-1>", self.pause_all)

        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)
        self.button_frame.columnconfigure(2, weight=1)

        self.columnconfigure(0, weight=1)

        self.ticker()

    def mainloop(self, *args, **kwargs):
        for c in self.counters:
            c['counter'].refresh()

        tk.Tk.mainloop(self, *args, **kwargs)

    def StartMove(self, event):
        self.x = event.x
        self.y = event.y

    def StopMove(self, event):
        self.x = None
        self.y = None

    def OnMotion(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry("+%s+%s" % (x, y))

    def pause_all(self, event=None):
        for c in self.counters:
            if not c['counter'].paused:
                c['counter'].clicked(CLICK_EVENT)

    def start_all(self, event=None):
        for c in self.counters:
            if c['counter'].paused:
                c['counter'].clicked(CLICK_EVENT)

    def create_counter(self, event=None, auto=False, work=False):
        frame = tk.Frame(self.frame)
        counter = Counter(frame, auto, work)
        counter.frame.grid(row=0, column=0)

        counter_dict = None  # set at the end

        def delete_counter(event):
            idx = self.counters.index(counter_dict)
            self.counters[idx]['frame'].destroy()
            del self.counters[idx]

            self.frame.rowconfigure(idx, weight=0)
            self.geometry("")

        delete_button = tk.Label(frame, text='X', fg='red', font=('Arial', DELETE_SIZE))
        delete_button.bind("<ButtonPress-1>", delete_counter)
        delete_button.grid(row=0, column=1)

        frame.grid(row=len(self.counters), column=0)
        self.frame.rowconfigure(len(self.counters), weight=1)

        self.counters.append(dict(
            counter=counter,
            frame=frame
        ))
        counter_dict = self.counters[-1]
        counter.refresh()
        self.geometry("")

    def update_counters(self):
        for counter in self.counters:
            counter['counter'].tick()
        # print 'tick'

    def ticker(self):
        self.after(1000, self.ticker)
        self.update_counters()


class Counter(object):
    def __init__(self, master, auto=False, work=False):
        self.frame = tk.Frame(master)
        self.auto_reset = auto
        self.work = work

        self.time_frame = tk.Frame(self.frame)
        self.time_frame.grid(column=0, row=1)

        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        self.now = datetime.now()
        self.timeorig = 60 * 30
        self.time = self.timeorig
        self.MAX = 60 * 60 * 60

        if self.work:
            self.FMT = '%d/%m/%Y %H:%M:%S'
            self.endwork = datetime.strptime(f'{self.now.day}/{self.now.month}/{self.now.year} 17:30:00', self.FMT)
            self.timenow = datetime.strptime(f'{self.now.day}/{self.now.month}/{self.now.year} {self.now.hour}:{self.now.minute}:{self.now.second}', self.FMT)
            self.startwork = datetime.strptime(f'{self.now.day}/{self.now.month}/{self.now.year} 08:00:00', self.FMT)  # startwork = f'{now.day}/{now.month}/{now.year} 08:00:00'
            self.delta = self.startwork.hour*3600+self.startwork.minute*60+self.startwork.second - (self.timenow.hour*3600+self.timenow.minute*60+self.startwork.second)

            if self.delta > 0:
                self.workdelta = self.endwork.second - self.timenow.second
            else:
                self.workdelta =  self.endwork.second - self.startwork.second

            self.time = self.workdelta

        if self.auto_reset:
            self.paused = False
            self.text_colour = Toggle(TIMER_ACTIVE_COLOUR, TIMER_INACTIVE_COLOUR)
        else:
            self.paused = True
            self.text_colour = Toggle(TIMER_INACTIVE_COLOUR, TIMER_ACTIVE_COLOUR)

        # title text for counter

        # self.title_text = tk.StringVar()
        # self.title = tk.Entry(self.frame, font=(FONT_NAME, LABEL_SIZE), textvariable=self.title_text)
        # self.title.grid(sticky='we', column=0, row=0)
        # self.title.focus()

        common = dict(
            font=(FONT_NAME, TIME_SIZE),
            highlightthickness=0,
            borderwidth=0,
            relief='flat'
        )

        self.hour = tk.Label(self.time_frame, **common)
        self.minute = tk.Label(self.time_frame, **common)
        self.second = tk.Label(self.time_frame, **common)

        self.labels = [self.second, self.minute, self.hour]

        for idx, label in enumerate(self.labels):
            change = int(60 ** idx)
            listener = self.scroll_listener(change)

            bind_scroll(label, listener)

            label.bind('<Button-1>', self.clicked)
            label.bind('<Double-Button-1>', self.reset)

    def reset(self, event=None):
        if self.auto_reset == True:
            self.paused = False
            self.time = self.timeorig
        else:
            self.paused = True
            self.time = 0
        self.text_colour.reset()
        self.refresh()

    def clicked(self, event):
        if event.num == 1 and self.time > 0:
            self.paused = not self.paused
            self.text_colour.flip()
            self.refresh()

    def scroll_listener(self, increment, decrement=None):
        def listener(event, delta):
            if not self.paused: return

            value = 0

            if delta == -1:
                value -= decrement or increment
            elif delta == 1:
                value += increment

            self.time += value
            self.time = self.time % self.MAX

            self.refresh()

        return listener

    def tick(self):
        if not self.paused and self.time > 0:
            self.time -= 1
            if self.time == 0:
                self.reset()
        self.refresh()
        # if self.auto_reset and self.time == 0:
        #     self.time = self.timeorig

    def refresh(self):
        times = convert(self.time)
        fmts = [':{:0>2d}'] * 3

        # delete the `:` from the hour
        # so we don't get `:00:00:00`
        fmts[-1] = fmts[-1][1:]

        for idx, f in enumerate(['second', 'minute', 'hour']):
            timestr = fmts[idx].format(times[idx])

            label = getattr(self, f)
            label.configure(text=timestr)
            label.configure(fg=self.text_colour.value)
            label.grid(column=2 - idx, row=1)


def main():
    app = Timer()
    app.create_counter(auto=True, work=True)
    app.create_counter(auto=True, work=False)
    app.mainloop()
    app.StartMove
    app.destroy()


main()
