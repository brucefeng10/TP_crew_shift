## Customer service staff scheduling:

### 问题:

- 客服人员排班问题，主要要考虑公平性
- 建立整数规划模型
- 模型重建：可将休息当成一种特殊的班次，工作时间为0

### data:

- call_demand.csv: 排班周期内每一天每半小时时间点客服需求（通过预测话务量计算）

- pre_shift.csv: 排班周期前五天的排班情况，过渡阶段

- team_info.csv: 人力班组信息，包含班组名称，班组人数

- shift_info.csv: 可执行班次信息，包括班次上班下班时间，工作时长，班次的类型，班次所覆盖的需求点

- night_shift_info.csv: 夜班信息，同上，夜班存在跨天情况，特殊考虑

### modeling:

#### notes:

$i$: 班组，$I$

$j$: 班次，$J$

$t$: 考勤天，$T$

$k$: 需求时间点， $K$

$sn_{i}$: staff number, 班组$i$包含人员数量

$sd_{j}$: shift duration, 班次$j$的工时

$start_j$: start time，班次$j$的开始时间

$end_j$: end time，班次$j$的结束时间，夜班结束时间+24h

$dem^{t}_{k}$: demand, 第$t$第$k$个时间点的话务需求量

$cov_{jk}$: 0-1，班次$j$是否覆盖当天的时间点$k$，统一认为时间段7:00-8:00覆盖时间点7:00和7:30，不覆盖时间点8:00

$cov^{eve}_{jk}$: 0-1，夜班$j$是否覆盖次日时间点$k$

$k_J$: 覆盖需求时间点$k$的班次集合

$shift\_type: [ZAO, CHEN, BAI, TIAO, ZHONG, WU, WAN]$: 0早，1晨，2白，3跳，4中，5午，6晚

$weekend\_t: [5,6,12,13,19,20,26,27]$: [8/31,9/1,9/8,9/8,9/15,9/16,9/22,9/23]

$cons\_work\_lmt$: 最多连续上班天数，6天

$max\_ye\_gap$: 两个夜班之间最小间隔天数，10天

$max\_tiao\_gap$: 两个跳班之间最小间隔天数，3天

$shift\_min\_gap$: 每人两个班次的最小时间间隔，10小时

$weekend\_rest\_cnt$: 周末最少休息次数，1次

#### decision variables:

$x^{t}_{ij}$: 0- 1变量，当班组$i$在第$t$天执行班次$j$时取值1，否则取值0

#### auxiliary variables:

$max\_work$: 考勤周期内所有班组的最大工作天数

$min\_work$: 考勤周期内所有班组的最小工作天数

$max\_minute$: 考勤周期内所有班组的最大工作小时数

$min\_minute$: 考勤周期内所有班组的最小工作小时数

$max\_zao$: 考勤周期内所有班组执行早班最多次数

$min\_zao$: 考勤周期内所有班组执行早班最小次数

$max\_wu$: 考勤周期内所有班组执行午班最多次数

$min\_wu$: 考勤周期内所有班组执行午班最小次数

$max\_ye$: 考勤周期内所有班组执行夜班最多次数

$min\_ye$: 考勤周期内所有班组执行夜班最小次数

$max\_tiao$: 考勤周期内所有班组执行跳班最多次数

$min\_tiao$: 考勤周期内所有班组执行跳班最小次数

$ct^t_i$: 0-1，班组$i$是否在第$t$和第$t+1$天均休息（连续两天休息），均休息取1，否则取0

$cw^t_i$: 0-1，班组$i$是否在第$t$和第$t+1$天均上午班（连续两天午班，其他同理），均休息取1，否则取0



#### model:

$$max\ work\_time=\sum_t\sum_i\sum_jsn_i*sd_j*x^t_{ij}$$

$$s.t.$$

$$\sum_i\sum^{k_J}_jsn_i*cov_{jk}*x^t_{ij}+\sum_isn_i*cov^{eve}_{jk}*x^{t-1}_{i6} \ge dem^t_k,\  \forall k,t$$  (1)时间点需求满足

$$\sum_ix^t_{ij} \le 1,\  \forall i,t$$  (2)每个班组每天最多执行一个班次

$$\sum_t\sum_jx^t_{ij} \le 24, \ \forall i$$  (3)考勤周期内最多工作24天

$$max\_work \ge \sum_t\sum_jx^t_{ij},\ \forall i$$

$$min\_work \le \sum_t\sum_jx^t_{ij},\ \forall i$$

$$max\_work-min\_work \le 1$$  最多最少上班天数不超过1

$$max\_minute \ge \sum_t\sum_j sd_jx^t_{ij},\ \forall i$$

$$min\_minute \le \sum_t\sum_j sd_jx^t_{ij},\ \forall i$$

$$max\_minute-min\_minute \le 8*60$$  最多最少上班工时不超过8h

$$\sum^{t_c+cons\_work\_lmt+1}_{t=t_c}\sum_jx^t_{ij} \le cons\_work\_lmt,\ \forall i,t_c\in T-cons\_work\_lm$$  最大连续工作天数

$$\sum_jx^{t+1}_{ij} \ge 1/2*(1-\sum_jx^{t}_{ij}),\ \forall i,t\in T-1$$  不能连续两天休息

$$\sum_jx^{t+2}_{ij} \ge 1/2*(1-\sum_jx^{t}_{ij}),\ \forall i,t\in T-2$$  不能只工作一天就休息，即休息日的第三天不休息

$$\sum^{t_y+max\_ye\_gap+1}_{t=t_y}\sum^{YE}_jx^t_{ij} \le 1,\ \forall i,t_y \in T-max\_ye\_gap$$  每两个夜班之间最小间隔天数，此约束与下面约束等同

