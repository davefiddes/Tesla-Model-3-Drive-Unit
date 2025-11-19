"""
Curve fitting for motor temperature sensor calibration

Based on python from https://github.com/fbaeuerlein/jupyter-steinhart-hart

Data comes from sandwiching a thermocouple between the motor sensor and a large
lump of mild steel. The mild steel was heated externally with a heat gun to
100 degrees then allowed to passively cool. Finally ice was placed on the steel
to get down to 0 degrees. The motor sensor resistance and thermocouple
temperature were recorded during the entire process.

"""

import csv

import matplotlib.pyplot as plt
import numpy
from scipy.optimize import curve_fit

x = []
y = []

print("Loading data...")
with open('active-heating-log.csv', newline='', encoding='utf-8') as csvfile:
    datareader = csv.DictReader(csvfile, delimiter=',')
    for row in datareader:
        x.append(float(row['Resistance'])*1000)  # resistance values in kOhm
        # convert temperature to absolute temperature
        y.append(float(row['Temp']) + 273.15)

with open('passive-cooling-log.csv', newline='', encoding='utf-8') as csvfile:
    datareader = csv.DictReader(csvfile, delimiter=',')
    for row in datareader:
        x.append(float(row['Resistance'])*1000)  # resistance values in kOhm
        # convert temperature to absolute temperature
        y.append(float(row['Temp']) + 273.15)

with open('active-cooling-log.csv', newline='', encoding='utf-8') as csvfile:
    datareader = csv.DictReader(csvfile, delimiter=',')
    for row in datareader:
        x.append(float(row['Resistance'])*1000)  # resistance values in kOhm
        # convert temperature to absolute temperature
        y.append(float(row['Temp']) + 273.15)

print("Sort the data by temperature")
xy = sorted(zip(x, y), key=lambda pair: pair[0])
x, y = zip(*xy)


def steinhart_hart(R, A, B, C):
    """
    Steinhart-Hart equation to get temperature from resistance

    Details from https://en.wikipedia.org/wiki/Steinhart%E2%80%93Hart_equation
    """
    return 1. / (A + B * numpy.log(R) + C * numpy.power(numpy.log(R), 3))


def inverse_steinhart_hart(T, A, B, C):
    """
    Inverse Steinhart-Hart equation to get resistance from temperature
    """
    x0 = (1./C)*(A - (1./T))
    y0 = numpy.sqrt((B/(3*C))**3 + x0**2/4)
    R = numpy.exp(numpy.cbrt(y0-x0/2)-numpy.cbrt(y0+x0/2))
    return R


# Do the fit with initial values (needed, otherwise no meaningful result)
print("Fitting data...")
params, cov = curve_fit(steinhart_hart, x, y, p0=[1e-4, 1e-4, 1e-4])

print("Coefficients: ")
for i, c in enumerate(params):
    print("a[{}] = {}".format(i, c))

print("Plotting results. Close plots to continue...")

y2 = []
for v in x:
    y2.append(steinhart_hart(v, params[0], params[1], params[2]))

ax, fig = plt.subplots()
# plot original data and result
fig.plot(x, y, color="b")
fig.plot(x, y2, color="r")
plt.xlabel("R [Ω]")
plt.ylabel("T [°K]")
plt.grid()
plt.show(block=False)

ax, fig = plt.subplots()
plt.plot(x, numpy.abs(numpy.subtract(y, y2)))  # error values
plt.xlabel("R [Ω]")
plt.ylabel("Error [°K]")
plt.grid()
plt.show()

print("Writing fit results to fit_results.csv...")

with open('fit_results.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Temp', 'Resistance'])
    for T in range(-40, 125, 5):
        # convert back to Celsius and kOhm
        writer.writerow([T, inverse_steinhart_hart(
            T+273.15, params[0], params[1], params[2])/1000])
