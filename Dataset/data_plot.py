import csv
import matplotlib.pyplot as plt

class DemographicSnapshot:
    def __init__(self):
        self.country_name = ""
        self.country_code = ""
        
        self.populations = {}
        
    def get_highest_population(self):
        return max(self.populations.values())
        
    def get_lowest_population(self):
        return min(self.populations.values())

snapshots = {}
columns = []

with open("demographic.csv") as csvfile:
    rows = csv.reader(csvfile, delimiter=",")
    
    is_parsing_columns = True
    
    for row in rows:
        if is_parsing_columns:
            is_parsing_columns = False
            
            columns = row
        else:
            snapshot = DemographicSnapshot()
            
            snapshot.country_name = row[0]
            snapshot.country_code = row[1]
            
            for t in range(4, len(columns) - 1):
                if row[t]:
                    snapshot.populations[columns[t]] = int(row[t])
            
            snapshots[snapshot.country_code] = snapshot

target = snapshots["RUS"]

unit = 1000000

xPoints = [int(timepoint) for timepoint in target.populations.keys()]
yPoints = [int(population) / unit for population in target.populations.values()]

plt.xlim(xPoints[0], xPoints[-1:][0])
plt.ylim(target.get_lowest_population() / unit, target.get_highest_population() / unit)

plt.plot(xPoints, yPoints, color='r', label='Population')

plt.xlabel("Year")
plt.ylabel("Population (Millions)")

plt.title("Russia's Population over 61 year span")

plt.grid()
plt.legend()
plt.show()
