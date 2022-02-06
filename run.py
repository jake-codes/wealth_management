import csv
import datetime
import glob
import pdb
import yaml


def load_transformations():
    with open("transformations.yml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def normalize_transaction(ts, isChase):
    date = ts['Date'] if not isChase else ts['Transaction Date']
    description = ts['Description']
    ts['PythonDate'] = datetime.datetime.strptime(date, '%m/%d/%Y').date()
    ts['ID'] = ts['Transaction Number'] if not isChase else '{}.{}.{}'.format(date, description, ts['Amount'])

    savings = 0
    debit = 0
    credit = 0

    if isChase:
        debit = abs(float(ts['Amount']))
    else:
        if ('Coinbase' in description or 'ealthfront' in description or 'Internet Transfer to Loan' in description):
            savings = abs(float(ts['Debit']))
        else:
            debit = abs(float(ts['Debit'])) if len(ts['Debit']) and abs(float(ts['Debit'])) > 0 else 0
            credit = abs(float(ts['Credit'])) if debit == 0 and len(ts['Credit']) and abs(float(ts['Credit'])) > 0 else 0

    ts['Saving'] = savings
    ts['Expense'] = debit
    ts['Paycheck'] = credit

    # if 'ealthfront' in description:
    #     pdb.set_trace()

    return (ts, savings)

def filters(ts, MAX_AMOUNT_FILTER = 9000):
    return ts['Expense'] < MAX_AMOUNT_FILTER and ts['Paycheck'] < MAX_AMOUNT_FILTER and 'credit card payment' not in ts['Category'].lower() and ts['PythonDate'] > datetime.datetime(2021, 7, 1).date()


def load_transaction_csv(filename, isChase=False):
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        transactions = []
        for row in reader:
            ts, savings = normalize_transaction(row, isChase)
            transactions.append(ts)
            # if savings:
            #     print(ts)
            #     print(sum([x['Saving'] for x in transactions]))
        return transactions

def load_transactions():
    csvFilenamesList = glob.glob('*.csv')
    transactions = []
    for filename in csvFilenamesList:
        isChase = 'chase' in filename.lower()
        transactions = transactions + load_transaction_csv(filename, isChase)
        # transactions = load_transaction_csv('AccountHistory.csv') + load_transaction_csv('Chase_jake.csv', isChase=True)
    return transactions

def filter_this_month(t):
    today = datetime.date.today()
    first = today.replace(day=1)
    lastMonth = first - datetime.timedelta(days=30)
    return t['PythonDate'] > lastMonth

def apply_filters(transactions):
    # transactions = list(filter(filter_this_month, transactions))
    return list(filter(filters, transactions))

def get_sums(transactions):
    expenses = sum([x['Expense'] for x in transactions])
    paychecks = sum([x['Paycheck'] for x in transactions])
    savings = sum([x['Saving'] for x in transactions])

    balance = paychecks - expenses
    true_savings = savings - balance
    true_savings_percent = 0 if paychecks == 0 else round(100*true_savings/paychecks)

    return (expenses, paychecks, savings, balance, true_savings, true_savings_percent)

def build_category_map(transactions):
    transformations = load_transformations()
    # CATEGORIES
    categories_map = {}
    expenses = list(filter(lambda x: x['Expense'] > 0, transactions))
    for t in expenses:
        cat = t['Category']
        if not cat:
            cat = 'Uncategorized'

        cat = transformations['categories'][cat] if cat in transformations['categories'] else cat
        val = abs(int(float(t['Expense']))) if t['Expense'] else 0

        if cat not in categories_map:
            categories_map[cat] = 0
        categories_map[cat] = categories_map[cat] + val

    cat_list = list(categories_map.items())
    cat_list.sort(reverse=True, key=lambda x: x[1])
    return categories_map, cat_list


# PLOTTINGx
def plot_categories(category_map):
    import matplotlib.pyplot as plt

    labels = []
    sizes = []

    for x, y in category_map.items():
        labels.append(x)
        sizes.append(y)

    # Plot
    plt.pie(sizes, labels=labels)

    plt.axis('equal')
    plt.show()

def print_category(category, transactions):
    cat_transactions = [x for x in transactions if x['Category'] == category]
    for x in cat_transactions:
        print('{}: {}'.format(x['Description'], x['Expense']))

if __name__ == '__main__':
    transactions = load_transactions()
    transactions = apply_filters(transactions)

    category_map, category_list = build_category_map(transactions)

    (expenses, paychecks, savings, balance, true_savings, true_savings_percent) = get_sums(transactions)

    print('Expenses: {}\nPaychecks: {}\nSavings: {} ({}%)\n'.format(int(expenses),int(paychecks),int(true_savings), int(true_savings_percent)))

    print('Categories:\n{}\n'.format(category_list))

    print('Personal Transactions:')
    print_category('Personal', transactions)

    plot_categories(category_map)

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