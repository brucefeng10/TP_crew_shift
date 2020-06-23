import csv
import datetime
import json
import numpy as np
import pandas as pd
from gurobipy import *


def read_data():
    """Reading data."""

    team_info = pd.read_csv(r'C:\Bee\aHuaat\TP_crew_shift\params\team_info.csv', index_col=('team_id',))
    team_info = team_info.to_dict()

    # index_col must be in usecols
    shift_info = pd.read_csv(r'C:\Bee\aHuaat\TP_crew_shift\params\shift_info.csv', index_col=['shift_id'],
                             usecols=['shift_id', 'shift_time', 'shift_minute', 'shift_type', 'shift_type_id', 'start1', 'end2'])
    shift_info = shift_info.to_dict()
    # print(shift_info)
    shift_cover = pd.read_csv(r'C:\Bee\aHuaat\TP_crew_shift\params\shift_info.csv', index_col=('shift_id', 'start1', 'end1', 'start2', 'end2', 'shift_time', 'shift_minute', 'shift_type', 'shift_type_id'))
    shift_cover = shift_cover.values
    shift_cover[np.isnan(shift_cover)] = 0
    night_shift_info = pd.read_csv(r'C:\Bee\aHuaat\TP_crew_shift\params\night_shift_info.csv', index_col=('shift_id', 'start1', 'end1', 'start2', 'end2', 'shift_time', 'shift_minute', 'shift_type', 'shift_type_id'))
    night_shift_info = night_shift_info.values
    night_shift_info[np.isnan(night_shift_info)] = 0
    night_shift_info = night_shift_info[0]

    call_dem = pd.read_csv(r'C:\Bee\aHuaat\TP_crew_shift\params\call_demand826.csv', index_col=('shift_id', 'shift'))
    call_dem = call_dem.values

    return team_info, shift_info, shift_cover, night_shift_info, call_dem


