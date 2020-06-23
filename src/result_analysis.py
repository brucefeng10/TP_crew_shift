import csv
import datetime
import numpy as np
import pandas as pd
from crew_scheduling import read_data


sol = pd.read_csv(r'C:\Bee\aHuaat\TP_crew_shift\result\solution.csv', header=0, index_col=0)
sol = sol.values
team_cnt, day_cnt = sol.shape
print(team_cnt, day_cnt)
sh_team = [0, 3, 6, 22]  # team id of sh
sz_team = [1, 4, 7, 9, 11]
sh_team_cnt, sz_team_cnt, wh_team_cnt = len(sh_team), len(sz_team), team_cnt-len(sh_team)-len(sz_team)
sh_worker_cnt, sz_worker_cnt, wh_worker_cnt = 37, 56, 212
shift_type_dict = {-1: 'xiuxi', 0: 'zaoban', 1: 'chenban', 2: 'baiban', 3: 'tiaoban', 4: 'zhongban', 5: 'wuban', 6: 'wanban'}

team_info, shift_info, shift_cover, night_shift_info, call_dem = read_data()


def summary():
    """Summary of each area."""

    sh_hour, sz_hour, wh_hour = 0, 0, 0
    sh_shift_cnt, sz_shift_cnt, wh_shift_cnt = [{-1: 0, 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0} for i in range(3)]
    sh_shift_hr, sz_shift_hr, wh_shift_hr = [{-1: 0, 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0} for j in range(3)]
    for i in range(team_cnt):
        for t in range(day_cnt):
            if i in sh_team:
                if sol[i, t] == -1:
                    sh_shift_cnt[-1] += team_info['worker_cnt'][i]
                else:
                    sh_hour += shift_info['shift_minute'][sol[i, t]] / 60
                    sh_shift_cnt[shift_info['shift_type_id'][sol[i, t]]] += team_info['worker_cnt'][i]
                    sh_shift_hr[shift_info['shift_type_id'][sol[i, t]]] += team_info['worker_cnt'][i] * shift_info['shift_minute'][sol[i, t]] / 60
            elif i in sz_team:
                if sol[i, t] == -1:
                    sz_shift_cnt[-1] += team_info['worker_cnt'][i]
                else:
                    sz_hour += shift_info['shift_minute'][sol[i, t]] / 60
                    sz_shift_cnt[shift_info['shift_type_id'][sol[i, t]]] += team_info['worker_cnt'][i]
                    sz_shift_hr[shift_info['shift_type_id'][sol[i, t]]] += team_info['worker_cnt'][i] * \
                                                                           shift_info['shift_minute'][sol[i, t]] / 60
            else:
                if sol[i, t] == -1:
                    wh_shift_cnt[-1] += team_info['worker_cnt'][i]
                else:
                    wh_hour += shift_info['shift_minute'][sol[i, t]] / 60
                    wh_shift_cnt[shift_info['shift_type_id'][sol[i, t]]] += team_info['worker_cnt'][i]
                    wh_shift_hr[shift_info['shift_type_id'][sol[i, t]]] += team_info['worker_cnt'][i] * \
                                                                           shift_info['shift_minute'][sol[i, t]] / 60

    sumy = [['运营区', '平均工时(小时)', '休息', '早班', '晨班', '白班', '跳班', '中班', '午班', '夜班'], ['SH'], ['SZ'], ['WH']]

    # shanghai
    ave_work_hr = round(sh_hour/sh_team_cnt, 2)  # 平均工作小时
    sumy[1].append(ave_work_hr)
    xiuxi = '总数=%s(次)平均=%s(次)' % (sh_shift_cnt[-1], round(sh_shift_cnt[-1]/sh_worker_cnt, 2))
    sumy[1].append(xiuxi)
    for i in range(7):
        if sh_shift_cnt[i] > 0:
            ban = '总数=%s(次)平均=%s(次)平均时长=%s(小时)' % (sh_shift_cnt[i], round(sh_shift_cnt[i] / sh_worker_cnt, 2), round(sh_shift_hr[i] / sh_shift_cnt[i], 2))
        else:
            ban = '总数=%s(次)平均=%s(次)平均时长=%s(小时)' % (0, 0, 0)
        sumy[1].append(ban)

    # shenzhen
    ave_work_hr = round(sz_hour / sz_team_cnt, 2)  # 平均工作小时
    sumy[2].append(ave_work_hr)
    xiuxi = '总数=%s(次)平均=%s(次)' % (sz_shift_cnt[-1], round(sz_shift_cnt[-1] / sz_worker_cnt, 2))
    sumy[2].append(xiuxi)
    for i in range(7):
        if sz_shift_cnt[i] > 0:
            ban = '总数=%s(次)平均=%s(次)平均时长=%s(小时)' % (
            sz_shift_cnt[i], round(sz_shift_cnt[i] / sz_worker_cnt, 2), round(sz_shift_hr[i] / sz_shift_cnt[i], 2))
        else:
            ban = '总数=%s(次)平均=%s(次)平均时长=%s(小时)' % (0, 0, 0)
        sumy[2].append(ban)

    # shanghai
    ave_work_hr = round(wh_hour / wh_team_cnt, 2)  # 平均工作小时
    sumy[3].append(ave_work_hr)
    xiuxi = '总数=%s(次)平均=%s(次)' % (wh_shift_cnt[-1], round(wh_shift_cnt[-1] / wh_worker_cnt, 2))
    sumy[3].append(xiuxi)
    for i in range(7):
        if wh_shift_cnt[i] > 0:
            ban = '总数=%s(次)平均=%s(次)平均时长=%s(小时)' % (
            wh_shift_cnt[i], round(wh_shift_cnt[i] / wh_worker_cnt, 2), round(wh_shift_hr[i] / wh_shift_cnt[i], 2))
        else:
            ban = '总数=%s(次)平均=%s(次)平均时长=%s(小时)' % (0, 0, 0)
        sumy[3].append(ban)

    with open(r'C:\Bee\aHuaat\TP_crew_shift\result\analysis\summ.csv', 'w', newline='') as fw:
        writer = csv.writer(fw)
        for v in sumy:
            writer.writerow(v)


summary()


def demand_cover():
    """Demand cover of each time point."""

    date0 = datetime.datetime(year=2019, month=8, day=26)
    date_col = []
    time_col = [(date0 + datetime.timedelta(minutes=30*i)).strftime("%H:%M") for i in range(48)] * day_cnt

    for t in range(day_cnt):
        date_col += [(date0 + datetime.timedelta(days=t)).strftime("%Y/%m/%d")] * 48
        day_cover = np.zeros(48)
        for i in range(team_cnt):
            if sol[i, t] > -1:
                st = int(sol[i, t])
                day_cover += shift_cover[st] * team_info['worker_cnt'][i]
        if t == 0:
            cover_num = day_cover
        else:
            cover_num = np.append(cover_num, day_cover)

    demand_num = call_dem[:, 0]
    for t in range(1, day_cnt):
        demand_num = np.append(demand_num, call_dem[:, t])

    diff_num = cover_num - demand_num

    demand_cv = {'date': date_col,
                 'time_pt': time_col,
                 'demand': list(demand_num),
                 'cover': list(cover_num),
                 'difference': list(diff_num)}
    data = pd.DataFrame(demand_cv)
    data.to_csv(r'C:\Bee\aHuaat\TP_crew_shift\result\analysis\demand_cover.csv', index=False)


demand_cover()


