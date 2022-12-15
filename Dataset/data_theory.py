import pandas
import numpy

demographics = pandas.read_csv("demographic.csv")

meanWorldPopulationDeltas = {}
for year in range(1961, 2021):
  yearKey = str(year)
  previousYearKey = str(year - 1)

  meanWorldPopulationDeltas[yearKey] = demographics[yearKey].mean() - demographics[previousYearKey].mean()

meanWorldPopulationIncrease = numpy.mean(list(meanWorldPopulationDeltas.values()))
if meanWorldPopulationIncrease >= 3000000:
  print("World population increase per year (mean) is above 3 million, which is normal - %d." % meanWorldPopulationIncrease)
else:
  print("World population increase per year (mean) is below 3 million, which is too low - %d." % meanWorldPopulationIncrease)
