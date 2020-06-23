import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn import datasets, linear_model, metrics
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression


data = pd.read_csv(r'C:\Bee\aHuaat\Coal_Blending\reports\coke_quality\mixed_coal_quality400.csv', encoding='gbk')


X = data[['A.d', 'V.daf', 'G值', 'Y值']]
y_csr = data[['CSR']]
y_cri = data[['CRI']]


print(X.shape)


X_train, X_test, y_train, y_test = train_test_split(X, y_csr, random_state=1)
# X_train, y_train = X, y_csr

linreg = LinearRegression()
linreg.fit(X_train, y_train)

print(linreg.intercept_)
print(linreg.coef_)

y_pred = linreg.predict(X_test)

print('MSE: ', metrics.mean_squared_error(y_test, y_pred))
print('RMSE: ', np.sqrt(metrics.mean_squared_error(y_test, y_pred)))
print('MAE: ', metrics.mean_absolute_error(y_test, y_pred))


ad, vdaf, g_value, y_value = 9.63, 31.09, 72, 12.5

cri = 0.92438328 * ad + 0.81488584 * vdaf + 0.00132951 * g_value + 0.94157372 * y_value - 16.11946182
csr = -2.18780194 * ad - 1.25916360 * vdaf - 0.00215018382 * g_value - 1.22897502 * y_value + 137

print('CRI', cri)
print('CSR', csr)


