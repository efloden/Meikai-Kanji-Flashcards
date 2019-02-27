# -*- coding: utf-8 -*-

"""
Meikaichan 1.0

Copyright (C) 2014 Earl Mark Floden -earl.floden@uqconnect.edu.au

Example dictionary .gif files sourced from: https://www.coscom.co.jp/japanesekanji/kanji50/
Example dictionary .mp3 files sourced from Google Translate API.

DESCRIPTION

Meikaichan 1.0 is the second version of a Kanji flash card learning program. It displays the English meaning, Kanji symbol, Hiragana, audio, and accompanying image for each card.

Meikaichan 1.0 only supports JSON dictionary files with image and audio paths.

LICENSE

I, Earl Mark Floden, Hereby grant the rights to distribute, modify, and edit the
source to Meikaichan , on the condition that this agreement, and my ownership
of the code contained herewithin be maintained.

Furthurmore, I grant the right to use excerpts from the source to Meikaichan 
without express permission, with exclusion of commercial application.
"""

from Tkinter import *
import random
import json
import pygame
import tkMessageBox
import tkFileDialog
import codecs

codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)
pygame.mixer.init(16000)

DISPLAY_FORMAT = "{0}{1}{2}{4}"

class Kanjicard(object):

    def __init__(self, meaning, kanji, hiragana, image, audio):
        """Initializes the Kanji Card, supplying it with a kanji, meaning, and

        image file name.
        """
        self._kanji = kanji
        self._hiragana = hiragana
        self._meaning = meaning
        self._image = image
        self._audio = audio

    def get_kanji(self):
        """Returns the Kanji of a card.

        get_kanji(self._kanji) --> str
        """
        return self._kanji

    def get_hiragana(self):
        return self._hiragana

    def get_meaning(self):
        """Returns the meaning of a card.

        get_meaning(self._meaning) --> str
        """
        return self._meaning

    def get_image(self):
        """Returns the image file of a card.

        get_image(self._image) --> str
        """
        return self._image

    def get_audio(self):
        """Returns the audio file of a card.

        get_audio(self._audio) --> str
        """
        return self._audio

    def __str__(self):
        """Returns a str of Kanjicard in DISPLAY_FORMAT.

        __str__(Kanjicard) --> str"""
        return DISPLAY_FORMAT.format(self.get_kanji, self.get_meaning, self.get_image)

    def __repr__(self):
        """Returns a repr of Kanjicard.

        __repr__(Kanjicard) --> str"""
        return "Kanjicard({0}, {1}, {2}, {3})".format(self.get_kanji, self.get_meaning, self.get_image)

class Cardlist(object):

    def __init__(self):
        """Initializes the Cards List to be empty.

        __init__(Cardlist) --> void
        """

        self._cards = []
        
    def load_file(self, filename):
        """Read a Cardlist from a .json file.

        load_file(dict) -> list((kanji, meaning, image, audio))
        """
        fd = codecs.open(filename, 'rU', 'utf-8')
        tmp_dict = json.load(fd, 'utf-8')
        for key in tmp_dict:
            meaning = key
            kanji, hiragana, image, audio = tmp_dict[key]
            self._cards.append(Kanjicard(meaning, kanji, hiragana, image, audio))
        fd.close()

    def get_index(self, index):
        """Returns the index of a card.

        get_index(Cardlist, index) --> index
        """
        return self._cards[index]

    def length(self):
        """Returns the length of the card list.

        length(Cardlist) --> length
        """
        return len(self._cards)

    def __str__(self):
        """Returns a str of the card list.

        __str__(Cardlist) --> str
        """
        return "{0}".format(self._cards)