($$1-\sum^{YE}_jx^t_{ij} \ge \sum^{YE}_jx^{t+m}_{ij},\ \forall i,t\in T,m\le max\_ye\_gap$$)

$$\sum^{t_t+max\_tiao\_gap+1}_{t=t_t}\sum^{TIAO}_jx^t_{ij} \le 1,\ \forall i,t_t \in T-max\_tiao\_gap$$  每两个跳班之间最小间隔天数，此约束与下面约束等同

($$1-\sum^{TIAO}_jx^t_{ij} \ge \sum^{TIAO}_jx^{t+m}_{ij},\ \forall i,t\in T-max\_tiao\_gap,m\le max\_tiao\_gap$$)

$$\sum_jend_j*x^t_{ij}+shift\_min\_gap*60*\sum_jx^{t+1}_{ij} \le \sum_jstart_j*x^{t+1}_{ij}+24*60,\ \forall i,t\in T-1$$  两个班次最小时间间隔，考虑到“班+班”、“班+休”、“休+班”三种情况，夜班结束时间需+24h

$$\sum^{weekend\_t}_t\sum_jx^t_{ij} \ge weekend\_rest\_cnt,\ \forall i$$  周末最少休息次数

$$\sum_t\sum^{YE}_jx^t_{ij} \le 2, \forall i$$  每人总夜班次数限制

$$\sum_t\sum^{TIAO}_jx^t_{ij} \le 4, \forall i$$  每人总跳班次数限制

$$\sum_t\sum^{WU}_jx^t_{ij} \le 4, \forall i$$  每人总午班次数限制

$$max\_zao \ge \sum_t\sum^{ZAO}_jx^t_{ij},\ \forall i$$

$$min\_zao \le \sum_t\sum^{ZAO}_jx^t_{ij},\ \forall i$$

$$max\_zao-min\_zao \le 2$$  早班次数差距限制2（4-6次）

$$max\_wu \ge \sum_t\sum^{WU}_jx^t_{ij},\ \forall i$$

$$min\_wu \le \sum_t\sum^{WU}_jx^t_{ij},\ \forall i$$

$$max\_wu-min\_wu \le 1$$  午班次数差距限制1（2-3次）

$$max\_ye \ge \sum_t\sum^{YE}_jx^t_{ij},\ \forall i$$

$$min\_ye \le \sum_t\sum^{YE}_jx^t_{ij},\ \forall i$$

$$max\_ye-min\_ye \le 1$$  夜班次数差距限制1（1-2次）

$$max\_tiao \ge \sum_t\sum^{TIAO}_jx^t_{ij},\ \forall i$$

$$min\_tiao \le \sum_t\sum^{TIAO}_jx^t_{ij},\ \forall i$$

$$max\_tiao-min\_tiao \le 1$$  跳班次数差距限制1（2-3次）

($$ct^t_i \ge 1-(\sum_jx^t_{ij}+\sum_jx^{t+1}_{ij}),\ \forall i,t \in T-1$$)

($$ct^t_i \le 1-1/2*(\sum_jx^t_{ij}+\sum_jx^{t+1}_{ij}),\ \forall i,t \in T-1$$)

$$cw^t_i \ge \sum^{WU}_jx^t_{ij}+\sum^{WU}_jx^{t+1}_{ij}-1,\ \forall i,t \in T-1$$

$$cw^t_i \le 1/2*(\sum^{WU}_jx^t_{ij}+\sum^{WU}_jx^{t+1}_{ij}),\ \forall i,t \in T-1$$

$$\sum^{T-1}_t cw^t_i \le 3, \ \forall i$$  连续午班小于3次，（连续跳班小于3次同理）

$$1-\sum^{ZAO}_j x^t_{ij} \ge \sum^{ZAO}_j x^{t+1}_{ij},\ \forall i,t \in T-1$$  早班后不接早班

$$1-\sum^{ZAO}_j x^t_{ij} \ge \sum^{ZHONG}_j x^{t+1}_{ij},\ \forall i,t \in T-1$$  中班后不接早班

$$1-\sum^{ZAO}_j x^t_{ij} \ge \sum^{TIAO}_j x^{t+1}_{ij},\ \forall i,t \in T-1$$  跳班后不接早班

$$1-\sum^{TIAO}_j x^t_{ij} \ge \sum^{CHEN}_j x^{t+1}_{ij},\ \forall i,t \in T-1$$  跳班后不接晨班

$$1-\sum^{TIAO}_j x^t_{ij} \ge \sum_j x^{t+1}_{ij} + \sum_j x^{t+2}_{ij} -1,\ \forall i,t \in T-2$$  跳班后第二天不休息则第三天必休息

$$1-\sum^{WU}_j x^t_{ij} \ge \sum_j x^{t+1}_{ij} + \sum_j x^{t+2}_{ij} -1,\ \forall i,t \in T-2$$  午班后第二天不休息则第三天必休息

$$1-\sum^{YE}_j x^t_{ij} \ge \sum_j x^{t+1}_{ij},\ \forall i,t \in T-1$$  夜班后必须接休息

$$1-\sum^{YE}_j x^t_{ij} \ge \sum^{ZAO}_j x^{t+2}_{ij},\ \forall i,t \in T-2$$  夜班休息后不接早班

$$1-\sum^{YE}_j x^t_{ij} \ge \sum^{CHEN}_j x^{t+2}_{ij},\ \forall i,t \in T-2$$  夜班休息后不接晨班

$$x^t_{ij},ct^t_i,cw^t_i \in {0,1}$$

$$other\ variables \in Integer$$







 