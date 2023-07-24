import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.signal import savgol_filter
from statistics import fmean, stdev
from tqdm import tqdm
import tkinter as tk

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
        self.__df_temp = pd.read_csv(temp, on_bad_lines='skip', sep='\t', encoding='utf-16')
        self.__df_curr = pd.read_csv(curr, on_bad_lines='skip', sep='\t', encoding='utf-16')
        self.__df_volt = pd.read_csv(volt, on_bad_lines='skip', sep='\t', encoding='utf-16')
        self.__df_pres = pd.read_csv(pres, on_bad_lines='skip', sep='\t', encoding='utf-16')

        self.__df_temp = self.__del_first_block(self.__df_temp)
        self.__df_curr = self.__del_first_block(self.__df_curr)
        self.__df_volt = self.__del_first_block(self.__df_volt)
        self.__df_pres = self.__del_first_block(self.__df_pres)

        self.__crossing()

    def __del_first_block(self, df_file):
        len_first_block = 0
        time_ms = df_file['Time_ms'].values[0]
        for i in range(len(df_file['Time_ms'].values)):
            if df_file['Time_ms'].values[i] != time_ms:
                len_first_block = i
                break

        df_file = df_file.drop(range(len_first_block))
        return df_file


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

        # "DB21_RS485_Omix_Ow_Mera_RRG_Data_real pan_ow{3}"    "2023-06-27 15:35:25"
        # 30.5275
        # 1
        # 45104649591.5509
        # "DB21_RS485_Omix_Ow_Mera_RRG_Data_real pan_ow{4}"    "2023-06-27 15:35:25"
        # 26.4084
        # 1
        # 45104649591.5509
        # "DB21_RS485_Omix_Ow_Mera_RRG_Data_real pan_ow{5}"    "2023-06-27 15:35:25"
        # 27.28109
        # 1
        # 45104649591.5509
        # "DB21_RS485_Omix_Ow_Mera_RRG_Data_real pan_ow{8}"    "2023-06-27 15:35:25"
        # 27.7454
        # 1
        # 45104649591.5509
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

        print(len(self.df_P1_T1), len(self.df_P1_T2), len(self.df_P1_T3), len(self.df_P1_T4), len(self.df_P1_T8))
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

        dif = len(self.df_T_u) - len(self.df_P1_T1)
        if dif > 0:
            if self.df_T_u.values[0][0] != self.df_P1_T1.values[0][0]:
                self.df_T_u = self.df_T_u[dif:]
            else:
                self.df_T_u = self.df_T_u[:0 - dif]
        elif dif < 0:
            if self.df_T_u.values[0][0] != self.df_P1_T1.values[0][0]:
                self.df_P1_T1 = self.df_P1_T1[dif:]
            else:
                self.df_P1_T1 = self.df_P1_T1[:0 - dif]

        # print(self.df_P1_Pr)
        # print(self.df_P1_T1)
        # print(self.df_T_u.columns)
        # exit()

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
        answer = input("\nХотите продолжить? (Д/Н) ")
        while (answer.upper() != 'Д') and (answer.upper() != 'Н'):
            answer = input("\nХотите продолжить? (Д/Н) ")
        if answer.upper() == 'Н':
            exit()

    def find_sigma(self):
        self.__spline()
        self.result_pieces = self.__complete_pieces()

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

        print(f"\nОбработка данных {len(self.df_periods)} периодов")
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

                    power_1[index].append(self.df_P1_T1_spline['P'].values[i])
                    power_2[index].append(self.df_P2_T1_spline['P'].values[i])
                    power_3[index].append(self.df_P3_T1_spline['P'].values[i])

                    pressure[index].append(self.df_P1_Pr_spline['Pressure'].values[i])
                else:
                    print("ERROR: index = -1")

        return temp_ust, temp_1, temp_2, temp_3, temp_4, temp_8, power_1, power_2, power_3, pressure

    def __spline(self):
        if len(self.df_P1_T1) < 150:
            print("ERROR: недостаточно данных. Лог-файл слишком короткий.")
            exit()
            input()

        self.df_P1_T1_spline = self.df_P1_T1
        self.df_P2_T1_spline = self.df_P2_T1
        self.df_P3_T1_spline = self.df_P3_T1
        self.df_P1_Pr_spline = self.df_P1_Pr

        for i in range(11):
            self.df_P1_T1_spline['P'] = savgol_filter(self.df_P1_T1_spline['P'].values, 6, 1)
            self.df_P2_T1_spline['P'] = savgol_filter(self.df_P2_T1_spline['P'].values, 6, 1)
            self.df_P3_T1_spline['P'] = savgol_filter(self.df_P3_T1_spline['P'].values, 6, 1)
            self.df_P1_Pr_spline['Pressure'] = savgol_filter(self.df_P1_Pr_spline['Pressure'].values, 6, 1)

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
                der1 = self.result_pieces[1][pie][i] - self.result_pieces[1][pie][i - 1]
                if abs(der1) < 100:
                    temp_1_derivate[pie].append(der1)
                der2 = self.result_pieces[2][pie][i] - self.result_pieces[2][pie][i - 1]
                if abs(der2) < 100:
                    temp_2_derivate[pie].append(der2)
                der3 = self.result_pieces[3][pie][i] - self.result_pieces[3][pie][i - 1]
                if abs(der3) < 100:
                    temp_3_derivate[pie].append(der3)
                der4 = self.result_pieces[4][pie][i] - self.result_pieces[4][pie][i - 1]
                if abs(der4) < 100:
                    temp_4_derivate[pie].append(der4)
                der5 = self.result_pieces[5][pie][i] - self.result_pieces[5][pie][i - 1]
                if abs(der5) < 100:
                    temp_8_derivate[pie].append(der5)

                power_1_derivate[pie].append(self.result_pieces[6][pie][i] - self.result_pieces[6][pie][i - 1])
                power_2_derivate[pie].append(self.result_pieces[7][pie][i] - self.result_pieces[7][pie][i - 1])
                power_3_derivate[pie].append(self.result_pieces[8][pie][i] - self.result_pieces[8][pie][i - 1])

                pressure_derivate[pie].append(self.result_pieces[9][pie][i] - self.result_pieces[9][pie][i - 1])

        return temp_1_derivate, temp_2_derivate, temp_3_derivate, temp_4_derivate, temp_8_derivate,\
            power_1_derivate, power_2_derivate, power_3_derivate, pressure_derivate

    def show_graphics(self, length_red):

        # ----------------------------------------------------------------------------------------------

        root = tk.Tk()
        root.geometry('360x300+100+200')
        root.title('Графики')
        root.iconbitmap(default="C:/Users/user/Downloads/logo1.ico")  # Иконка

        period = tk.StringVar(value=1)  # начальное значение 1
        def set_begin_end(period_):
            begin = self.df_periods['Служ.инф.'].values[int(period_.get()) - 1][0]
            end = self.df_periods['Служ.инф.'].values[int(period_.get()) - 1][1]
            return begin, end

        tk.Label(text="\n", font=("Arial", 7)).grid(row=1, column=2, sticky='e')
        tk.Label(text="  Выберите период: ", font=("Arial", 10)).grid(row=3, column=1)
        spinbox = tk.Spinbox(from_=1.0, to=float(len(self.df_periods)), textvariable=period).grid(row=3, column=2)

        tk.Label(text="\n   Выберите датчики\n", font=("Arial", 10)).grid(row=5, column=2)
        tk.Label(text="температуры:", font=("Arial", 10)).grid(row=6, column=1)
        tk.Label(text="мощности:", font=("Arial", 10)).grid(row=6, column=2)
        tk.Label(text="давления:", font=("Arial", 10)).grid(row=6, column=3)

        enabled_T1 = tk.IntVar()
        enabled_T2 = tk.IntVar()
        enabled_T3 = tk.IntVar()
        enabled_T4 = tk.IntVar()
        enabled_T8 = tk.IntVar()
        enabled_P1 = tk.IntVar()
        enabled_P2 = tk.IntVar()
        enabled_P3 = tk.IntVar()
        enabled_Pr = tk.IntVar()

        checkbutton_T1 = tk.Checkbutton(text="TI1   ", variable=enabled_T1).grid(row=7, column=1)
        checkbutton_T2 = tk.Checkbutton(text="TI2.1", variable=enabled_T2).grid(row=8, column=1)
        checkbutton_T3 = tk.Checkbutton(text="TI2.2", variable=enabled_T3).grid(row=9, column=1)
        checkbutton_T4 = tk.Checkbutton(text="TI3   ", variable=enabled_T4).grid(row=10, column=1)
        checkbutton_T8 = tk.Checkbutton(text="TE    ", variable=enabled_T8).grid(row=11, column=1)
        checkbutton_P1 = tk.Checkbutton(text="P1    ", variable=enabled_P1).grid(row=7, column=2)
        checkbutton_P2 = tk.Checkbutton(text="P2    ", variable=enabled_P2).grid(row=8, column=2)
        checkbutton_P3 = tk.Checkbutton(text="P3    ", variable=enabled_P3).grid(row=9, column=2)
        checkbutton_Pr = tk.Checkbutton(text="PS4  ", variable=enabled_Pr).grid(row=7, column=3)

        # def complete_zones(begin, end):

        def click_btn_calc(period_):
            res = set_begin_end(period_)
            begin = res[0]
            end = res[1]

            cur_dir = os.path.abspath(os.curdir)
            df_result_train = pd.read_csv(cur_dir + '\Result_Train.csv', sep=',')

            zones_values = [[[], [], [], [], [], [], [], []],
                            [[], [], [], [], [], [], [], []],
                            [[], [], [], [], [], [], [], []]]
            zones_time = [[[], [], [], [], [], [], [], []],
                          [[], [], [], [], [], [], [], []],
                          [[], [], [], [], [], [], [], []]]
            print("\nПреобразуем данные для графиков...")

            cnt_arr = [0, 0, 0, 0, 0]
            flg_arr = [False, False, False, False, False]

            for i in tqdm(range(begin, end)):
                k_T = []
                k_P = []

                k_T.append(self.df_P1_T1.values[i + 1][-1] - self.df_P1_T1.values[i][-1])
                k_T.append(self.df_P1_T2.values[i + 1][-1] - self.df_P1_T2.values[i][-1])
                k_T.append(self.df_P1_T3.values[i + 1][-1] - self.df_P1_T3.values[i][-1])
                k_T.append(self.df_P1_T4.values[i + 1][-1] - self.df_P1_T4.values[i][-1])
                k_T.append(self.df_P1_T8.values[i + 1][-1] - self.df_P1_T8.values[i][-1])

                k_P.append(self.df_P1_T1.values[i + 1][1] - self.df_P1_T1.values[i][1])
                k_P.append(self.df_P2_T1.values[i + 1][1] - self.df_P2_T1.values[i][1])
                k_P.append(self.df_P3_T1.values[i + 1][1] - self.df_P3_T1.values[i][1])

                k_Pr = self.df_P1_Pr.values[i + 1][-1] - self.df_P1_Pr.values[i][-1]

                Temp = []
                Time = []

                Temp.append(self.df_P1_T1.values[i][-1])
                Temp.append(self.df_P1_T2.values[i][-1])
                Temp.append(self.df_P1_T3.values[i][-1])
                Temp.append(self.df_P1_T4.values[i][-1])
                Temp.append(self.df_P1_T8.values[i][-1])

                Time.append(self.df_P1_T1.values[i][0])
                Time.append(self.df_P1_T2.values[i][0])
                Time.append(self.df_P1_T3.values[i][0])
                Time.append(self.df_P1_T4.values[i][0])
                Time.append(self.df_P1_T8.values[i][0])

                Power = []
                Time_p = []

                Power.append(self.df_P1_T1_spline['P'].values[i])
                Power.append(self.df_P2_T1_spline['P'].values[i])
                Power.append(self.df_P3_T1_spline['P'].values[i])

                Time_p.append(self.df_P1_T1_spline['Time_ms'].values[i])
                Time_p.append(self.df_P2_T1_spline['Time_ms'].values[i])
                Time_p.append(self.df_P3_T1_spline['Time_ms'].values[i])

                Pressure = self.df_P1_Pr_spline['Pressure'].values[i]

                Time_pr = self.df_P1_Pr_spline['Time_ms'].values[i]

                for zone in range(0, 1800, 200):

                    if zone <= self.df_T_u['VarValue'].values[i] < zone + 200:

                        # ----- T E R M O P A I R S -----
                        for termopara in range(1, 6):

                            mu_T = float(df_result_train.values[int(zone / 200)][termopara][
                                         df_result_train.values[int(zone / 200)][termopara].find('[') + 1:
                                         df_result_train.values[int(zone / 200)][termopara].find(',')])
                            sigma_T = float(df_result_train.values[int(zone / 200)][termopara][
                                            df_result_train.values[int(zone / 200)][termopara].find(' ') + 1:
                                            df_result_train.values[int(zone / 200)][termopara].find(']')])

                            if mu_T - sigma_T * 2 <= k_T[termopara - 1] <= mu_T + sigma_T * 2:
                                if cnt_arr[termopara - 1] > 0:
                                    if cnt_arr[termopara - 1] < length_red:
                                        for j in range(len(zones_values[2][termopara - 1]) - cnt_arr[termopara - 1],
                                                       len(zones_values[2][termopara - 1])):
                                            zones_values[1][termopara - 1].append(zones_values[2][termopara - 1][j])
                                            zones_time[1][termopara - 1].append(zones_time[2][termopara - 1][j])
                                        del zones_values[2][termopara - 1][-cnt_arr[termopara - 1]:]
                                        del zones_time[2][termopara - 1][-cnt_arr[termopara - 1]:]

                                    cnt_arr[termopara - 1] = 0

                                if mu_T - sigma_T <= k_T[termopara - 1] <= mu_T + sigma_T:
                                    zones_values[0][termopara - 1].append(Temp[termopara - 1])
                                    zones_time[0][termopara - 1].append(Time[termopara - 1])
                                else:
                                    zones_values[1][termopara - 1].append(Temp[termopara - 1])
                                    zones_time[1][termopara - 1].append(Time[termopara - 1])
                            else:
                                cnt_arr[termopara - 1] += 1
                                zones_values[2][termopara - 1].append(Temp[termopara - 1])
                                zones_time[2][termopara - 1].append(Time[termopara - 1])

                        # ----- P O W E R S -----
                        for power_idx in range(6, 9):
                            mu_T = float(df_result_train.values[int(zone / 200)][power_idx][
                                         df_result_train.values[int(zone / 200)][power_idx].find('[') + 1:
                                         df_result_train.values[int(zone / 200)][power_idx].find(',')])
                            sigma_T = float(df_result_train.values[int(zone / 200)][power_idx][
                                            df_result_train.values[int(zone / 200)][power_idx].find(' ') + 1:
                                            df_result_train.values[int(zone / 200)][power_idx].find(']')])

                            if mu_T - sigma_T * 2 <= k_P[power_idx - 6] <= mu_T + sigma_T * 2:
                                if mu_T - sigma_T <= k_P[power_idx - 6] <= mu_T + sigma_T:
                                    zones_values[0][power_idx - 1].append(Power[power_idx - 6])
                                    zones_time[0][power_idx - 1].append(Time_p[power_idx - 6])
                                else:
                                    zones_values[1][power_idx - 1].append(Power[power_idx - 6])
                                    zones_time[1][power_idx - 1].append(Time_p[power_idx - 6])
                            else:
                                zones_values[2][power_idx - 1].append(Power[power_idx - 6])
                                zones_time[2][power_idx - 1].append(Time_p[power_idx - 6])

                        # ----- P R E S S U R E -----
                        mu_T = float(df_result_train.values[int(zone / 200)][-1][
                                     df_result_train.values[int(zone / 200)][-1].find('[') + 1:
                                     df_result_train.values[int(zone / 200)][-1].find(',')])
                        sigma_T = float(df_result_train.values[int(zone / 200)][-1][
                                        df_result_train.values[int(zone / 200)][-1].find(' ') + 1:
                                        df_result_train.values[int(zone / 200)][-1].find(']')])

                        if mu_T - sigma_T * 2 <= k_Pr <= mu_T + sigma_T * 2:
                            if mu_T - sigma_T <= k_Pr <= mu_T + sigma_T:
                                zones_values[0][-1].append(Pressure)
                                zones_time[0][-1].append(Time_pr)
                            else:
                                zones_values[1][-1].append(Pressure)
                                zones_time[1][-1].append(Time_pr)
                        else:
                            zones_values[2][-1].append(Pressure)
                            zones_time[2][-1].append(Time_pr)

                    if 1800 <= self.df_T_u['VarValue'].values[i]:

                        # ----- T E R M O P A I R S -----
                        for termopara in range(1, 6):
                            mu_T = float(df_result_train.values[-1][termopara][
                                         df_result_train.values[-1][termopara].find('[') + 1:df_result_train.values[-1][
                                             termopara].find(',')])
                            sigma_T = float(df_result_train.values[-1][termopara][
                                            df_result_train.values[-1][termopara].find(' ') + 1:
                                            df_result_train.values[-1][termopara].find(']')])

                            if mu_T - sigma_T * 2 <= k_T[termopara - 1] <= mu_T + sigma_T * 2:
                                if cnt_arr[termopara - 1] > 0:
                                    if cnt_arr[termopara - 1] < length_red:
                                        for j in range(len(zones_values[2][termopara - 1]) - cnt_arr[termopara - 1],
                                                       len(zones_values[2][termopara - 1])):
                                            zones_values[1][termopara - 1].append(zones_values[2][termopara - 1][j])
                                            zones_time[1][termopara - 1].append(zones_time[2][termopara - 1][j])
                                        del zones_values[2][termopara - 1][-cnt_arr[termopara - 1]:]
                                        del zones_time[2][termopara - 1][-cnt_arr[termopara - 1]:]

                                    cnt_arr[termopara - 1] = 0

                                if mu_T - sigma_T <= k_T[termopara - 1] <= mu_T + sigma_T:
                                    zones_values[0][termopara - 1].append(Temp[termopara - 1])
                                    zones_time[0][termopara - 1].append(Time[termopara - 1])
                                else:
                                    zones_values[1][termopara - 1].append(Temp[termopara - 1])
                                    zones_time[1][termopara - 1].append(Time[termopara - 1])
                            else:
                                cnt_arr[termopara - 1] += 1
                                zones_values[2][termopara - 1].append(Temp[termopara - 1])
                                zones_time[2][termopara - 1].append(Time[termopara - 1])

                        # ----- P O W E R S -----
                        for power_idx in range(6, 9):
                            mu_T = float(df_result_train.values[int(zone / 200)][power_idx][
                                         df_result_train.values[int(zone / 200)][power_idx].find('[') + 1:
                                         df_result_train.values[int(zone / 200)][power_idx].find(',')])
                            sigma_T = float(df_result_train.values[int(zone / 200)][power_idx][
                                            df_result_train.values[int(zone / 200)][power_idx].find(' ') + 1:
                                            df_result_train.values[int(zone / 200)][power_idx].find(']')])

                            if mu_T - sigma_T * 2 <= k_P[power_idx - 6] <= mu_T + sigma_T * 2:
                                if mu_T - sigma_T <= k_P[power_idx - 6] <= mu_T + sigma_T:
                                    zones_values[0][power_idx - 1].append(Power[power_idx - 6])
                                    zones_time[0][power_idx - 1].append(Time_p[power_idx - 6])
                                else:
                                    zones_values[1][power_idx - 1].append(Power[power_idx - 6])
                                    zones_time[1][power_idx - 1].append(Time_p[power_idx - 6])
                            else:
                                zones_values[2][power_idx - 1].append(Power[power_idx - 6])
                                zones_time[2][power_idx - 1].append(Time_p[power_idx - 6])

                        # ----- P R E S S U R E -----
                        mu_T = float(df_result_train.values[int(zone / 200)][-1][
                                     df_result_train.values[int(zone / 200)][-1].find('[') + 1:
                                     df_result_train.values[int(zone / 200)][-1].find(',')])
                        sigma_T = float(df_result_train.values[int(zone / 200)][-1][
                                        df_result_train.values[int(zone / 200)][-1].find(' ') + 1:
                                        df_result_train.values[int(zone / 200)][-1].find(']')])

                        if mu_T - sigma_T * 2 <= k_Pr <= mu_T + sigma_T * 2:
                            if mu_T - sigma_T <= k_Pr <= mu_T + sigma_T:
                                zones_values[0][-1].append(Pressure)
                                zones_time[0][-1].append(Time_pr)
                            else:
                                zones_values[1][-1].append(Pressure)
                                zones_time[1][-1].append(Time_pr)
                        else:
                            zones_values[2][-1].append(Pressure)
                            zones_time[2][-1].append(Time_pr)

            if enabled_T1.get() == 1:
                plt.plot(self.df_P1_T1['Time_ms'].values[begin:end], self.df_P1_T1['T'].values[begin:end], color='black', linewidth=1, label="Literacy rate")
                plt.scatter(zones_time[0][0][:], zones_values[0][0][:], color='green', linewidths=1)
                plt.scatter(zones_time[1][0][:], zones_values[1][0][:], color='yellow', linewidths=1)
                plt.scatter(zones_time[2][0][:], zones_values[2][0][:], color='red', linewidths=1)

            if enabled_T2.get() == 1:
                plt.plot(self.df_P1_T2['Time_ms'].values[begin:end], self.df_P1_T2['T'].values[begin:end], color='black', linewidth=1, label="Literacy rate")
                plt.scatter(zones_time[0][1][:], zones_values[0][1][:], color='green', linewidths=1)
                plt.scatter(zones_time[1][1][:], zones_values[1][1][:], color='yellow', linewidths=1)
                plt.scatter(zones_time[2][1][:], zones_values[2][1][:], color='red', linewidths=1)

            if enabled_T3.get() == 1:
                plt.plot(self.df_P1_T3['Time_ms'].values[begin:end], self.df_P1_T3['T'].values[begin:end], color='black', linewidth=1, label="Literacy rate")
                plt.scatter(zones_time[0][2][:], zones_values[0][2][:], color='green', linewidths=1)
                plt.scatter(zones_time[1][2][:], zones_values[1][2][:], color='yellow', linewidths=1)
                plt.scatter(zones_time[2][2][:], zones_values[2][2][:], color='red', linewidths=1)

            if enabled_T4.get() == 1:
                plt.plot(self.df_P1_T4['Time_ms'].values[begin:end], self.df_P1_T4['T'].values[begin:end], color='black', linewidth=1, label="Literacy rate")
                plt.scatter(zones_time[0][3][:], zones_values[0][3][:], color='green', linewidths=1)
                plt.scatter(zones_time[1][3][:], zones_values[1][3][:], color='yellow', linewidths=1)
                plt.scatter(zones_time[2][3][:], zones_values[2][3][:], color='red', linewidths=1)

            if enabled_T8.get() == 1:
                plt.plot(self.df_P1_T8['Time_ms'].values[begin:end], self.df_P1_T8['T'].values[begin:end], color='black', linewidth=1, label="Literacy rate")
                plt.scatter(zones_time[0][4][:], zones_values[0][4][:], color='green', linewidths=1)
                plt.scatter(zones_time[1][4][:], zones_values[1][4][:], color='yellow', linewidths=1)
                plt.scatter(zones_time[2][4][:], zones_values[2][4][:], color='red', linewidths=1)

            if enabled_P1.get() == 1:
                plt.plot(self.df_P1_T1['Time_ms'].values[begin:end], self.df_P1_T1_spline['P'].values[begin:end], color='black', linewidth=1, label="Literacy rate")
                plt.scatter(zones_time[0][5][:], zones_values[0][5][:], color='green', linewidths=1)
                plt.scatter(zones_time[1][5][:], zones_values[1][5][:], color='yellow', linewidths=1)
                plt.scatter(zones_time[2][5][:], zones_values[2][5][:], color='red', linewidths=1)

            if enabled_P2.get() == 1:
                plt.plot(self.df_P1_T2['Time_ms'].values[begin:end], self.df_P2_T1_spline['P'].values[begin:end], color='black', linewidth=1, label="Literacy rate")
                plt.scatter(zones_time[0][6][:], zones_values[0][6][:], color='green', linewidths=1)
                plt.scatter(zones_time[1][6][:], zones_values[1][6][:], color='yellow', linewidths=1)
                plt.scatter(zones_time[2][6][:], zones_values[2][6][:], color='red', linewidths=1)

            if enabled_P3.get() == 1:
                plt.plot(self.df_P1_T3['Time_ms'].values[begin:end], self.df_P3_T1_spline['P'].values[begin:end], color='black', linewidth=1, label="Literacy rate")
                plt.scatter(zones_time[0][7][:], zones_values[0][7][:], color='green', linewidths=1)
                plt.scatter(zones_time[1][7][:], zones_values[1][7][:], color='yellow', linewidths=1)
                plt.scatter(zones_time[2][7][:], zones_values[2][7][:], color='red', linewidths=1)

            if enabled_Pr.get() == 1:
                plt.plot(self.df_P1_Pr['Time_ms'].values[begin:end], self.df_P1_Pr_spline['Pressure'].values[begin:end], color='black', linewidth=1, label="Literacy rate")
                plt.scatter(zones_time[0][-1][:], zones_values[0][-1][:], color='green', linewidths=1)
                plt.scatter(zones_time[1][-1][:], zones_values[1][-1][:], color='yellow', linewidths=1)
                plt.scatter(zones_time[2][-1][:], zones_values[2][-1][:], color='red', linewidths=1)

            if sum([enabled_T1.get(), enabled_T2.get(), enabled_T3.get(), enabled_T4.get(), enabled_T8.get(),
                    enabled_P1.get(), enabled_P2.get(), enabled_P3.get(), enabled_Pr.get()]) == 0:
                tk.messagebox.showwarning(title="Предупреждение", message="Вы не выбрали ни один параметр")
            else:
                plt.show()


        def click_btn_exit():
            exit()

        btn_calc = tk.Button(text="Построить", command=lambda: click_btn_calc(period)).grid(row=12, column=2)
        btn_exit = tk.Button(text="Выход", command=click_btn_exit).grid(row=12, column=3)

        root.mainloop()



log_path = input("Введите путь к папке с Лог-Файлами:  ")
# log_path = r'C:\Users\user\Desktop\Ostec\log\2logs'

log_files = LogFiles(log_path)

calc = Calculations(log_files)
calc.find_sigma()
print("\nПоиск границ завершен. Результат записан в файл Result_Train.csv")

calc.show_graphics(6)

input()
