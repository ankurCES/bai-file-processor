import datetime
import re
import warnings
from decimal import Decimal

from .constants import TypeCode, TypeCodeLevel, TypeCodes


def parse_date(value):
    """
    YYMMDD Format.
    """
    return datetime.datetime.strptime(value, '%y%m%d').date()


def write_date(date):
    return date.strftime('%y%m%d')


def parse_time(value):
    clock_pattern = re.compile(r'\d\d:\d\d:\d\d')

    if clock_pattern.match(value):
        return parse_clock_time(value)
    else:
        return parse_military_time(value)


def parse_clock_time(value):
    return datetime.datetime.strptime(value, '%H:%M:%S').time()


def parse_military_time(value):
    """
    Military Format, 24 hours. 0001 through 2400.
    Times are stated in military format (0000 through 2400).
    0000 indicates the beginning of the day and 2400 indicates the end of the day
    for the date indicated.
    Some processors use 9999 to indicate the end of the day.
    Be prepared to recognize 9999 as end-of-day when receiving transmissions.
    """
    # 9999 indicates end of the day
    # 2400 indicates end of the day but 24:00 not allowed so
    # it's really 23:59
    if value == '9999' or value == '2400':
        return datetime.time.max
    return datetime.datetime.strptime(value, '%H%M').time()


def write_time(time, clock_format_for_intra_day=False):
    if clock_format_for_intra_day and time != datetime.time.max:
        return write_clock_time(time)
    else:
        return write_military_time(time)


def write_clock_time(time):
    return time.strftime('%H:%M:%S')


def write_military_time(time):
    if time == datetime.time.max:
        return '2400'
    return time.strftime('%H%M')


def parse_type_code(value):
    type_code = TypeCodes.get(value)
    if type_code is None:
        warnings.warn(
            f'Unknown BAI2 type code {value!r} — treating as unclassified detail transaction.',
            stacklevel=2,
        )
        type_code = TypeCode(code=value, transaction=None, level=TypeCodeLevel.detail,
                             description=f'Unknown ({value})')
    return type_code


def parse_amount(value):
    """Parse a BAI2 amount string as Decimal, supporting both integer ('10000')
    and explicit-decimal ('1000.50') formats sent by different banks."""
    return Decimal(value)


def format_amount(raw_amount):
    """Convert a raw BAI2 amount (smallest currency unit, e.g. cents) to a
    decimal dollar value by dividing by 100."""
    if raw_amount is None:
        return None
    return Decimal(str(raw_amount)) / Decimal('100')


def convert_to_string(value):
    if value is None:
        return ''
    else:
        return str(value)


def process_account_summary(summary):
    summary_data = {
        'BAI Code': summary.type_code.code,
        'Level': summary.type_code.level.value,
        'Description': summary.type_code.description,
        'Amount': format_amount(summary.amount),
        'Count': summary.item_count,
        'Fund Type': summary.funds_type,
        'Availability': summary.availability
    }
    return summary_data

def process_account_header(header):
    summary_list = []
    for account_summary in header.summary_items:
        summary_data = process_account_summary(account_summary)
        summary_data['Customer Account Number'] = header.customer_account_number
        summary_data['Currency'] = header.currency
        summary_list.append(summary_data)
    return summary_list

def process_account_transactions(identifier, transactions):
    list_transactions = []
    # TransactionDetail
    for transaction in transactions:
        transaction_dict = {
            'Customer Account Number': identifier.customer_account_number,
            'Currency': identifier.currency,
            'BAI Code': transaction.type_code.code,
            'Transaction': transaction.type_code.transaction.value,
            'Level': transaction.type_code.level.value,
            'Description': transaction.type_code.description,
            'Amount': format_amount(transaction.amount),
            'Fund Type': transaction.funds_type,
            'Availability': transaction.availability,
            'Bank Reference': transaction.bank_reference,
            'Customer Reference': transaction.customer_reference,
            'Text': transaction.text
        }
        list_transactions.append(transaction_dict)
    return list_transactions

def process_accounts(accounts):
    list_transactions = []
    summary_accounts = []
    for account in accounts:
        account_identifier = account.header
        account_trailer = account.trailer
        account_transactions = account.children
        # Process Entities
        summary_list = process_account_header(account_identifier)
        tr_list = process_account_transactions(account_identifier, account_transactions)
        list_transactions = list_transactions + tr_list
        summary_accounts = summary_accounts + summary_list
    return list_transactions, summary_accounts

def process_bai_header(bai_header):
    header_dict = {
        'Sender ID': bai_header.sender_id,
        'Receiver ID': bai_header.receiver_id,
        'Creation Date': bai_header.creation_date.strftime('%m/%d/%Y') if bai_header.creation_date != None else None,
        'Creation Time': bai_header.creation_time.strftime('%H:%M') if bai_header.creation_time != None else None,
        'File ID': bai_header.file_id,
    }
    return header_dict

def process_bai_grp_header(grp_header):
    grp_dict_head = {
        'Ultimate Receiver ID': grp_header.ultimate_receiver_id,
        'Originator ID': grp_header.originator_id,
        'Group Status': grp_header.group_status.name if grp_header.group_status != None else None,
        'As of date': grp_header.as_of_date.strftime('%m/%d/%Y') if grp_header.as_of_date != None else None,
        'As of time': grp_header.as_of_time.strftime('%H:%M') if grp_header.as_of_time != None else None,
        'Currency': grp_header.currency,
        'As of Date Modifier': grp_header.as_of_date_modifier.name if grp_header.as_of_date_modifier != None else None,

    }
    return grp_dict_head

def process_file_data(file_data):
    # Extract Header, Trailer, Transaction Data
    header_dict = process_bai_header(file_data.header)
    # Iterate all groups; grp_header_dict captures the first group only
    # (return signature is preserved for backwards compatibility)
    grp_header_dict = None
    list_transactions = []
    summary_accounts = []
    for group in file_data.children:
        if grp_header_dict is None:
            grp_header_dict = process_bai_grp_header(group.header)
        tr_list, summary_list = process_accounts(group.children)
        list_transactions += tr_list
        summary_accounts += summary_list
    return header_dict, grp_header_dict, list_transactions, summary_accounts