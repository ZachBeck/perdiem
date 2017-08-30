import json
from bs4 import BeautifulSoup
from bs4 import element
import requests
import csv
from datetime import datetime
import re
import random
import time


ZIP_MATCHER = re.compile(r'\d{5}($|(-\d{4}))')

RECORD_CATEGORIES = {
    'TWO_TABLE': 'TWO_TABLE'
}


RATES_2017 = 'rates_2017.json'
TABLES_2017 = 'gsa_tables_2017.json'

RATE_DATE_FORMAT = '%Y-%m'

RATE_DATES = ['2016-10', '2016-11', '2016-12',
              '2017-01', '2017-02', '2017-03',
              '2017-04', '2017-05', '2017-06',
              '2017-07', '2017-08', '2017-09']


FISCAL_YEARS = {
    '2017': (datetime.strptime('10/01/2016', '%m/%d/%Y'), datetime.strptime('9/30/2017', '%m/%d/%Y')),
    '2016': (datetime.strptime('10/01/2015', '%m/%d/%Y'), datetime.strptime('9/30/2016', '%m/%d/%Y'))
}


def save_tables(table, json_path=RATES_2017):
    with open(json_path, 'w') as f_out:
        f_out.write(json.dumps(table, sort_keys=True, indent=4))


def load_tables(json_path=RATES_2017):
    with open(json_path, 'r') as json_file:
        rate_tables = json.load(json_file)

    return rate_tables


def parse_gsa_table(rate_key, tbody_text):
    record = None
    if len(tbody_text) == 15:
        record = make_table_record(rate_key, tbody_text)
    elif len(tbody_text) == 30:
        record1 = make_table_record(rate_key, tbody_text[:15])
        record2 = make_table_record(rate_key, tbody_text[:30])
        if sum(record1['rates'].values()) > sum(record2['rates'].values()):
            record = record1
        else:
            record = record2
        record['category'] = RECORD_CATEGORIES['TWO_TABLE']

    return record


def make_table_record(rate_key, tbody_text):
    record = {
        rate_key: {
            'destination': tbody_text[0],
            'county': tbody_text[1],
            'rates': None
        }
    }
    rates = tbody_text[2:-1]
    if len(rates) != 12:
        raise ValueError('Where are all the rates!!!')
    rates = dict(zip(RATE_DATES, [int(r.replace('$', '').strip()) for r in rates]))
    record[rate_key]['rates'] = rates

    return record


def get_rate_key(state, city, zipcode):
    rate_key = '{}:{}'.format(state.lower(), city.lower() + str(zipcode))
    return rate_key


def get_perdiem_table(state, city, zipcode, previous_tables, gsa_multitables):
    apiCheck_Url = "https://www.gsa.gov/portal/category/100120"
    payload = {
        'perdiemSearchVO.year': '2017',
        'resultName': 'getPerdiemRatesBySearchVO',
        'currentCategory.categoryId': '100120',
        'perdiemSearchVO.state': state.lower(),
        'perdiemSearchVO.city': city.lower(),
        'perdiemSearchVO.zip': zipcode
    }

    rate_key = get_rate_key(state, city, zipcode)
    if rate_key in previous_tables:
        return previous_tables[rate_key]
    elif rate_key in gsa_multitables:
        return None

    time.sleep(random.uniform(2.0, 5.0))
    r = requests.post(apiCheck_Url, params=payload)
    page = None

    try:
        page = BeautifulSoup(r.content, 'html.parser')
    except:
        print "Error: Service did not respond."
    error_divs = page.find_all('div', {'class': 'error-text-body'})
    if len(error_divs) > 0:
        error_tag = error_divs[0].find_all('h3')
        error_text = ''
        if error_tag is not None and type(error_tag) == element.ResultSet:
            error_text = error_tag[0].text

        print 'Error:', error_text
        return None
    tbody_text = [e.get_text() for e in page.find_all('tbody')[0].find_all('td')]
    try:
        table_record = parse_gsa_table(rate_key, tbody_text)
    except ValueError:
        print 'MakeTableIssue', rate_key
        return None

    if table_record is None:
        gsa_multitables[rate_key] = tbody_text
        save_tables(gsa_multitables, TABLES_2017)
        return None

    previous_tables[rate_key] = table_record[rate_key]
    save_tables(previous_tables)
    return table_record[rate_key]


def get_fiscal_year(month_day_year):
    date = datetime.strptime(month_day_year, '%m/%d/%Y')
    for year in FISCAL_YEARS:
        start = FISCAL_YEARS[year][0]
        end = FISCAL_YEARS[year][1]
        if date >= start and date <= end:
            return year

    return None


def lookup_state(state):
    state_codes = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
    }
    return state_codes[state]

