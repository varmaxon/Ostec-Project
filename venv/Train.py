import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.signal import savgol_filter
from statistics import fmean, stdev
from tqdm import tqdm


class LogFiles(object):
    def __init__(self, path):
        cnt_check = 0
        try:
            for root, dirs, files in os.walk(path):
                if 'Temperature0.txt' in files:
                    self.__file_temp = os.path.join(root, 'Temperature0.txt')
                    cnt_check += 1
                elif 'Current0.txt' in files:
                    self.__file_curr = os.path.join(root, 'Current0.txt')
                    cnt_check += 1
                elif 'Voltage0.txt' in files:
                    self.__file_volt = os.path.join(root, 'Voltage0.txt')
                    cnt_check += 1
                elif 'Pressure0.txt' in files:
                    self.__file_pres = os.path.join(root, 'Pressure0.txt')
                    cnt_check += 1
        except:
            print("ERROR: ошибка при инициализации объекта LofFiles")
            input()
            exit()

        if cnt_check == 4:
            print("Необходимые файлы найдены: Temperature0.txt, Current0.txt, Voltage0.txt, Pressure0.txt")
        else:
            print("ERROR: не все файлы были найдены")
            input()
            exit()

    def get_file_temp(self):
        return self.__file_temp

    def get_file_curr(self):
        return self.__file_curr

    def get_file_volt(self):
        return self.__file_volt

    def get_file_pres(self):
        return self.__file_pres