class Controller(object):
    def __init__(self, master):
        """
        Controller is the controller of the Meikaichan program
        it contains labels, a menu, four main frames and a canvas.
        all elements of the program are linked through the controller.
        __init__(Controller, tk) --> void
        """
        
        #Global elements

        #Displayed list
        self._displayed = []
        
        #setup the app basic specifications: title, close protocol, size.
        self._master = master
        master.title("Meikaichan 1.0")
        master.protocol("WM_DELETE_WINDOW", self.quit)
        master.minsize(500, 375)
        master.maxsize(700, 525)
        
        #Initialize a Cardlist, attempt count, and correct answer count.
        self._items = Cardlist()
        self._acount = 0
        self._ccount = 0
        
        #Set up a random audio file for incorrect answers.
        self._shikkari = ""
        self._chigau = ""
        self._aho = ""
        self._batsu = []
        self._rnum = int

        #Initialize the mode flags, set default to Meikai.
        self._meikai = True
        self._seikai = 0
        self._reikai = 0
        self._timestart = True

        #Create a menubar
        menubar = Menu(master)
        master.config(menu=menubar)

        filemenu = Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open Card List", command=self.open_file)
        filemenu.add_command(label="Save Card List", command=self.save)
        filemenu.add_command(label="Meikaimodo", command=self.meikai)
        filemenu.add_command(label="Seikaimodo", command=self.seikai)
        filemenu.add_command(label="Reikaimodo", command=self.reikai)
        filemenu.add_command(label="Exit", command=self.close)

        #Create a welcome label for the app. Japanese text = "Hello World!"
        frame2 = Frame(master)
        frame2.pack(side=TOP)
        self._label = Label(frame2, text='ようこそ世界へ！\n Welcome to Meikaichan, please load a .json file', font=30)
        self._label.pack(side=TOP, pady=5, padx=5)
        self._libel = Label(frame2, text="", font=30)
        self._libel.pack(side=TOP)

        #Create a frame, give it a background and pack a Canvas to it for the default image.
        self._Cframe = Frame(master)
        self._Cframe.pack(side=TOP)
        self._c = Canvas(self._Cframe, width=350, height=350, background = 'white')
        self._c.pack(expand = YES, fill = BOTH)
        
        self._c.default = PhotoImage(file='img/default.gif')
        self._item = self._c.create_image(25, 25, image=self._c.default, anchor=NW)
        
        self._c.true = PhotoImage(file='img/blank.gif')
        self._marui = self._c.create_image(25, 25, image=self._c.true, anchor=NW)

        #Create a frame, pack entry and widget, submit and listen to it. Hide on open.
        frame3 = Frame(master)
        frame3.pack(side=BOTTOM)

        self._entry = Entry(frame3, width=30)
        self._entry.bind('<Return>', (lambda event: self.Entry_submit()))
        self._entry.pack_forget()
        
        self._submit = Button(frame3, text="Submit", font = 8, command=self.Entry_submit)
        self._submit.pack_forget()

        self._playaudio = Button(frame3, text="Listen", font=8, command=self.Play_Audio)
        self._playaudio.pack_forget()

        self._button1 = Button(frame3, text="", font = 100, command=self.AnswerOne)
        self._button1.pack_forget()
        
        self._button2 = Button(frame3, text="", font = 100, command=self.AnswerTwo)
        self._button2.pack_forget()
        
        self._button3 = Button(frame3, text="", font = 100, command=self.AnswerThree)
        self._button3.pack_forget()


        #Create a frame, pack label to it. Set default as blank.
        frame4 = Frame(master)
        frame4.pack(side=BOTTOM)
        self._clabel = Label(frame4, text="", font=5)
        self._clabel.pack(side=BOTTOM, pady=5, padx=5)

        #Pack a timer to the frame, call a function if the timer reaches zero.
        self._timer = Canvas(frame3, width=27, height=27, bg = 'white', bd = 3, relief=RIDGE)
        self._timer.pack_forget()

    def tick(self):
        """Set a timer to a canvas which counts down, changes color when below 5

        and checks the entry field or returns an incorrect answer

        tick(Controller) --> void
        """
        self._timer.delete(ALL)
        global time
        self._time -= 1
        self._timer.create_text(17, 17, text=self._time, anchor = CENTER)
        
        if self._time == 5:
            self._timer.config(bg = 'red')
            
        if self._time == 0:
            if self._seikai or self._reikai:
                self.Entry_submit()
                self._time = 21
                self._timer.config(bg = 'white')
                self._timer.after(1000, self.tick)
            elif self._meikai:
                pygame.mixer.music.load('sound/chigau.mp3')
                pygame.mixer.music.play()
                self._c.true = PhotoImage(file='img/batsu.gif')
                self._marui = self._c.create_image(25, 25, image=self._c.true, anchor=NW)
                self._clabel.config(bg = 'grey')
                self._time = 21
                self._timer.config(bg = 'white')
                self._timer.after(1000, self.tick)
                self.marutick()
        else:
            self._timer.after(1000, self.tick)
            
    def marutick(self):
        """Set a timer for displaying Red correct circle and incorrect cross

        marutick(Controller) --> void
        """
        global time
        self._marutime -= 1
        if self._marutime == 0:
            self.refresh()
        else:
            self._master.after(1000, self.marutick)
    
    def open_file(self):
        """Opens the tkInter Filedialog to select a file.

        If filename is true, runs load_file on the filename.

        Packs buttons to un-hide. runs self.refresh().
        
        open_file(Controller) --> load_file(filename)
        """
        filename = tkFileDialog.askopenfilename()
        
        if filename:
            self._items.load_file(filename)
            if self._meikai:
                self._timer.pack(side=LEFT, pady=10, padx=20)
                self._button1.pack(side=LEFT, pady = 10, padx = 10)
                self._button2.pack(side=LEFT, pady = 10, padx = 10)
                self._button3.pack(side=LEFT, pady = 10, padx = 10)
                self._playaudio.pack(side=LEFT, pady=10, padx = 20)
                self._time = 21
