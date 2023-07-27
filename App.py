import os
import tkinter
from functools import partial

import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import showinfo, showerror
import codecs


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
        cur_dir = os.path.abspath(os.curdir)

        with open(cur_dir + "\Predict_Errors.txt", mode="a+") as file_errors:
            text = file_errors.read()
            if len(text) == 0:
                file_errors.write("ID_Error\tStatus\tTimeString\tT_ust\tParameter\n")

        self.__token = ""
        try:
            with open(cur_dir + "\TOKEN.txt", mode="r") as file_token:
                self.__token = file_token.read()
        except:
            showerror(
                title='Ошибка',
                message='Создайте файл TOKEN.txt в папке приложения'
            )

        if len(self.__token) < 5:
            showerror(
                title='Ошибка',
                message='Запишите токен телеграм-бота в файл TOKEN.txt'
            )

        # self.__token = "6390531140:AAHGej2c3P22aUAonX_y1_wd1BQSxwqE5Qk"
        try:
            self.bot = Bot(self.__token)
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

        self.__train_file = train_file_name
        df_result_train = pd.read_csv(self.__train_file, sep=',')
        self.matrix_mu = []
        self.matrix_sigma = []

        self.fl_first = False
        self.fl_second = False
        self.id_message_w = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.id_message_e = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.period = 0
        self.period_and_fl = ""
        self.last_values = []
        self.mas_zones = []
        self.fl_w = [False, False, False, False, False, False, False, False, False]
        self.fl_e = [False, False, False, False, False, False, False, False, False]

        for i in range(10):
            pie_mu = []
            pie_sigma = []
            for j in range(1, 10):
                pie_mu.append(float(df_result_train.values[i][j][df_result_train.values[i][j].find('[') + 1: df_result_train.values[i][j].find(',')]))
                pie_sigma.append(float(df_result_train.values[i][j][df_result_train.values[i][j].find(' ') + 1: df_result_train.values[i][j].find(']')]))
            self.matrix_mu.append(pie_mu)
            self.matrix_sigma.append(pie_sigma)

        cnt_check = 0
        for root, dirs, files in os.walk(log_file_path):
            if 'Temperature0.txt' in files:
                self.file_temp = os.path.join(root, 'Temperature0.txt').replace(os.sep, '/')
                cnt_check += 1
            elif 'Current0.txt' in files:
                self.file_curr = os.path.join(root, 'Current0.txt').replace(os.sep, '/')
                cnt_check += 1
            elif 'Voltage0.txt' in files:
                self.file_volt = os.path.join(root, 'Voltage0.txt').replace(os.sep, '/')
                cnt_check += 1
            elif 'Pressure0.txt' in files:
                self.file_pres = os.path.join(root, 'Pressure0.txt').replace(os.sep, '/')
                cnt_check += 1
        if cnt_check == 4:
            print("Необходимые файлы найдены: Temperature0.txt, Current0.txt, Voltage0.txt, Pressure0.txt\n")
        else:
            print("ERROR: не все файлы были найдены")
            input()
            exit()

    def read_block(self, file_name, time_ms):
        file = codecs.open(file_name, 'r', "utf-8")
        file_lines = list(reversed(file.readlines()))

        block = []
        i = 0
        while float(file_lines[i].split('\t')[-1]) == time_ms:
            block.append(file_lines[i])
            i += 1

        file.close()
        return list(reversed(block))

    def block_analysis(self, temp, curr, volt, pres):
        temp_values = []
        date = temp[0].split('\t')[1]

        for i in range(len(temp)):
            if (i < 4) or (i > 6):
                temp_values.append(float(temp[i].split('\t')[2]))

        curr_values = []
        for i in range(len(curr)):
            curr_values.append(float(curr[i].split('\t')[2]))

        volt_values = []
        for i in range(len(volt)):
            volt_values.append(float(volt[i].split('\t')[2]))

        power_values = np.array(curr_values) * np.array(volt_values)

        pres_values = []
        for i in range(len(pres)):
            pres_values.append(float(pres[i].split('\t')[2]))

        cur_dir = os.path.abspath(os.curdir)

        if temp_values[-1] > 0:
            self.period_and_fl = "1 True"
            try:
                with open(cur_dir + "\Period.txt", mode="r") as file_period:
                    file_period.seek(0)
                    text = file_period.read()
                    if len(text) > 2:
                        self.period_and_fl = text
                        if self.period_and_fl.split(' ')[1] == "False":
                            self.period_and_fl = str(int(self.period_and_fl.split(' ')[0]) + 1) + " " + "True"
            except FileNotFoundError:
                print("Файл Period.txt не найден.\nФайл создан.")

            with open(cur_dir + "\Period.txt", mode="w") as file_period:
                file_period.write(self.period_and_fl)
        else:
            self.period_and_fl = ""
            try:
                with open(cur_dir + "\Period.txt", mode="r") as file_period:
                    file_period.seek(0)
                    text = file_period.read()
                    if len(text) > 1:
                        self.period_and_fl = text
            except FileNotFoundError:
                print("Файл Period.txt не найден.\nФайл создан.")

            with open(cur_dir + "\Period.txt", mode="w") as file_period:
                if len(self.period_and_fl) > 1:
                    if self.period_and_fl.split(' ')[1] == "True":
                        file_period.write(str(self.period_and_fl.split(' ')[0]) + " " + "False")
                    else:
                        file_period.write(self.period_and_fl)

        if self.fl_first:
            self.last_values.append([temp_values, power_values, pres_values])
            power_values_filter_p1 = []
            power_values_filter_p2 = []
            power_values_filter_p3 = []
            power_values_filter_pr = []

            for i in range(len(self.last_values)):
                power_values_filter_p1.append(self.last_values[i][1][0])
                power_values_filter_p2.append(self.last_values[i][1][1])
                power_values_filter_p3.append(self.last_values[i][1][2])

                power_values_filter_pr.append(self.last_values[i][2][3])

            for i in range(10):
                power_values_filter_p1 = savgol_filter(power_values_filter_p1, 7, 1)
                power_values_filter_p2 = savgol_filter(power_values_filter_p2, 7, 1)
                power_values_filter_p3 = savgol_filter(power_values_filter_p3, 7, 1)
                power_values_filter_pr = savgol_filter(power_values_filter_pr, 7, 1)

            ras_p1 = power_values_filter_p1[-1] - power_values_filter_p1[-2]
            ras_p2 = power_values_filter_p2[-1] - power_values_filter_p2[-2]
            ras_p3 = power_values_filter_p3[-1] - power_values_filter_p3[-2]
            ras_pr = power_values_filter_pr[-1] - power_values_filter_pr[-2]

            mas_ras = [ras_p1, ras_p2, ras_p3, ras_pr]

            temp_ust = self.last_values[-1][0][-1]
            for item in range(len(mas_ras)):

                t_pair = ""
                if item == 0:
                    t_pair = "P1"
                elif item == 1:
                    t_pair = "P2"
                elif item == 2:
                    t_pair = "P3"
                elif item == 3:
                    t_pair = "PS4"

                for zone in range(0, 1800, 200):
                    if zone <= temp_ust < zone + 200:
                        mu = self.matrix_mu[int(zone / 200)][item + 5]
                        sigma = self.matrix_sigma[int(zone / 200)][item + 5]
                        if mu - sigma * 2 <= mas_ras[item] <= mu + sigma * 2:
                            if mu - sigma <= mas_ras[item] <= mu + sigma:  # GREEN ZONE
                                if self.fl_w[item + 5]:
                                    with open(cur_dir + "\Period.txt", mode="r") as file_period:
                                        self.period = file_period.read().split(' ')[0]
                                    if t_pair != "PS4":
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"✅ <b>Warning canceled</b>: Мощность по датчику №{item + 1}\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Мощность:    {self.last_values[-1][1][item]}",
                                                                       parse_mode='HTML')
                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\t"
                                                              f"0\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][1][item]}\n")

                                        print(f"{date}   Предупреждение снято:  Мощность по датчику №{item + 1}")
                                        self.fl_w[item + 5] = False

                                    else:
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"✅ <b>Warning canceled</b>: Давление\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Давление:    {self.last_values[-1][2][3]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\t"
                                                              f"0\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][2][3]}\n")

                                        print(f"{date}   Предупреждение снято:  Давление")
                                        self.fl_w[item + 5] = False

                                if self.fl_e[item + 5]:
                                    with open(cur_dir + "\Period.txt", mode="r") as file_period:
                                        self.period = file_period.read().split(' ')[0]
                                    if t_pair != "PS4":
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"✅ <b>Error canceled</b>: Мощность по датчику №{item + 1}\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Мощность:    {self.last_values[-1][1][item]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\t"
                                                              f"0\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][1][item]}\n")

                                        print(f"{date}   Опасность снята:       Мощность по датчику №{item + 1}")
                                        self.fl_e[item + 5] = False

                                    else:
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"✅ <b>Error canceled</b>: Давление\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Давление:    {self.last_values[-1][2][3]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\t"
                                                              f"0\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][2][3]}\n")

                                        print(f"{date}   Опасность снята:       Давление")
                                        self.fl_e[item + 5] = False
                            else:
                                if not self.fl_w[item + 5]:
                                    self.id_message_w[item + 5] += 1
                                    with open(cur_dir + "\Period.txt", mode="r") as file_period:
                                        self.period = file_period.read().split(' ')[0]
                                    if t_pair != "PS4":
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"⚠ <b>Warning</b>: Мощность по датчику №{item + 1}\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Мощность:    {self.last_values[-1][1][item]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\t"
                                                              f"1\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][1][item]}\n")

                                        print(f"{date}   Предупреждение:        Мощность по датчику №{item + 1}")
                                        self.fl_w[item + 5] = True

                                    else:
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"⚠ <b>Warning</b>: Давление\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Давление:    {self.last_values[-1][2][3]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\t"
                                                              f"1\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][2][3]}\n")

                                        print(f"{date}   Предупреждение:        Давление")
                                        self.fl_w[item + 5] = True

                        else:
                            if not self.fl_e[item + 5]:
                                self.id_message_e[item + 5] += 1
                                with open(cur_dir + "\Period.txt", mode="r") as file_period:
                                    self.period = file_period.read().split(' ')[0]
                                if t_pair != "PS4":
                                    for client in self.bot.array_id:
                                        client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                   text=f"#E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\n"
                                                                        f"{date}\n"
                                                                        f"❗ <b>Error</b>: Мощность по датчику №{item + 1}\n"
                                                                        f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                        f"Мощность:    {self.last_values[-1][1][item]}",
                                                                   parse_mode='HTML')

                                    with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                        file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\t"
                                                          f"1\t"
                                                          f"{date}\t"
                                                          f"{self.last_values[-1][0][-1]}\t"
                                                          f"{self.last_values[-1][1][item]}\n")

                                    print(f"{date}   Опасность:             Мощность по датчику №{item + 1}")
                                    self.fl_e[item + 5] = True

                                else:
                                    for client in self.bot.array_id:
                                        client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                   text=f"#E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\n"
                                                                        f"{date}\n"
                                                                        f"❗ <b>Error</b>: Давление\n"
                                                                        f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                        f"Давление:    {self.last_values[-1][2][3]}",
                                                                   parse_mode='HTML')

                                    with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                        file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\t"
                                                          f"1\t"
                                                          f"{date}\t"
                                                          f"{self.last_values[-1][0][-1]}\t"
                                                          f"{self.last_values[-1][2][3]}\n")

                                    print(f"{date}   Опасность:             Давление")
                                    self.fl_e[item + 5] = True

                    if 1800 <= temp_ust:
                        mu = self.matrix_mu[-1][item + 5]
                        sigma = self.matrix_sigma[-1][item + 5]
                        if mu - sigma * 2 <= mas_ras[item] <= mu + sigma * 2:
                            if mu - sigma <= mas_ras[item] <= mu + sigma:  # GREEN ZONE
                                if self.fl_w[item + 5]:
                                    with open(cur_dir + "\Period.txt", mode="r") as file_period:
                                        self.period = file_period.read().split(' ')[0]
                                    if t_pair != "PS4":
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"✅ <b>Warning canceled</b>: Мощность по датчику №{item + 1}\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Мощность:    {self.last_values[-1][1][item]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\t"
                                                              f"0\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][1][item]}\n")

                                        print(f"{date}   Предупреждение снято:  Мощность по датчику №{item + 1}")
                                        self.fl_w[item + 5] = False

                                    else:
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"✅ <b>Warning canceled</b>: Давление\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Давление:    {self.last_values[-1][2][3]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\t"
                                                              f"0\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][2][3]}\n")

                                        print(f"{date}   Предупреждение снято:  Давление")
                                        self.fl_w[item + 5] = False

                                if self.fl_e[item + 5]:
                                    with open(cur_dir + "\Period.txt", mode="r") as file_period:
                                        self.period = file_period.read().split(' ')[0]
                                    if t_pair != "PS4":
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"✅ <b>Error canceled</b>: Мощность по датчику №{item + 1}\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Мощность:    {self.last_values[-1][1][item]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\t"
                                                              f"0\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][1][item]}\n")

                                        print(f"{date}   Опасность снята:       Мощность по датчику №{item + 1}")
                                        self.fl_e[item + 5] = False

                                    else:
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"✅ <b>Error canceled</b>: Давление\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Давление:    {self.last_values[-1][2][3]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\t"
                                                              f"0\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][2][3]}\n")

                                        print(f"{date}   Опасность снята:       Давление")
                                        self.fl_e[item + 5] = False
                            else:
                                if not self.fl_w[item + 5]:
                                    self.id_message_w[item + 5] += 1
                                    with open(cur_dir + "\Period.txt", mode="r") as file_period:
                                        self.period = file_period.read().split(' ')[0]
                                    if t_pair != "PS4":
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"⚠ <b>Warning</b>: Мощность по датчику №{item + 1}\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Мощность:    {self.last_values[-1][1][item]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\t"
                                                              f"1\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][1][item]}\n")

                                        print(f"{date}   Предупреждение:        Мощность по датчику №{item + 1}")
                                        self.fl_w[item + 5] = True

                                    else:
                                        for client in self.bot.array_id:
                                            client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                       text=f"#W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\n"
                                                                            f"{date}\n"
                                                                            f"⚠ <b>Warning</b>: Давление\n"
                                                                            f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                            f"Давление:    {self.last_values[-1][2][3]}",
                                                                       parse_mode='HTML')

                                        with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                            file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[item + 5]}\t"
                                                              f"1\t"
                                                              f"{date}\t"
                                                              f"{self.last_values[-1][0][-1]}\t"
                                                              f"{self.last_values[-1][2][3]}\n")

                                        print(f"{date}   Предупреждение:        Давление")
                                        self.fl_w[item + 5] = True

                        else:
                            if not self.fl_e[item + 5]:
                                self.id_message_e[item + 5] += 1
                                with open(cur_dir + "\Period.txt", mode="r") as file_period:
                                    self.period = file_period.read().split(' ')[0]
                                if t_pair != "PS4":
                                    for client in self.bot.array_id:
                                        client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                   text=f"#E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\n"
                                                                        f"{date}\n"
                                                                        f"❗ <b>Error</b>: Мощность по датчику №{item + 1}\n"
                                                                        f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                        f"Мощность:    {self.last_values[-1][1][item]}",
                                                                   parse_mode='HTML')

                                    with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                        file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\t"
                                                          f"1\t"
                                                          f"{date}\t"
                                                          f"{self.last_values[-1][0][-1]}\t"
                                                          f"{self.last_values[-1][1][item]}\n")

                                    print(f"{date}   Опасность:             Мощность по датчику №{item + 1}")
                                    self.fl_e[item + 5] = True

                                else:
                                    for client in self.bot.array_id:
                                        client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                                   text=f"#E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\n"
                                                                        f"{date}\n"
                                                                        f"❗ <b>Error</b>: Давление\n"
                                                                        f"T℃ уставки: {self.last_values[-1][0][-1]}\n"
                                                                        f"Давление:    {self.last_values[-1][2][3]}",
                                                                   parse_mode='HTML')

                                    with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                        file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[item + 5]}\t"
                                                          f"1\t"
                                                          f"{date}\t"
                                                          f"{self.last_values[-1][0][-1]}\t"
                                                          f"{self.last_values[-1][2][3]}\n")

                                    print(f"{date}   Опасность:             Давление")
                                    self.fl_e[item + 5] = True



            if self.fl_second:
                del self.mas_zones[0]
                tmp_zones = []
                for j in range(5):  # 5 scanners
                    ras = self.last_values[-1][0][j] - self.last_values[-2][0][j]

                    for zone in range(0, 1800, 200):
                        if zone <= temp_ust < zone + 200:
                            mu = self.matrix_mu[int(zone / 200)][j]
                            sigma = self.matrix_sigma[int(zone / 200)][j]
                            if mu - sigma * 2 <= ras <= mu + sigma * 2:
                                if mu - sigma <= ras <= mu + sigma:
                                    tmp_zones.append(0)
                                else:
                                    tmp_zones.append(1)
                            else:
                                tmp_zones.append(2)

                        if 1800 <= temp_ust:
                            mu = self.matrix_mu[-1][j]
                            sigma = self.matrix_sigma[-1][j]
                            if mu - sigma * 2 <= ras <= mu + sigma * 2:
                                if mu - sigma <= ras <= mu + sigma:
                                    tmp_zones.append(0)
                                else:
                                    tmp_zones.append(1)
                            else:
                                tmp_zones.append(2)

                self.mas_zones.append(tmp_zones)

                sm = np.sum(np.array(self.mas_zones), axis=0)
                for i in range(len(sm)):
                    t_pair = ""
                    if i == 0:
                        t_pair = "TI1"
                    elif i == 1:
                        t_pair = "TI21"
                    elif i == 2:
                        t_pair = "TI22"
                    elif i == 3:
                        t_pair = "TI3"
                    elif i == 4:
                        t_pair = "TE"

                    if 5 < sm[i] <= 10:
                        if not self.fl_w[i]:
                            self.id_message_w[i] += 1
                            with open(cur_dir + "\Period.txt", mode="r") as file_period:
                                self.period = file_period.read().split(' ')[0]
                            for client in self.bot.array_id:
                                client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                           text=f"#W_{t_pair}_{self.period}_{self.id_message_w[i]}\n"
                                                                f"{date}\n"
                                                                f"⚠ <b>Warning</b>: термопара №{i + 1}\n"
                                                                f"T℃ уставки:   {self.last_values[-1][0][-1]}\n"
                                                                f"T℃ термопары: {self.last_values[-1][0][i]}",
                                                       parse_mode='HTML')

                            with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[i]}\t"
                                                  f"1\t"
                                                  f"{date}\t"
                                                  f"{self.last_values[-1][0][-1]}\t"
                                                  f"{self.last_values[-1][0][i]}\n")

                            print(f"{date}   Предупреждение:        термопара №{i + 1}")
                            self.fl_w[i] = True
                    elif 11 <= sm[i]:
                        if not self.fl_e[i]:
                            self.id_message_e[i] += 1
                            for client in self.bot.array_id:
                                client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                           text=f"#E_{t_pair}_{self.period}_{self.id_message_e[i]}\n"
                                                                f"{date}\n"
                                                                f"❗ <b>Error</b>: термопара №{i + 1}\n"
                                                                f"T℃ уставки:   {self.last_values[-1][0][-1]}\n"
                                                                f"T℃ термопары: {self.last_values[-1][0][i]}",
                                                       parse_mode='HTML')

                            with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[i]}\t"
                                                  f"1\t"
                                                  f"{date}\t"
                                                  f"{self.last_values[-1][0][-1]}\t"
                                                  f"{self.last_values[-1][0][i]}\n")

                            print(f"{date}   Опасность:             Термопара №{i + 1}")
                            self.fl_e[i] = True
                    else:
                        if self.fl_w[i]:
                            for client in self.bot.array_id:
                                client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                           text=f"#W_{t_pair}_{self.period}_{self.id_message_w[i]}\n"
                                                                f"{date}\n"
                                                                f"✅ <b>Warning canceled</b>: термопара №{i + 1}\n"
                                                                f"T℃ уставки:   {self.last_values[-1][0][-1]}\n"
                                                                f"T℃ термопары: {self.last_values[-1][0][i]}\n",
                                                       parse_mode='HTML')

                            with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                file_errors.write(f"W_{t_pair}_{self.period}_{self.id_message_w[i]}\t"
                                                  f"0\t"
                                                  f"{date}\t"
                                                  f"{self.last_values[-1][0][-1]}\t"
                                                  f"{self.last_values[-1][0][i]}\n")

                            print(f"{date}   Предупреждение снято:  Термопара №{i + 1}")
                            self.fl_w[i] = False
                        if self.fl_e[i]:
                            for client in self.bot.array_id:
                                client[1].bot.send_message(chat_id=client[0].effective_chat.id,
                                                           text=f"#E_{t_pair}_{self.period}_{self.id_message_e[i]}\n"
                                                                f"{date}\n"
                                                                f"✅ <b>Error</b>: термопара №{i + 1}\n"
                                                                f"T℃ уставки:   {self.last_values[-1][0][-1]}\n"
                                                                f"T℃ термопары: {self.last_values[-1][0][i]}",
                                                       parse_mode='HTML')

                            with open(cur_dir + "\Predict_Errors.txt", mode="a") as file_errors:
                                file_errors.write(f"E_{t_pair}_{self.period}_{self.id_message_e[i]}\t"
                                                  f"0\t"
                                                  f"{date}\t"
                                                  f"{self.last_values[-1][0][-1]}\t"
                                                  f"{self.last_values[-1][0][i]}\n")

                            print(f"{date}   Опасность снята:       Термопара №{i + 1}")
                            self.fl_e[i] = False

                # |0|0|0|0|0|0| => 0 (sm <= 5)
                # |1|1|1|1|1|0| => 1 (6 <= sm <= 10)
                # |1|1|1|1|1|1| => 1
                # |2|2|2|2|1|1| => 1
                # |2|2|2|2|2|1| => 2 (11 <= sm)
                # |2|2|2|2|2|2| => 2

                # #W_TI1_16_5
                # 2023-06-13 11:16:30
                # ⚠️ Warning: термопара №1
                # T℃ уставки: 208.0415
                # T℃ термопары: 215.9262

                # #E_TI21_16_2
                # 2023-06-13 11:15:15
                # ❗️ Error: термопара №2
                # T℃ уставки: 200.5411
                # T℃ термопары: 216.9153

            else:
                for i in range(6):  # 6 * 5 = 30 sec
                    tmp_zones = []
                    temp_ust = self.last_values[i][0][-1]
                    for j in range(5):  # 5 scanners
                        ras = self.last_values[i + 1][0][j] - self.last_values[i][0][j]

                        for zone in range(0, 1800, 200):
                            if zone <= temp_ust < zone + 200:
                                mu = self.matrix_mu[int(zone / 200)][j]
                                sigma = self.matrix_sigma[int(zone / 200)][j]
                                if mu - sigma * 2 <= ras <= mu + sigma * 2:
                                    if mu - sigma <= ras <= mu + sigma:
                                        tmp_zones.append(0)
                                    else:
                                        tmp_zones.append(1)
                                else:
                                    tmp_zones.append(2)

                            if 1800 <= temp_ust:
                                mu = self.matrix_mu[-1][j]
                                sigma = self.matrix_sigma[-1][j]
                                if mu - sigma * 2 <= ras <= mu + sigma * 2:
                                    if mu - sigma <= ras <= mu + sigma:
                                        tmp_zones.append(0)
                                    else:
                                        tmp_zones.append(1)
                                else:
                                    tmp_zones.append(2)

                    self.mas_zones.append(tmp_zones)

                self.fl_second = True

            del self.last_values[0]

        else:
            self.last_values.append([temp_values, power_values, pres_values])
            if len(self.last_values) == 6:
                self.fl_first = True


