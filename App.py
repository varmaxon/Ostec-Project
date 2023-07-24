import os
import tkinter
from functools import partial

import pandas as pd
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import showinfo, showerror


def DFRead(file_name):
    if 'csv' in file_name:
        df = pd.read_csv(file_name, sep=';')
    elif 'xlsx' in file_name:
        df = pd.read_excel(file_name)
    else:
        df = pd.read_csv(file_name, sep='\t', )

    return df


class Manager:
    def __init__(self, train_file_name, log_file_path):
        self.__train_file = train_file_name
        for root, dirs, files in os.walk(log_file_path):
            if 'Temperature0.txt' in files:
                self.file_temp = os.path.join(root, 'Temperature0.txt').replace(os.sep, '/')
            elif 'Current0.txt' in files:
                self.file_curr = os.path.join(root, 'Current0.txt').replace(os.sep, '/')
            elif 'Voltage0.txt' in files:
                self.file_volt = os.path.join(root, 'Voltage0.txt').replace(os.sep, '/')
            elif 'Pressure0.txt' in files:
                self.file_pres = os.path.join(root, 'Pressure0.txt').replace(os.sep, '/')

    def read_block(self, file_name, time_ms):
        file_lines = list(reversed(open(file_name).readlines()))

        block = []
        i = 0
        while float(file_lines[i].split('\t')[-1]) == time_ms:
            block.append(file_lines[i])
            i += 1

        return list(reversed(block))

    def block_analysis(self):
        pass

    def general_analysis(self):
        pass


class Bot:
    def __init__(self, TOKEN, manager_):
        self.manager_ = manager_
        self.bot = telegram.Bot(token=TOKEN)
        self.__updater = Updater(token=TOKEN, use_context=True)
        self.__dispatcher = self.__updater.dispatcher

        self.__start_markup = telegram.ReplyKeyboardMarkup.from_button(
            telegram.KeyboardButton(
                text='Анализ состояния печи'
            )
        )
        self.__start_markup.resize_keyboard = True

        self.__back_markup = telegram.ReplyKeyboardMarkup.from_button(
            telegram.KeyboardButton(
                text='Назад'
            )
        )
        self.__back_markup.resize_keyboard = True

        self.__analysis_flag = True

    def start(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='<b>Добро пожаловать в сервис для мониторинга состояния печи.</b>\n\n'
                                  '<b>Анализ состояния печи</b> - Эта функция показывает текущее состояние печи.\n\n'
                                   'Также бот будет предупреждать о возможных авариях.',
                                 reply_markup=self.__start_markup,
                                 parse_mode='HTML')

    def get_text_messages(self, update, context):
        if update.message.text == 'Анализ состояния печи':
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Текущее состояние печи',
                                     reply_markup=self.__back_markup)

        elif update.message.text == 'Назад':
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Главное меню',
                                     reply_markup=self.__start_markup)

        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='<b>Неправильный формат ввода!</b>',
                                     reply_markup=self.__start_markup,
                                     parse_mode='HTML')

    def handler(self):
        start_handler = CommandHandler('start', self.start)
        self.__dispatcher.add_handler(start_handler)

        text_handler = MessageHandler(Filters.text & (~Filters.command), self.get_text_messages)
        self.__dispatcher.add_handler(text_handler)

    def run(self):
        self.handler()
        self.__updater.start_polling()