class DFrame(object):
    def __init__(self, temp, curr, volt, pres):
        self.__df_temp = pd.read_csv(temp, sep='\t', encoding='utf-16')
        self.__df_curr = pd.read_csv(curr, sep='\t', encoding='utf-16')
        self.__df_volt = pd.read_csv(volt, sep='\t', encoding='utf-16')
        self.__df_pres = pd.read_csv(pres, sep='\t', encoding='utf-16')

        self.__crossing()

    def __crossing(self):
        df_I_2 = self.__df_curr.loc[self.__df_curr['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real panel_al{5}']
        df_I_1 = self.__df_curr.loc[self.__df_curr['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real panel_al{4}']
        df_I_3 = self.__df_curr.loc[self.__df_curr['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real panel_al{6}']

        df_U_1 = self.__df_volt.loc[self.__df_volt['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real panel_al{1}']
        df_U_2 = self.__df_volt.loc[self.__df_volt['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real panel_al{2}']
        df_U_3 = self.__df_volt.loc[self.__df_volt['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real panel_al{3}']

        df_Pr = self.__df_pres.loc[self.__df_pres['VarName'] == 'DB3_Analog Input_Analog input panel{6}']

        self.df_T_u = self.__df_temp.loc[self.__df_temp['VarName'] == 'DB16_Heat work_Set value temperature']
        df_T_1 = self.__df_temp.loc[self.__df_temp['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real pan_ow{1}']
        df_T_2 = self.__df_temp.loc[self.__df_temp['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real pan_ow{2}']
        df_T_3 = self.__df_temp.loc[self.__df_temp['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real pan_ow{3}']
        df_T_4 = self.__df_temp.loc[self.__df_temp['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real pan_ow{4}']
        df_T_8 = self.__df_temp.loc[self.__df_temp['VarName'] == 'DB21_RS485_Omix_Ow_Mera_RRG_Data_real pan_ow{8}']

        crossing_IU_1 = pd.merge(df_I_1, df_U_1, how='inner', on=['Time_ms']).drop(
            columns=['TimeString_y', 'VarName_x', 'VarName_y', 'Validity_x', 'Validity_y']).rename(
            columns={"VarValue_x": "I", "VarValue_y": "U"})
        crossing_IU_2 = pd.merge(df_I_2, df_U_2, how='inner', on=['Time_ms']).drop(
            columns=['TimeString_y', 'VarName_x', 'VarName_y', 'Validity_x', 'Validity_y']).rename(
            columns={"VarValue_x": "I", "VarValue_y": "U"})
        crossing_IU_3 = pd.merge(df_I_3, df_U_3, how='inner', on=['Time_ms']).drop(
            columns=['TimeString_y', 'VarName_x', 'VarName_y', 'Validity_x', 'Validity_y']).rename(
            columns={"VarValue_x": "I", "VarValue_y": "U"})

        I_index = -1
        U_index = -1
        Time_ms_index = -1
        for i in range(len(crossing_IU_1.columns)):
            if crossing_IU_1.columns[i] == 'I':
                I_index = i
            elif crossing_IU_1.columns[i] == 'U':
                U_index = i
            elif crossing_IU_1.columns[i] == 'Time_ms':
                Time_ms_index = i
        if (I_index < 0) or (U_index < 0) or (Time_ms_index < 0):
            print("ERROR: index of column < 0")
            input()
            exit()


        cross_time = pd.merge(crossing_IU_1, self.df_T_u, how='inner', on=['Time_ms']).drop(columns=['TimeString_x'])
        cross_time = pd.merge(cross_time, df_Pr, how='inner', on=['Time_ms']).drop(columns=['VarName_x', 'TimeString_x',
                                                                                            'VarValue_x', 'Validity_x',
                                                                                            'VarName_y', 'TimeString_y',
                                                                                            'VarValue_y', 'Validity_y'])

        crossing_IU_1['P'] = crossing_IU_1.I * crossing_IU_1.U
        crossing_IU_2['P'] = crossing_IU_2.I * crossing_IU_2.U
        crossing_IU_3['P'] = crossing_IU_3.I * crossing_IU_3.U

        crossing_IU_1 = pd.merge(crossing_IU_1, cross_time,  how='inner', on=['Time_ms']).drop(columns=['TimeString_x', 'I_x', 'U_x', 'I_y', 'U_y'])
        crossing_IU_2 = pd.merge(crossing_IU_2, cross_time,  how='inner', on=['Time_ms']).drop(columns=['TimeString_x', 'I_x', 'U_x', 'I_y', 'U_y'])
        crossing_IU_3 = pd.merge(crossing_IU_3, cross_time,  how='inner', on=['Time_ms']).drop(columns=['TimeString_x', 'I_x', 'U_x', 'I_y', 'U_y'])

        self.df_P1_T1 = pd.merge(crossing_IU_1, df_T_1, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P1_T2 = pd.merge(crossing_IU_1, df_T_2, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P1_T3 = pd.merge(crossing_IU_1, df_T_3, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P1_T4 = pd.merge(crossing_IU_1, df_T_4, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P1_T8 = pd.merge(crossing_IU_1, df_T_8, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})

        self.df_P2_T1 = pd.merge(crossing_IU_2, df_T_1, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P2_T2 = pd.merge(crossing_IU_2, df_T_2, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P2_T3 = pd.merge(crossing_IU_2, df_T_3, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P2_T4 = pd.merge(crossing_IU_2, df_T_4, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P2_T8 = pd.merge(crossing_IU_2, df_T_8, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})

        self.df_P3_T1 = pd.merge(crossing_IU_3, df_T_1, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P3_T2 = pd.merge(crossing_IU_3, df_T_2, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P3_T3 = pd.merge(crossing_IU_3, df_T_3, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P3_T4 = pd.merge(crossing_IU_3, df_T_4, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})
        self.df_P3_T8 = pd.merge(crossing_IU_3, df_T_8, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "T"})

        if len(set([len(self.df_P1_T1), len(self.df_P1_T2), len(self.df_P1_T3), len(self.df_P1_T4), len(self.df_P1_T8),
                    len(self.df_P2_T1), len(self.df_P2_T2), len(self.df_P2_T3), len(self.df_P2_T4), len(self.df_P2_T8),
                    len(self.df_P3_T1), len(self.df_P3_T2), len(self.df_P3_T3), len(self.df_P3_T4), len(self.df_P3_T8)])) != 1:
            print("ERROR: the lengths of 'Pi_Ti' don't match")
            input()
            exit()

        self.df_P1_Pr = pd.merge(crossing_IU_1, df_Pr, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "Pressure"})
        self.df_P2_Pr = pd.merge(crossing_IU_2, df_Pr, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "Pressure"})
        self.df_P3_Pr = pd.merge(crossing_IU_3, df_Pr, how='inner', on=['Time_ms']).drop(columns=['Validity', 'TimeString', 'VarName']).rename(columns={"VarValue": "Pressure"})

        if len(set([len(self.df_P1_Pr), len(self.df_P2_Pr), len(self.df_P3_Pr)])) != 1:
            print("ERROR: the lengths of 'Pi_Pr' don't match")
            input()
            exit()

        dif = len(self.df_P1_Pr) - len(self.df_P1_T1)
        if dif > 0:
            if self.df_P1_Pr.values[0][0] != self.df_P1_T1.values[0][0]:
                self.df_P1_Pr = self.df_P1_Pr[dif:]
            else:
                self.df_P1_Pr = self.df_P1_Pr[:0 - dif]
        elif dif < 0:
            if self.df_P1_Pr.values[0][0] != self.df_P1_T1.values[0][0]:
                self.df_P1_T1 = self.df_P1_T1[dif:]
            else:
                self.df_P1_T1 = self.df_P1_T1[:0 - dif]

        # print(self.df_P1_Pr)
        # print(self.df_P1_T1)

        if len(self.df_P1_Pr) != len(self.df_P1_T1):
            print("ERROR: the lengths of 'P1_Pr & P1_T1' don't match")
            input()
            exit()

        print("ДатаФреймы сформированы")


class Calculations(DFrame):
    def __init__(self, obj):
        super().__init__(obj.get_file_temp(), obj.get_file_curr(), obj.get_file_volt(), obj.get_file_pres())
        self.find_periods()

    def find_periods(self):
        self.df_periods = pd.DataFrame()

        periods = []
        periods_k = []
        length_time = []
        temp_max = []
        c = []
        d = []
        fl = False
        k = 0
        length_points = 1
        t_max = 0
        for i in self.df_T_u.values:
            if fl:
                length_points += 1
                if i[2] > t_max:
                    t_max = i[2]

            if (i[2] > 0) and (not fl):
                fl = True
                d.append(i[-1])
                c.append(k)

            elif fl and (i[2] == 0):
                fl = False
                d.append(i[-1])
                c.append(k)
                periods_k.append(c)
                periods.append(d)
                d = []
                c = []
                length_time.append(length_points)
                length_points = 1
                temp_max.append(t_max)
                t_max = 0

            k += 1

        for i in range(len(length_time)):
            length_time[i] = length_time[i] * 5
            length_time[i] = round(length_time[i] / 60, 2)

        self.df_periods['Период (№)'] = range(1, len(periods) + 1)
        self.df_periods['Длительность (мин)'] = length_time
        self.df_periods['Tmax (℃)'] = temp_max
        self.df_periods['Границы (мс)'] = periods
        self.df_periods['Служ.инф.'] = periods_k
        print("\nИнформация о включениях:")
        print(self.df_periods.to_string())

    def find_sigma(self):
        self.result_pieces = self.__complete_pieces()
        self.__spline()
        result_derivate = self.__calc_derivate()


        temp_1_mu_sigma = []
        temp_2_mu_sigma = []
        temp_3_mu_sigma = []
        temp_4_mu_sigma = []
        temp_8_mu_sigma = []
        power_1_mu_sigma = []
        power_2_mu_sigma = []
        power_3_mu_sigma = []
        pressure_mu_sigma = []

        for i in range(len(result_derivate[0])):
            if len(result_derivate[0][i]) > 0:
                temp_1_mu_sigma.append([fmean(result_derivate[0][i]), stdev(result_derivate[0][i])])
                temp_2_mu_sigma.append([fmean(result_derivate[1][i]), stdev(result_derivate[1][i])])
                temp_3_mu_sigma.append([fmean(result_derivate[2][i]), stdev(result_derivate[2][i])])
                temp_4_mu_sigma.append([fmean(result_derivate[3][i]), stdev(result_derivate[3][i])])
                temp_8_mu_sigma.append([fmean(result_derivate[4][i]), stdev(result_derivate[4][i])])
                power_1_mu_sigma.append([fmean(result_derivate[5][i]), stdev(result_derivate[5][i])])
                power_2_mu_sigma.append([fmean(result_derivate[6][i]), stdev(result_derivate[6][i])])
                power_3_mu_sigma.append([fmean(result_derivate[7][i]), stdev(result_derivate[7][i])])
                pressure_mu_sigma.append([fmean(result_derivate[8][i]), stdev(result_derivate[8][i])])
            else:
                temp_1_mu_sigma.append([0, 0])
                temp_2_mu_sigma.append([0, 0])
                temp_3_mu_sigma.append([0, 0])
                temp_4_mu_sigma.append([0, 0])
                temp_8_mu_sigma.append([0, 0])
                power_1_mu_sigma.append([0, 0])
                power_2_mu_sigma.append([0, 0])
                power_3_mu_sigma.append([0, 0])
                pressure_mu_sigma.append([0, 0])

        try:
            df_result_train = pd.DataFrame()

            df_result_train['Ranges'] = ['0-200', '200-400', '400-600', '600-800', '800-1000', '1000-1200',
                                         '1200-1400', '1400-1600', '1600-1800', '1800+']
            df_result_train['T1'] = temp_1_mu_sigma
            df_result_train['T2'] = temp_2_mu_sigma
            df_result_train['T3'] = temp_3_mu_sigma
            df_result_train['T4'] = temp_4_mu_sigma
            df_result_train['T8'] = temp_8_mu_sigma
            df_result_train['P1'] = power_1_mu_sigma
            df_result_train['P2'] = power_2_mu_sigma
            df_result_train['P3'] = power_3_mu_sigma
            df_result_train['Pressure'] = pressure_mu_sigma
        except:
            print("ERROR: ошибка в формировании датафрейма-результата")
            input()
            exit()

        try:
            cur_dir = os.path.abspath(os.curdir)
            df_result_train.to_csv(f"{cur_dir}\Result_Train.csv", columns = df_result_train.columns, index=False)
        except:
            print("ERROR: ошибка записи датафрейма в файл Result_Train.csv")
            input()
            exit()

    def __complete_pieces(self):
        temp_ust = [[], [], [], [], [], [], [], [], [], []]
        temp_1 = [[], [], [], [], [], [], [], [], [], []]
        temp_2 = [[], [], [], [], [], [], [], [], [], []]
        temp_3 = [[], [], [], [], [], [], [], [], [], []]
        temp_4 = [[], [], [], [], [], [], [], [], [], []]
        temp_8 = [[], [], [], [], [], [], [], [], [], []]
        power_1 = [[], [], [], [], [], [], [], [], [], []]
        power_2 = [[], [], [], [], [], [], [], [], [], []]
        power_3 = [[], [], [], [], [], [], [], [], [], []]
        pressure = [[], [], [], [], [], [], [], [], [], []]

        index = -1

        print(f"Обработка данных {len(self.df_periods)} периодов")
        for period in self.df_periods['Служ.инф.']:
            for i in tqdm(range(period[0], period[1])):
                value_ust = self.df_T_u.values[i][2]

                if 0 <= value_ust < 200:
                    index = 0
                elif 200 <= value_ust < 400:
                    index = 1
                elif 400 <= value_ust < 600:
                    index = 2
                elif 600 <= value_ust < 800:
                    index = 3
                elif 800 <= value_ust < 1000:
                    index = 4
                elif 1000 <= value_ust < 1200:
                    index = 5
                elif 1200 <= value_ust < 1400:
                    index = 6
                elif 1400 <= value_ust < 1600:
                    index = 7
                elif 1600 <= value_ust < 1800:
                    index = 8
                else:
                    index = 9

                if index != -1:
                    temp_ust[index].append(value_ust)
                    temp_1[index].append(self.df_P1_T1['T'].values[i])
                    temp_2[index].append(self.df_P1_T2['T'].values[i])
                    temp_3[index].append(self.df_P1_T3['T'].values[i])
                    temp_4[index].append(self.df_P1_T4['T'].values[i])
                    temp_8[index].append(self.df_P1_T8['T'].values[i])

                    power_1[index].append(self.df_P1_T1['P'].values[i])
                    power_2[index].append(self.df_P2_T1['P'].values[i])
                    power_3[index].append(self.df_P3_T1['P'].values[i])

                    pressure[index].append(self.df_P1_Pr['Pressure'].values[i])
                else:
                    print("ERROR: index = -1")

        return temp_ust, temp_1, temp_2, temp_3, temp_4, temp_8, power_1, power_2, power_3, pressure

    def __spline(self):
        for i in range(11):
            for j in range(10):
                if len(self.result_pieces[-4][j]) > 6:
                    self.result_pieces[-4][j] = savgol_filter(self.result_pieces[-4][j], 6, 1)
                    self.result_pieces[-3][j] = savgol_filter(self.result_pieces[-3][j], 6, 1)
                    self.result_pieces[-2][j] = savgol_filter(self.result_pieces[-2][j], 6, 1)
                    self.result_pieces[-1][j] = savgol_filter(self.result_pieces[-1][j], 6, 1)

    def __calc_derivate(self):
        temp_1_derivate = [[], [], [], [], [], [], [], [], [], []]
        temp_2_derivate = [[], [], [], [], [], [], [], [], [], []]
        temp_3_derivate = [[], [], [], [], [], [], [], [], [], []]
        temp_4_derivate = [[], [], [], [], [], [], [], [], [], []]
        temp_8_derivate = [[], [], [], [], [], [], [], [], [], []]
        power_1_derivate = [[], [], [], [], [], [], [], [], [], []]
        power_2_derivate = [[], [], [], [], [], [], [], [], [], []]
        power_3_derivate = [[], [], [], [], [], [], [], [], [], []]
        pressure_derivate = [[], [], [], [], [], [], [], [], [], []]

        for pie in range(len(temp_1_derivate)):
            for i in range(1, len(self.result_pieces[1][pie])):
                temp_1_derivate[pie].append(self.result_pieces[1][pie][i] - self.result_pieces[1][pie][i - 1])
                temp_2_derivate[pie].append(self.result_pieces[2][pie][i] - self.result_pieces[2][pie][i - 1])
                temp_3_derivate[pie].append(self.result_pieces[3][pie][i] - self.result_pieces[3][pie][i - 1])
                temp_4_derivate[pie].append(self.result_pieces[4][pie][i] - self.result_pieces[4][pie][i - 1])
                temp_8_derivate[pie].append(self.result_pieces[5][pie][i] - self.result_pieces[5][pie][i - 1])

                power_1_derivate[pie].append(self.result_pieces[6][pie][i] - self.result_pieces[6][pie][i - 1])
                power_2_derivate[pie].append(self.result_pieces[7][pie][i] - self.result_pieces[7][pie][i - 1])
                power_3_derivate[pie].append(self.result_pieces[8][pie][i] - self.result_pieces[8][pie][i - 1])

                pressure_derivate[pie].append(self.result_pieces[9][pie][i] - self.result_pieces[9][pie][i - 1])

        return temp_1_derivate, temp_2_derivate, temp_3_derivate, temp_4_derivate, temp_8_derivate,\
            power_1_derivate, power_2_derivate, power_3_derivate, pressure_derivate


log_path = input("Введите путь к папке с Лог-Файлами:  ")
# log_path = r'C:\Users\user\Desktop\Ostec\log\2logs'

log_files = LogFiles(log_path)

calc = Calculations(log_files)
calc.find_sigma()

print("\nПоиск границ завершен. Результат записан в файл Result_Train.csv")
input()