class Bot:
    def __init__(self, TOKEN):
        self.bot = telegram.Bot(token=TOKEN)
        self.updater = Updater(token=TOKEN, use_context=True)
        self.__dispatcher = self.updater.dispatcher

        self.array_id = []
        self.flag = False
        self.__start_markup = telegram.ReplyKeyboardMarkup.from_button(
            telegram.KeyboardButton(
                text='Старт'
            )
        )
        self.__start_markup.resize_keyboard = True

    def get_text_messages(self, update, context):
        if update.message.text == 'Старт':
            # if [update, context] not in self.array_id:
            if not self.flag:
                self.array_id.append([update, context])
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Приложение запущено!',
                                         reply_markup=self.__start_markup)
                self.flag = True

    def start(self, update, context):
        # if [update, context] not in self.array_id:
        if not self.flag:
            self.array_id.append([update, context])
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='<b>Добро пожаловать в сервис для мониторинга состояния печи.</b>\n\n'
                                          'Бот будет предупреждать о возможных авариях.',
                                     parse_mode='HTML',
                                     reply_markup=self.__start_markup)
            self.flag = True

    def handler(self):
        self.__dispatcher.add_handler(CommandHandler('start', self.start))
        self.__dispatcher.add_handler(MessageHandler(Filters.text, self.get_text_messages))

    def run(self):
        self.handler()
        self.updater.start_polling()