class CrewScheduling(object):
    """Crew scheduling of Taiping customer service staff."""
    def __init__(self):
        self.team_info, self.shift_info, self.shift_cover, self.night_shift_info, self.call_dem = read_data()
        self.shift_type_compo = self.shift_type_compose(self.shift_info['shift_type_id'])
        self.shift_start_time, self.shift_end_time = self.shift_start(self.shift_info['start1']), self.shift_end(self.shift_info['end2'])
        self.team_size = self.team_info['worker_cnt']
        self.team_cnt = len(self.team_size)  # 班组数量
        self.shift_cnt = len(self.shift_info['shift_time'])  # 班次数量
        self.dem_timing_cnt, self.sche_day_cnt = self.call_dem.shape  # 需求统计点数量，排班规划天数
        # self.sche_day_cnt = 21
        self.x_mat = -np.ones([self.team_cnt, self.sche_day_cnt])  # save result
        self.max_work_day = 23  # 最大上班天数
        self.max_consecutive = 6  # 最大连续工作天数
        self.min_consecutive = 2  # 最小连续工作天数
        self.work_day_diff = 1  # 坐席员工工作天数之差（不包括调休）
        self.work_minute_diff = 480  # 坐席员工工作时间之差（不包括调休）
        self.zaoban_diff = 2  # 不同客服的早班次数差距限制，4-6次
        self.wuban_diff = 1  # 不同客服的午班次数差距限制，2-3次
        self.yeban_diff = 1  # 不同客服的夜班次数差距限制，1-2次
        self.tiaoban_diff = 1  # 不同客服的跳班次数差距限制，2-3次
        self.max_yeban_gap = 10  # 两个夜班之间最小间隔天数
        self.max_tiaoban_gap = 3  # 两个跳班之间最小间隔天数
        self.max_yeban_cnt = 2  # 每人总的夜班次数限制
        self.max_tiaoban_cnt = 4  # 每人总的跳班次数限制
        self.max_yeban_cnt = 4  # 每人总的午班次数限制
        self.max_2rest = 0  # 最少连续两天休息次数
        self.min_weekend_rest = 1  # 周末最少休息次数
        self.shift_min_gap = 10  # 每人两个班次的最小时间间隔10h
        self.weekend_days = [5, 6, 12, 13, 19, 20, 26, 27]  # weekend days
        # self.weekend_days = [5, 6, 12, 13, 19, 20]  # weekend days
        self.weekend_rest_cnt = 1  # minimum weekend rest count

    @staticmethod
    def shift_type_compose(shift_type_dict):
        """Get the shifts of each shift type.
        shift_type_dict: {shift_id: shift_type_id}
        shift_type_compo: {shift_type_id: [shift_id1, shift_id2, ...]}"""

        shift_type_compo = dict()
        for k, v in shift_type_dict.items():
            if v in shift_type_compo:
                shift_type_compo[v].append(k)
            else:
                shift_type_compo[v] = [k]
        return shift_type_compo

    def shift_start(self, start_time_str):
        """Get shift start time. Transfer str format("8:00") to int format.
        shift_start_time: {shift_id: start_time}
        """

        shift_start_time = dict()
        for ky, vl in start_time_str.items():
            ts = vl.split(':')
            shift_start_time[ky] = eval(ts[0]) * 60 + eval(ts[1])
        return shift_start_time

    def shift_end(self, end_time_str):
        """Get shift end time. Transfer str format("8:00") to int format.
        shift_end_time: {shift_id: end_time}
        """

        shift_end_time = dict()
        for ky, vl in end_time_str.items():
            ts = vl.split(':')
            if self.shift_info['shift_type_id'][ky] == 6:  # 夜班存在跨天情况，结束时间增加一天（24小时）
                shift_end_time[ky] = eval(ts[0]) * 60 + eval(ts[1]) + 24 * 60
            else:
                shift_end_time[ky] = eval(ts[0]) * 60 + eval(ts[1])
        return shift_end_time

    def ip_model(self):
        """Crew scheduling integer programming mdoel."""

        print('班组数量：', self.team_cnt)
        print('班次数量：', self.shift_cnt)
        print('需求点数量：', self.dem_timing_cnt)
        print('排班天数：', self.sche_day_cnt)

        try:
            m = Model('crew scheduling')
            x = m.addVars(self.team_cnt, self.shift_cnt, self.sche_day_cnt, vtype='B', name='x')
            # ct = m.addVars(self.team_cnt, self.sche_day_cnt-1, vtype='B', name='ct')
            cw = m.addVars(self.team_cnt, self.sche_day_cnt-1, vtype='B', name='cw')
            min_work = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='min_work')
            max_work = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='max_work')
            min_minute = m.addVar(lb=0, ub=30*24, vtype='I', name='min_minute')
            max_minute = m.addVar(lb=0, ub=30*24, vtype='I', name='max_minute')
            min_zao = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='min_zao')
            max_zao = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='max_zao')
            min_wu = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='min_wu')
            max_wu = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='max_wu')
            min_ye = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='min_ye')
            max_ye = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='max_ye')
            min_tiao = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='min_tiao')
            max_tiao = m.addVar(lb=0, ub=self.sche_day_cnt, vtype='I', name='max_tiao')

            obj1 = quicksum(self.team_size[i] * self.shift_info['shift_minute'][j]/60 * x[i, j, t] for i in range(
                self.team_cnt) for j in range(self.shift_cnt) for t in range(self.sche_day_cnt))
            obj2 = max_work - min_work
            m.setObjective(obj2, GRB.MINIMIZE)
            # m.setObjectiveN(obj1, index=0, priority=1, name='obj1')
            # m.setObjectiveN(obj2, index=1, priority=2, name='obj2')  # objective with larger priority will be optimized first

            cons = list()

            # satisfy call demand at any demand timing
            for t in range(self.sche_day_cnt):
                for k in range(14, self.dem_timing_cnt):  # no demand in 0:00-7:00
                    supply_kt = quicksum(self.team_size[i] * self.shift_cover[j, k] * x[i, j, t] for i in range(
                        self.team_cnt) for j in range(self.shift_cnt))
                    cons.append(m.addConstr(supply_kt >= self.call_dem[k, t]))
                    # + quicksum(team_size[i] * x[i, 93, t-1] for i in range(team_cnt)) * night_shift_info[k]

            # work at most 24 days for a month
            for i in range(self.team_cnt):
                work_day = quicksum(x[i, j, t] for j in range(self.shift_cnt) for t in range(self.sche_day_cnt))
                cons.append(m.addConstr(work_day <= self.max_work_day))

            # a team can execute at most one shift every day
            for t in range(self.sche_day_cnt):
                for i in range(self.team_cnt):
                    cons.append(m.addConstr(quicksum(x[i, j, t] for j in range(self.shift_cnt)) <= 1))
            # '''
            # min and max work day count
            for i in range(self.team_cnt):
                work_day = quicksum(x[i, j, t] for j in range(self.shift_cnt) for t in range(self.sche_day_cnt))
                cons.append(m.addConstr(min_work <= work_day))
                cons.append(m.addConstr(max_work >= work_day))
            # cons.append(m.addConstr(max_work - min_work <= 1))
            '''
            # min and max work time(minute) balance
            for i in range(self.team_cnt):
                work_minute = quicksum(self.shift_info['shift_minute'][j]/60 * x[i, j, t] for j in range(self.shift_cnt) for t in range(self.sche_day_cnt))
                cons.append(m.addConstr(min_minute <= work_minute))
                cons.append(m.addConstr(max_minute >= work_minute))
            cons.append(m.addConstr(max_minute - min_minute <= self.work_minute_diff/60))
            '''
            # max consecutive work day
            for i in range(self.team_cnt):
                for tc in range(self.sche_day_cnt-self.max_consecutive):
                    cons_sum = quicksum(x[i, j, t] for j in range(self.shift_cnt) for t in range(tc, tc+self.max_consecutive+1))
                    cons.append(m.addConstr(cons_sum <= self.max_consecutive))

            # can not rest for 2 consecutive days, can not rest after just one day work
            for i in range(self.team_cnt):
                for t in range(self.sche_day_cnt-1):
                    if i == 4 and t == 29:
                        continue
                    if i == 13 and t == 19:
                        continue
                    if i == 16 and t in {17, 18}:
                        continue
                    s1 = 0.5 * (1 - quicksum(x[i, j, t] for j in range(self.shift_cnt)))
                    s2 = quicksum(x[i, j, t+1] for j in range(self.shift_cnt))
                    cons.append(m.addConstr(s2 >= s1))
                    if t < self.sche_day_cnt-2:
                        s3 = quicksum(x[i, j, t+2] for j in range(self.shift_cnt))
                        cons.append(m.addConstr(s3 >= s1))

            # minimum gap between two YE/TIAO Ban
            for i in range(self.team_cnt):
                # YE ban gap
                for ty in range(self.sche_day_cnt-self.max_yeban_gap):
                    s1 = quicksum(x[i, j, t] for j in self.shift_type_compo[6] for t in range(ty, ty+self.max_yeban_gap+1))
                    cons.append(m.addConstr(s1 <= 1))
                # TIAO ban gap
                for tt in range(self.sche_day_cnt-self.max_tiaoban_gap):
                    s2 = quicksum(x[i, j, t] for j in self.shift_type_compo[3] for t in range(tt, tt+self.max_tiaoban_gap+1))
                    cons.append(m.addConstr(s2 <= 1))

            # minimum hour gap between 2 shifts
            for i in range(self.team_cnt):
                for t in range(self.sche_day_cnt-1):
                    s1 = quicksum(self.shift_end_time[j] * x[i, j, t] + (self.shift_min_gap*60-self.shift_start_time[t]) *
                                  x[i, j, t+1] for j in range(self.shift_cnt))
                    cons.append(s1 <= 24*60)

            # minimum rest day count on weekends
            for i in range(self.team_cnt):
                s1 = quicksum(x[i, j, t] for j in range(self.shift_cnt) for t in self.weekend_days)
                cons.append(m.addConstr(s1 >= self.weekend_rest_cnt))

            # max YE, TIAO, WU limit
            for i in range(self.team_cnt):
                s1 = quicksum(x[i, j, t] for j in self.shift_type_compo[6] for t in range(self.sche_day_cnt))
                s2 = quicksum(x[i, j, t] for j in self.shift_type_compo[3] for t in range(self.sche_day_cnt))
                s3 = quicksum(x[i, j, t] for j in self.shift_type_compo[5] for t in range(self.sche_day_cnt))
                cons.append(m.addConstr(s1 <= 2))
                cons.append(m.addConstr(s2 <= 4))
                cons.append(m.addConstr(s3 <= 4))

            # ZAO, WU, YE, TIAO difference
            for i in range(self.team_cnt):
                s1 = quicksum(x[i, j, t] for j in self.shift_type_compo[0] for t in range(self.sche_day_cnt))
                s2 = quicksum(x[i, j, t] for j in self.shift_type_compo[5] for t in range(self.sche_day_cnt))
                s3 = quicksum(x[i, j, t] for j in self.shift_type_compo[6] for t in range(self.sche_day_cnt))
                s4 = quicksum(x[i, j, t] for j in self.shift_type_compo[3] for t in range(self.sche_day_cnt))
                cons.append(m.addConstr(max_zao >= s1))
                cons.append(m.addConstr(min_zao <= s1))
                cons.append(m.addConstr(max_wu >= s2))
                cons.append(m.addConstr(min_wu <= s2))
                cons.append(m.addConstr(max_ye >= s3))
                cons.append(m.addConstr(min_ye <= s3))
                cons.append(m.addConstr(max_tiao >= s4))
                cons.append(m.addConstr(min_tiao <= s4))
            cons.append(m.addConstr(max_zao - min_zao <= 2))
            cons.append(m.addConstr(max_wu - min_wu <= 2))
            cons.append(m.addConstr(max_ye - min_ye <= 1))
            cons.append(m.addConstr(max_tiao - min_tiao <= 2))

            # consecutive WU ban less than 3 times
            for i in range(self.team_cnt):
                for t in range(self.sche_day_cnt-1):
                    s1 = quicksum(x[i, j, t] + x[i, j, t+1] for j in self.shift_type_compo[5])
                    cons.append(m.addConstr(cw[i, t] >= s1 - 1))
                    cons.append(m.addConstr(cw[i, t] <= 0.5 * s1))
                cons.append(m.addConstr(quicksum(cw[i, tw] for tw in range(self.sche_day_cnt-1)) <= 3))

            # ZAO+ZAO, ZHONG+ZAO, TIAO+ZAO, TIAO+CHEN are forbidden order
            for i in range(self.team_cnt):
                for t in range(self.sche_day_cnt-1):
                    cons.append(m.addConstr(quicksum(x[i, j, t] + x[i, j, t+1] for j in self.shift_type_compo[0]) <= 1))
                    s1 = quicksum(x[i, j, t] for j in self.shift_type_compo[0])
                    s2 = quicksum(x[i, j, t+1] for j in self.shift_type_compo[4])
                    cons.append(m.addConstr(s1 + s2 <= 1))
                    s3 = quicksum(x[i, j, t + 1] for j in self.shift_type_compo[3])
                    cons.append(m.addConstr(s1 + s3 <= 1))
                    s4 = quicksum(x[i, j, t] for j in self.shift_type_compo[3])
                    s5 = quicksum(x[i, j, t + 1] for j in self.shift_type_compo[1])
                    cons.append(m.addConstr(s4 + s5 <= 1))

                    # must rest after YE ban
                    s6 = quicksum(x[i, j, t] for j in self.shift_type_compo[6])
                    s7 = quicksum(x[i, j, t + 1] for j in range(self.shift_cnt))
                    cons.append(m.addConstr(s6 + s7 <= 1))

            # following 2 days restriction
            for i in range(self.team_cnt):
                for t in range(self.sche_day_cnt-2):
                    s_t = quicksum(x[i, j, t] for j in self.shift_type_compo[3])
                    s1 = quicksum(x[i, j, t+1] + x[i, j, t+2] for j in range(self.shift_cnt))
                    cons.append(m.addConstr(s_t + s1 <= 2))
                    s_w = quicksum(x[i, j, t] for j in self.shift_type_compo[5])
                    cons.append(m.addConstr(s_w + s1 <= 2))

                    # YE+rest+ZAO, YE+rest+CHEN are forbidden
                    s_y = quicksum(x[i, j, t] for j in self.shift_type_compo[6])
                    s_z = quicksum(x[i, j, t+2] for j in self.shift_type_compo[0])
                    s_c = quicksum(x[i, j, t+2] for j in self.shift_type_compo[1])
                    cons.append(m.addConstr(s_y + s_z <= 1))
                    cons.append(m.addConstr(s_y + s_c <= 1))

            # special requirements
            # 13:产险呼入06班 - WH, 9/14,9/15请假
            cons.append(m.addConstr(quicksum(x[13, j, 19] + x[13, j, 20] for j in range(self.shift_cnt)) <= 0))
            # 16:产险呼入10班 - WH, 9/12,9/13,9/14请假
            cons.append(m.addConstr(quicksum(x[16, j, 19] + x[16, j, 18] + x[16, j, 17] for j in range(self.shift_cnt)) <= 0))
            # 4:产险呼入02班 - SZ, 9/24,9/25请假
            cons.append(m.addConstr(quicksum(x[4, j, 29] + x[4, j, 30] for j in range(self.shift_cnt)) <= 0))

            for i in range(self.team_cnt):
                if i not in {4, 13, 16}:
                    for t in range(self.sche_day_cnt):
                        m.addConstr(x[i, self.shift_cnt-1, t] == 0)

            # m.write('crew_scheduling.lp')
            m.params.LogFile = 'grblog.log'
            m.params.LogToConsole = 1
            m.params.MIPFocus = 1
            m.params.TimeLimit = 1800
            m.params.MIPGap = 0.01
            m.optimize()

            solution_info = json.loads(m.getJSONSolution())
            print(solution_info)
            print('Optimization status: ', m.status)
            print('Objective Value: ', m.objVal)

            if m.SolCount > 0:
                for i in range(self.team_cnt):
                    for t in range(self.sche_day_cnt):
                        for j in range(self.shift_cnt):
                            if x[i, j, t].x == 1:
                                self.x_mat[i, t] = j
                                continue

        except GurobiError as e:
            print('Error: ', e)

    def write_x(self):
        """Write solved decision variable values to csv."""

        df_x = pd.DataFrame(self.x_mat)
        df_x.to_csv(r'C:\Bee\aHuaat\TP_crew_shift\result\solution.csv')

    def print_result(self):
        """Print scheduling result."""
        date0 = datetime.datetime(year=2019, month=8, day=26)
        result = [['team_id', 'team'] + [(date0 + datetime.timedelta(days=dt)).strftime("%Y/%m/%d") for dt in range(self.sche_day_cnt)]]
        for i in range(self.team_cnt):
            result_i = [i, self.team_info['team'][i]]
            for t in range(self.sche_day_cnt):
                if self.x_mat[i, t] == -1:
                    result_i.append('休息')
                else:
                    j = self.x_mat[i, t]
                    shift_ijt = str(j) + ', ' + str(self.shift_info['shift_type'][j]) + ', ' + str(
                        self.shift_info['shift_minute'][j]) + 'Min' + ', ' + str(self.shift_info['shift_time'][j])
                    result_i.append(shift_ijt)

            for ii in range(self.team_info['worker_cnt'][i]): result.append(result_i)

        with open(r'C:\Bee\aHuaat\TP_crew_shift\result\result.csv', 'w', newline='') as fw:
            writer = csv.writer(fw)
            for re in result:
                writer.writerow(re)


if __name__ == '__main__':
    # read_data()
    cs = CrewScheduling()
    cs.ip_model()
    if_write = False
    if if_write:
        cs.write_x()
        cs.print_result()