class App:
    def __init__(self):
        self.__root = Tk()
        self.__root.title = 'Анализ состояния печи'

        self.__root.bind_all("<Key>", self._onKeyRelease, "+")

        self.__train_file_name = tkinter.StringVar()
        self.__log_file_name = tkinter.StringVar()
        self.__token = tkinter.StringVar()

        train_file_frame = tkinter.Frame(self.__root)
        train_file_frame.pack(padx=10, pady=10, fill='x', expand=True)

        train_file_label = tkinter.Label(train_file_frame, text="Укажите путь для файла c параметрами обучения:")
        train_file_label.pack(fill='x', expand=True)

        train_file_entry = tkinter.Entry(train_file_frame, width=50, textvariable=self.__train_file_name)
        train_file_entry.pack(fill='x', expand=True, side=tkinter.LEFT)
        train_file_entry.focus()

        train_file_btn = Button(train_file_frame, text="Найти", width=10, command=partial(self.browse_dir, self.__train_file_name))
        train_file_btn.pack(fill='x', expand=True, side=tkinter.LEFT, padx=5)

        log_file_frame = tkinter.Frame(self.__root)
        log_file_frame.pack(padx=10, pady=10, fill='x', expand=True)

        log_file_label = tkinter.Label(log_file_frame, text="Укажите путь для лог файла:")
        log_file_label.pack(fill='x', expand=True)

        log_file_entry = tkinter.Entry(log_file_frame, width=50, textvariable=self.__log_file_name)
        log_file_entry.pack(fill='x', expand=True, side=tkinter.LEFT)

        log_file_btn = Button(log_file_frame, text="Найти", width=10, command=partial(self.browse_dir, self.__log_file_name))
        log_file_btn.pack(fill='x', expand=True, side=tkinter.LEFT, padx=5)

        token_frame = tkinter.Frame(self.__root)
        token_frame.pack(padx=10, pady=10, fill='x', expand=True)

        token_label = Label(token_frame, text="Укажите токен для телеграмм-бота:")
        token_label.pack(fill='x', expand=True, padx=10)

        token_entry = Entry(token_frame, textvariable=self.__token)
        token_entry.pack(fill='x', side=tkinter.LEFT, expand=True)

        btn_frame = tkinter.Frame(self.__root)
        btn_frame.pack(padx=10, pady=10, fill='x', expand=True)

        start_btn = Button(btn_frame, text="Начать", font=32, command=self.start)
        start_btn.pack(anchor=tkinter.CENTER)

        exit_btn = Button(btn_frame, text="Выход", command=exit)
        exit_btn.pack(pady=10, anchor=tkinter.CENTER)

    def _onKeyRelease(self, event):
        ctrl = (event.state & 0x4) != 0
        if event.keycode == 88 and ctrl and event.keysym.lower() != "x":
            event.widget.event_generate("<<Cut>>")

        if event.keycode == 86 and ctrl and event.keysym.lower() != "v":
            event.widget.event_generate("<<Paste>>")

        if event.keycode == 67 and ctrl and event.keysym.lower() != "c":
            event.widget.event_generate("<<Copy>>")

    def start(self):
        try:
            self.manager = Manager(self.__train_file_name.get(), self.__log_file_name.get())
        except Exception as error:
            showerror(
                title='Ошибка',
                message=f'Ошибка при открытии лог файлов:\n{error}'
            )

            return

        try:
            self.bot = Bot(self.__token.get(), self.manager)
            self.bot.run()
            showinfo(
                title='Анализ состояния печи',
                message='Программа запущена'
            )
        except Exception as error:
            showerror(
                title='Ошибка',
                message=f'Ошибка при запуске бота:\n{error}'
            )
            return

        cur_time_ms = 0.0
        while True:
            try:
                new_time_ms = float(list(reversed(open(self.manager.file_temp).readlines()))[0].split('\t')[-1])
                if cur_time_ms != new_time_ms:
                    temp_block = self.manager.read_block(self.manager.file_temp, new_time_ms)
                    curr_block = self.manager.read_block(self.manager.file_curr, new_time_ms)
                    volt_block = self.manager.read_block(self.manager.file_volt, new_time_ms)
                    pres_block = self.manager.read_block(self.manager.file_pres, new_time_ms)
                    cur_time_ms = new_time_ms
                    print(temp_block)
            except Exception as error:
                showerror(
                    title='Ошибка',
                    message=f'Ошибка работы программы:\n{error}'
                )
                continue

    def browse_dir(self, text_var):
        dir_name = filedialog.askdirectory(
            title='Выбрать нужную папку',
            initialdir='/',
            )

        text_var.set(dir_name)
        return dir_name

    def run(self):
        self.__root.mainloop()


app = App()
app.run()

