import csv
import datetime

with open('AccountHistory.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    transactions = []
    for row in reader:
        row['PythonDate'] = datetime.datetime.strptime(row['Date'], '%m/%d/%Y').date()
        transactions.append(row)

withdrawals = 0.0
savings = 0.0
credits = 0.0

# FILTERING
today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=30)
print('Filtering to: {}'.format(lastMonth))

def filter_this_month(t):
    return t['PythonDate'] > lastMonth

transactions = list(filter(filter_this_month, transactions))

# SUMMING THE DATA
for t in transactions:
    description = t['Description']
    if 'Coinbase' in description or 'ealthfront' in description:
        savings = savings + abs(float(t['Debit']))
    elif t['Debit'] and float(t['Debit']) < 0:
        withdrawals = withdrawals + float(t['Debit'])
    else:
        credits = credits + float(t['Credit'])

# TOTALS
balance = withdrawals + credits
true_savings = savings + balance

print('withdrawals: {}\ncredits: {}\nsavings: {} ({}%)'.format(int(withdrawals),int(credits),int(true_savings), int(100*true_savings/credits)))

# CATEGORIES
categories_map = {}
for t in transactions:
    cat = t['Category']
    val = abs(int(float(t['Debit']))) if t['Debit'] else 0
    if cat not in categories_map:
        categories_map[cat] = 0
    categories_map[cat] = categories_map[cat] + val
print(categories_map)


# PLOTTINGx
def plot_categories():
    import matplotlib.pyplot as plt

    labels = []
    sizes = []

    for x, y in categories_map.items():
        labels.append(x)
        sizes.append(y)

    # Plot
    plt.pie(sizes, labels=labels)

    plt.axis('equal')
    plt.show()

plot_categories()

# print(transactions[0])

# # Time series data source: fpp pacakge in R.
# import pandas as pd
# import matplotlib.pyplot as plt
# df = pd.read_csv('AccountHistory.csv', parse_dates=['Date'], index_col='Date')
# df_filter = df[(df.Debit >= -40000) & ('Coinbase' in df['Description'])]

# # Draw Plot
# def plot_df(df, x, y, title="", xlabel='Date', ylabel='Value', dpi=100):
#     plt.figure(figsize=(16,5), dpi=dpi)
#     plt.plot(x, y, color='tab:red')
#     plt.gca().set(title=title, xlabel=xlabel, ylabel=ylabel)
#     plt.show()

# plot_df(df_filter, x=df_filter.index, y=df_filter.Debit, title='Withdrawals') 