##                if self._timestart == True:
##                    self._timer.after(1, self.tick)

            if self._seikai:
                self._timer.pack(side=LEFT)
                self._entry.pack(side=LEFT, pady = 10)
                self._submit.pack(side=LEFT, pady = 10, padx = 10)
                self._playaudio.pack(side=LEFT, pady=10)
                self._timer.after(1, self.tick)
                self._time = 21
##                if self._timestart == True:
##                    self._timer.after(1, self.tick)
                
            elif self._reikai:
                self._timer.pack(side=LEFT)
                self._entry.pack(side=LEFT, pady = 10)
                self._submit.pack(side=LEFT, pady = 10, padx = 10)
                self._timer.after(1, self.tick)
                self._time = 21
##                if self._timestart == True:
##                    self._timer.after(1, self.tick)

            elif self._timestart == True:
                self._timer.after(1, self.tick)
                    
            self._timestart = False
            self.refresh()
            
    def Play_Audio(self):
        """Plays the audio file in the location of self._afile.

        Play_Audio(Controller) --> audiofile
        """
        pygame.mixer.music.load("{}".format(self._afile))
        pygame.mixer.music.play()

    def Entry_submit(self):
        """Calls the check_answer function on the buttons text.

        Increments the self._acount var, and calls self.refresh.

        AnswerOne(Controller) --> void
        """
        self.check_answer(self._entry.get().lower())
        self._entry.delete(0, END)
        self._acount += 1

    def AnswerOne(self):
        """Calls the check_answer function on the buttons text.

        Increments the self._acount var, and calls self.refresh.

        AnswerOne(Controller) --> void
        """
        self.check_answer(self._button1.config('text')[-1])
        self._acount += 1

    def AnswerTwo(self):
        """Calls the check_answer function on the buttons text.

        Increments the self._acount var, and calls self.refresh.

        AnswerTwo(Controller) --> void
        """
        self.check_answer(self._button2.config('text')[-1])
        self._acount += 1

    def AnswerThree(self):
        """Calls the check_answer function on the buttons text.

        Increments the self._acount var, and calls self.refresh.

        AnswerThree(Controller) --> void
        """
        self.check_answer(self._button3.config('text')[-1])
        self._acount += 1

    def check_answer(self, text):
        """Checks if the text of the correct meaning is the same as that

        of the button clicked by the user. If correct increments the correct
        
        answer count and changes the label color to green, otherwise changes
        
        the label color to grey.
        
        check_answer(Controller, str) --> void
        """
        self._time = 21
        
        if self._meikai:
            if self._answer1 == text:
                pygame.mixer.music.load('sound/seikai.mp3')
                pygame.mixer.music.play()
                self._c.true = PhotoImage(file='img/maru.gif')
                self._marui = self._c.create_image(25, 25, image=self._c.true, anchor=NW)
                self._ccount += 1
                self._clabel.config(bg = 'green')
            else:
##                pygame.mixer.music.load(self._batsu[self._rnum])
                pygame.mixer.music.load('sound/chigau.mp3')
                pygame.mixer.music.play()
                self._c.true = PhotoImage(file='img/batsu.gif')
                self._marui = self._c.create_image(25, 25, image=self._c.true, anchor=NW)
                self._clabel.config(bg = 'grey')
        elif self._seikai:   
            if self._answer1.lower() == text:
                pygame.mixer.music.load('sound/seikai.mp3')
                pygame.mixer.music.play()
                self._c.true = PhotoImage(file='img/maru.gif')
                self._marui = self._c.create_image(25, 25, image=self._c.true, anchor=NW)
                self._ccount += 1
                self._clabel.config(bg = 'green')
            else:
##                pygame.mixer.music.load(self._batsu[self._rnum])
                pygame.mixer.music.load('sound/aho.mp3')
                pygame.mixer.music.play()
                self._c.true = PhotoImage(file='img/batsu.gif')
                self._marui = self._c.create_image(25, 25, image=self._c.true, anchor=NW)
                self._clabel.config(bg = 'grey')
        elif self._reikai:
            if self._hiraga == text:
                pygame.mixer.music.load('sound/seikai.mp3')
                pygame.mixer.music.play()
                self._c.true = PhotoImage(file='img/maru.gif')
                self._marui = self._c.create_image(25, 25, image=self._c.true, anchor=NW)
                self._ccount += 1
                self._clabel.config(bg = 'green')
            else:
##                pygame.mixer.music.load(str(self._batsu[self._rnum]))
                pygame.mixer.music.load('sound/shikkari.mp3')
                pygame.mixer.music.play()
                self._c.true = PhotoImage(file='img/batsu.gif')
                self._marui = self._c.create_image(25, 25, image=self._c.true, anchor=NW)
                self._clabel.config(bg = 'grey')
        self.marutick()
                
    def refresh(self):
        """Updates all buttons and labels with values from the JSON file dict.

        Uses the random module to randomize the Kanji and Meanings displayed.

        refresh(Controller) --> void
        """
        
        #updates the label displaying user attempt and correct answer count 
        self._clabel.config(text="Attempts: {0},  Correct: {1}/30".format(self._acount, self._ccount))
        self._time = 21
        self._marutime = 2
        
        #Turns the timer canvas white.
        self._timer.config(bg = 'white')
        
        #Assigns a random card from the Cardlist to kj_card
        num = random.randint(0, self._items.length()-1)
        kj_card = self._items.get_index(num)
        
        while kj_card in self._displayed:
            num = random.randint(0, self._items.length()-1)
            kj_card = self._items.get_index(num)

        self._displayed.append(kj_card)
        if len(self._displayed) == 30:
            self._displayed = []
        
        #Configure the Kanji label and Correct Answer button
        self._label.config(text=kj_card.get_kanji())
        if self._meikai or self._seikai:
            self._libel.config(text=kj_card.get_hiragana())
        self._afile = kj_card.get_audio()
        self._c.delete(self._item)
        self._c.current = PhotoImage(file=kj_card.get_image())
        self._c.create_image(25, 25, image=self._c.current, anchor=NW)
        self._answer1 = kj_card.get_meaning()
        self._hiraga = kj_card.get_hiragana()

        self._c.true = PhotoImage(file='img/blank.gif')
        self._marui = self._c.create_image(25, 25, image=self._c.true, anchor=NW)

        #Configure the Incorrect Answer buttons
        bnum = random.randint(0,2)
        
        nu = random.randint(0, self._items.length()-1)
        k_card = self._items.get_index(nu)
        self._answer2 = k_card.get_meaning()
        
        n = random.randint(0, self._items.length()-1)
        kcard = self._items.get_index(n)
        self._answer3 = kcard.get_meaning()

        #Randomly configuring the Buttons to be 1 of 3
        alist = [self._answer1, self._answer2, self._answer3]
        self._button1.config(text=alist[bnum])
        alist.pop(bnum)
        rnum = random.randint(0,1)
        self._button2.config(text=alist[rnum])
        alist.pop(rnum)
        self._button3.config(text=alist[0])

        #Set up a random audio file for incorrect answers.
        self._rnum = random.randint(0,2)
        self._shikkari = 'sound/shikkari.mp3'
        self._chigau = 'sound/chigau.mp3'
        self._aho = 'sound/aho.mp3'
        self._batsu = [self._shikkari, self._chigau, self._batsu]

        #Once correct answers reach 30, open tkMessagebox, if OK,
        #reset attempts, correct answers to 0
        if self._ccount == 30:
            ans = tkMessageBox.askokcancel(
                'Deck Complete', "Congratulations! You've completed this deck. Start Again?"
                )
            if ans:
                self._ccount = 0
                self._acount = 0
                self.refresh()

    def save(self):
