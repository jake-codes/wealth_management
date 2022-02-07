import csv
import datetime
import glob
import pdb
import yaml

import matplotlib.pyplot as plt


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

    debit = 0
    credit = 0

    if isChase:
        debit = abs(float(ts['Amount'])) if float(ts['Amount']) < 0.0 else 0
    else:
        debit = abs(float(ts['Debit'])) if len(ts['Debit']) and abs(float(ts['Debit'])) > 0  else 0
        credit = abs(float(ts['Credit'])) if debit == 0 and len(ts['Credit']) and abs(float(ts['Credit'])) > 0  else 0

    ts['Expense'] = debit
    ts['Paycheck'] = credit

    # if 'ealthfront' in description:
    #     pdb.set_trace()

    return ts

def filters(ts, filters_, MAX_AMOUNT_FILTER = 9000):
    for f, key in filters_.items():
        if f.lower() in ts[key].lower():
            return False
    return ts['Expense'] < MAX_AMOUNT_FILTER and ts['Paycheck'] < MAX_AMOUNT_FILTER and 'credit card payment' not in ts['Category'].lower() and ts['PythonDate'] > datetime.datetime(2021, 7, 1).date()


def load_transaction_csv(filename, isChase=False):
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        transactions = []
        for row in reader:
            ts = normalize_transaction(row, isChase)
            transactions.append(ts)
        return transactions

def load_transactions():
    csvFilenamesList = glob.glob('*.csv')
    print('csvFilenamesList: {}'.format(csvFilenamesList))
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
    filters_ = load_transformations()['filters']
    return list(filter(lambda t: filters(t, filters_), transactions))

def get_sums(transactions):
    expenses = sum([x['Expense'] for x in transactions if not 'Savings' in x['Category'] ])
    paychecks = sum([x['Paycheck'] for x in transactions])
    savings = sum([x['Expense'] for x in transactions if 'Savings' in x['Category']])
    savings_percent = 0 if paychecks == 0 else round(100*savings/paychecks)

    balance = abs(paychecks) - abs(expenses)
    true_savings = abs(savings) - balance
    true_savings_percent = 0 if paychecks == 0 else round(100*true_savings/paychecks)

    print('Expenses: {}\nPaychecks: {}\nSavings: {} ({}%)\nTrue Savings: {} ({}%)\n'.format(int(expenses),int(paychecks),int(savings), int(savings_percent),int(true_savings), int(true_savings_percent)))

    return (expenses, paychecks, savings, balance, true_savings, true_savings_percent)


def transform_categories(transactions):
    transformations = load_transformations()
    for t in transactions:
        if abs(float(t['Expense'])) > 0:
            cat = t['Category'] if t['Category'] else 'Uncategorized'
            category_transformed = False
            for desc_key, cat_val in transformations['descriptions'].items():
                if desc_key.lower() in t['Description'].lower():
                    cat = cat_val
                    category_transformed = True
                if not category_transformed:
                    cat = transformations['categories'][cat] if cat in transformations['categories'] else cat
            t['Category'] = cat

    return transactions

def sum_categories(transactions, total_expenses):
    # CATEGORIES
    categories_map = {}
    expenses = list(filter(lambda x: x['Expense'] > 0, transactions))
    for t in expenses:
        cat = t['Category']
        if cat not in categories_map:
            categories_map[cat] = {"amount": 0, "%": 0}
        val = abs(int(float(t['Expense']))) if t['Expense'] else 0
        categories_map[cat]['amount'] = val if cat not in categories_map else categories_map[cat]['amount'] + val
        categories_map[cat]['%'] = round(100.0*categories_map[cat]['amount']/total_expenses)

    return categories_map


# PLOTTINGx

def plot_table(category_map):
    print('\nPlotting table')
    # pdb.set_trace()
    table_data = list([[x[0],x[1]['%'],  x[1]['amount']] for x in category_map.items()])
    # pdb.set_trace()
    table_data.sort(key=lambda x: x[2], reverse=True)
    # cols = ['Categories', 'Amounts']
    # rows = [x[0] for x in table_data]
    
    fig, ax = plt.subplots()
    # ax.set_axis_off()
    table = ax.table(
        cellText = table_data,
        loc ='center'
    )
    # table.set_fontsize(14)
    # table.scale(1,4)
    ax.axis('off')
    plt.show()

def plot_categories(category_map):

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
        print('{}: -{} +{}'.format(x['Description'], x['Expense'], x['Paycheck']))

if __name__ == '__main__':
    transactions = load_transactions()
    transactions = apply_filters(transactions)
    transactions = transform_categories(transactions)

    (expenses, paychecks, savings, balance, true_savings, true_savings_percent) = get_sums(transactions)

    category_map = sum_categories(transactions, expenses)

    for category in category_map:
        print('\n---------------')
        print('{} Transactions:'.format(category))
        print('---------------\n')
        print_category(category, transactions)

    # plot_categories(category_map)

    plot_table(category_map)
