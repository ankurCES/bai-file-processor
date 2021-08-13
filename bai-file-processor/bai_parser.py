from .parsers import Bai2FileParser
from .writers import Bai2FileWriter
from .helpers import IteratorHelper
from .utils import process_file_data
import csv

def debugger(header_dict, grp_header_dict, list_transactions, summary_accounts, **kwargs):
    print('-------------------------------------------------------------------------------')
    print('-------------               Header                            -----------------')
    print('-------------------------------------------------------------------------------')
    print(header_dict)
    print('-------------------------------------------------------------------------------')
    print('-------------               Group Header                      -----------------')
    print('-------------------------------------------------------------------------------')
    print(grp_header_dict)
    print('-------------------------------------------------------------------------------')
    print('-------------                    Summary                      -----------------')
    print('-------------------------------------------------------------------------------')
    print(summary_accounts)
    print('-------------------------------------------------------------------------------')
    print('-------------               Transactions                      -----------------')
    print('-------------------------------------------------------------------------------')
    print(list_transactions)

def parse_from_lines(lines, **kwargs):
    helper = IteratorHelper(lines)
    parser = Bai2FileParser(helper, **kwargs)
    return parser.parse()


def parse_from_string(s, **kwargs):
    return parse_from_lines(s.splitlines(), **kwargs)


def parse_from_file(f, **kwargs):
    with open(f) as bai_file:
        lines = bai_file.readlines()
        proc_lines = []
        for line in lines:
            # cleanup lines and remove whitespaces
            pr_line = line.strip()
            proc_lines.append(pr_line)
        return parse_from_lines(proc_lines, **kwargs)

def extract_bai_components(f, debug=False, export_csv=False, filepath='.', **kwargs):
    file_data = parse_from_file(f, **kwargs)
    header_dict, grp_header_dict, list_transactions, summary_accounts = process_file_data(file_data)
    if debug:
        debugger(header_dict, grp_header_dict, list_transactions, summary_accounts, **kwargs)
    
    if export_csv:
        create_csv_file(filepath, list_transactions, summary_accounts, **kwargs)
    
    return header_dict, grp_header_dict, list_transactions, summary_accounts

def create_csv_file(filepath, transactions, summary, **kwargs):
    if len(transactions) > 0:
        tr_keys = transactions[0].keys()
        with open('{}/transactions.csv'.format(filepath), 'w',encoding='utf8', newline='')  as output_file:
            dict_writer = csv.DictWriter(output_file, tr_keys)
            dict_writer.writeheader()
            dict_writer.writerows(transactions)
    
    if len(summary) > 0:
        summary_keys = summary[0].keys()
        with open('{}/summary.csv'.format(filepath), 'w',encoding='utf8', newline='')  as output_file:
            dict_writer = csv.DictWriter(output_file, summary_keys)
            dict_writer.writeheader()
            dict_writer.writerows(summary)

def write(bai2_obj, **kwargs):
    return '\n'.join(Bai2FileWriter(bai2_obj, **kwargs).write())