##      placeholder for later versions
        pass
    
    def close(self):
        """Asks the user to confirm whether they would like to exit.

        close(Controller) --> destroy
        """
        ans = tkMessageBox.askokcancel('Verify exit', "Really exit?")
        if ans: self._master.destroy()

    def quit(self):
        """Asks the user to confirm whether they would like to exit.

        close(Controller) --> destroy
        """
        ans = tkMessageBox.askokcancel('Verify exit', "Really exit?")
        if ans: self._master.destroy()

    def meikai(self):
        """Sets the Meikai mode flag to True, gives it a custom title. Calls hide_all.

        meikai(Controller) --> void
        """
        self._meikai = True
        self._seikai = False
        self._reikai = False
        self._label.config(text="めいかいモード\nMeikai Mode:\nChoose the Kanji meaning")
        self.hide_all()
        
    def seikai(self):
        """Sets the Seikai mode flag to True, gives it a custom title. Calls hide_all.

        seikai(Controller) --> void
        """
        self._meikai = False
        self._seikai = True
        self._reikai = False
        self._label.config(text="せいかいモード\nSeikai Mode:\nWrite the Kanji meaning")
        self.hide_all()

    def reikai(self):
        """Sets the Reikai mode flag to True, gives it a custom title. Calls hide_all.

        reikai(Controller) --> void
        """
        self._meikai = False
        self._seikai = False
        self._reikai = True
        self._label.config(text="れいかいモード\nReikai Mode:\nWrite the Hiragana before the time runs out")
        self.hide_all()

    def hide_all(self):
        """Hides all widgets to default to the open screen. Resets answer, correct

        and image data to default. Calls the refresh function.

        hide_all(Controller) -- void
        """
        self._timer.pack_forget()
        self._entry.pack_forget()
        self._submit.pack_forget()
        self._button1.pack_forget()
        self._button2.pack_forget()
        self._button3.pack_forget()
        self._playaudio.pack_forget()
        self._acount = 0
        self._ccount = 0
        self._c.true = PhotoImage(file='img/blank.gif')
        self._c.create_image(25, 25, image=self._c.true, anchor=NW)
        self._c.current = PhotoImage(file='img/default.gif')
        self._c.create_image(25, 25, image=self._c.current, anchor=NW)
        self._clabel.config(text="", bg=None)
        self._libel.config(text="", bg=None)
        self.refresh
                     
class Meikaiapp(object):
    def __init__(self, master=None):
        master.title("Meikai")
        self.controller = Controller(master)

def main():
        #run the Meikaiapp
        root = Tk()
        app = Meikaiapp(root)
        root.mainloop()

if __name__ == '__main__':
    main()