def log_error(id_num, category):
    error_csv = 'results/errors.csv'
    with open(error_csv, 'ab') as errors:
        writer = csv.writer(errors)
        writer.writerow((id_num, category))

def get_records_from_table(data, previous_tables):
    gsa_multitables = load_tables(TABLES_2017)
    date_string = '%m/%d/%Y'
    with open(data, 'rb') as stays:
        reader = csv.DictReader(stays)
        for row in reader:
            id_num, state, city, zipcode, checkin_date = (
                                                  int(row['ID'].strip()),
                                                  row['STATE'].strip(),
                                                  row['CITY'].strip(),
                                                  row['ZIP_CODE'].strip(),
                                                  row['CHECKIN_DATE'].strip())
            try:
                state = lookup_state(state)
            except KeyError:
                print 'NOT FOUND', id_num, state, zipcode
                log_error(id_num, 'state not found')
                continue
            try:
                fiscal_year = get_fiscal_year(checkin_date)
                if fiscal_year != '2017':
                    continue
            except ValueError:
                print 'BAD CHECKIN', id_num, checkin_date
                log_error(id_num, 'checkin_date format error')
                continue
            # checkin_date = datetime.strftime(datetime.strptime(checkin_date, date_string), RATE_DATE_FORMAT)
            city, zipcode = (city, zipcode)
            zip1 = ''
            if ZIP_MATCHER.match(zipcode) is not None:
                zip1 = zipcode.split('-')[0].strip()

            record = get_perdiem_table(state.strip(), city, zip1, previous_tables, gsa_multitables)
            if record is None:
                record = get_perdiem_table(state.strip(), city, '', previous_tables, gsa_multitables)
                if record is None:
                    print 'bad bad bad', row
                    log_error(id_num, 'service error')
                    continue

            # print '{}, {}-{}:\n{}'.format(city, state, zipcode, record)
        # rates = record['rates']
        # print rates


def get_records_from_lookup(data, previous_tables, output_csv):
    date_string = '%m/%d/%Y'
    with open(data, 'rb') as stays, open(output_csv, 'wb') as output:
        reader = csv.DictReader(stays)
        writer = csv.writer(output)
        writer.writerow(reader.fieldnames + ['PERDIEM'])
        for row in reader:
            id_num, state, city, zipcode, checkin_date = (
                                                  int(row['ID'].strip()),
                                                  row['STATE'].strip(),
                                                  row['CITY'].strip(),
                                                  row['ZIP_CODE'].strip(),
                                                  row['CHECKIN_DATE'].strip())
            try:
                state = lookup_state(state)
            except KeyError:
                print 'NOT FOUND', id_num, state, zipcode
                continue
            try:
                fiscal_year = get_fiscal_year(checkin_date)
                if fiscal_year != '2017':
                    continue
            except ValueError:
                print 'BAD CHECKIN', id_num, checkin_date
                continue
            rate_date = datetime.strftime(datetime.strptime(checkin_date, date_string), RATE_DATE_FORMAT)
            city, zipcode = (city, zipcode)
            zip1 = ''
            if ZIP_MATCHER.match(zipcode) is not None:
                zip1 = zipcode.split('-')[0].strip()

            rate_key = get_rate_key(state, city, zip1)
            if rate_key not in previous_tables:
                continue
            rates = previous_tables[rate_key]['rates']
            if rate_date not in rates:
                print 'bad rate date', rate_key, rate_date
            else:
                writer.writerow([row[field] for field in reader.fieldnames] + [rates[rate_date]])


def remove_completed(stay_csv, completed_csv, shared_id_field, output_csv):
    completed_ids = {}
    with open(completed_csv) as completed:
        completed_reader = csv.DictReader(completed)
        for row in completed_reader:
            completed_ids[row[shared_id_field]] = None

    with open(stay_csv, 'rb') as stays, open(output_csv, 'wb') as output:
        reader = csv.DictReader(stays)
        writer = csv.writer(output)
        writer.writerow(reader.fieldnames)
        for row in reader:
            id_num = row[shared_id_field]
            if id_num not in completed_ids:
                writer.writerow([row[field] for field in reader.fieldnames])


if __name__ == '__main__':
    data = 'stays/non_utah_round2.csv'
    previous_tables = load_tables()
    get_records_from_table(data, previous_tables)
    # get_records_from_lookup(data, previous_tables, 'results/temp.csv')
    # remove_completed(data, 'results/non_utah_easy.csv', 'ID', 'stays/non_utah_round2.csv')

    # state, city, zip_code = ('Pennsylvania', 'PITTSBURGH', '15524')
    # record = get_perdiem_table(state, city, zip_code, previous_tables)
    # if record is None:
    #     record = get_perdiem_table(state, city, '', previous_tables)
    # print '{}, {}-{}:\n{}'.format(city, state, zip_code, record)