class App:
    def __init__(self):
        self.__root = Tk()
        self.__root.title('Анализ состояния печи')

        self.__root.bind_all("<Key>", self._onKeyRelease, "+")

        # self.__train_file_name = r"C:\Users\user\PycharmProjects\Ostec\venv\Result_Train.csv"
        # self.__log_file_name = r"C:\Users\user\Desktop\Ostec\log\generate_logs_2"

        self.__log_file_name = tkinter.StringVar()
        self.__train_file_name = tkinter.StringVar()

        train_file_frame = tkinter.Frame(self.__root)
        train_file_frame.pack(padx=10, pady=10, fill='x', expand=True)

        train_file_label = tkinter.Label(train_file_frame, text="Путь файла с параметрами обучения (Result_Train.csv):")
        train_file_label.pack(fill='x', expand=True)

        train_file_entry = tkinter.Entry(train_file_frame, width=60, textvariable=self.__train_file_name)
        train_file_entry.pack(fill='x', expand=True, side=tkinter.LEFT)
        train_file_entry.focus()

        train_file_btn = Button(train_file_frame, text="Найти", width=10,
                                command=partial(self.browse_dir, self.__train_file_name))
        train_file_btn.pack(padx=5, fill='x', expand=True, side=tkinter.LEFT)

        log_file_frame = tkinter.Frame(self.__root)
        log_file_frame.pack(padx=10, pady=10, fill='x', expand=True)

        log_file_label = tkinter.Label(log_file_frame, text="Путь папки с Лог-Файлами:")
        log_file_label.pack(fill='x', expand=True)

        log_file_entry = tkinter.Entry(log_file_frame, width=60, textvariable=self.__log_file_name)
        log_file_entry.pack(fill='x', expand=True, side=tkinter.LEFT)

        log_file_btn = Button(log_file_frame, text="Найти", width=10,
                              command=partial(self.browse_dir, self.__log_file_name))
        log_file_btn.pack(padx=5, fill='x', expand=True, side=tkinter.LEFT)

        btn_frame = tkinter.Frame(self.__root)
        btn_frame.pack(padx=5, pady=10, fill='x', expand=True)

        exit_btn = Button(btn_frame, text="Выход", font=16, command=exit)
        exit_btn.pack(padx=10, side=tkinter.RIGHT)

        start_btn = Button(btn_frame, text="Начать", font=16, command=self.start)
        start_btn.pack(side=tkinter.RIGHT)


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
                message=f'Ошибка при открытии лог-файлов:\n{error}'
            )

            return

        self.__root.withdraw()
        cur_time_ms = 0.0
        while True:
            try:
                file = codecs.open(self.manager.file_volt, 'r', "utf-8")
                new_time_ms = float(list(reversed(file.readlines()))[0].split('\t')[-1])
                file.close()
                if cur_time_ms != new_time_ms:
                    temp_block = self.manager.read_block(self.manager.file_temp, new_time_ms)
                    curr_block = self.manager.read_block(self.manager.file_curr, new_time_ms)
                    volt_block = self.manager.read_block(self.manager.file_volt, new_time_ms)
                    pres_block = self.manager.read_block(self.manager.file_pres, new_time_ms)
                    self.manager.block_analysis(temp_block, curr_block, volt_block, pres_block)
                    cur_time_ms = new_time_ms
            except Exception as error:
                showerror(
                    title='Ошибка',
                    message=f'Ошибка работы программы:\n{error}'
                )
                break


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
