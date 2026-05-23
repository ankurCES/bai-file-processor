from .models import Record
from .constants import RecordCode
from .exceptions import ParsingException


def _build_record(rows):
    fields_str = ''
    for row in rows:
        field_str = row[1]

        if field_str:
            if field_str[-1] == '/':
                fields_str += field_str[:-1] + ','
            else:
                fields_str += field_str + ' '

    fields = fields_str[:-1].split(',')
    return Record(code=rows[0][0], fields=fields, rows=rows)


def _parse_row(line):
    try:
        return (RecordCode(line[:2]), line[3:])
    except ValueError:
        raise ParsingException(f'Unrecognised record code in line: {line!r}')


def record_generator(lines):
    rows = iter(
        [_parse_row(line) for line in lines if line.strip()]
    )

    records = [next(rows)]
    while True:
        try:
            row = next(rows)
        except StopIteration:
            break

        if row[0] != RecordCode.continuation:
            yield _build_record(records)
            records = [row]
        else:
            records.append(row)

    yield _build_record(records)


class IteratorHelper:
    def __init__(self, lines):
        self._generator = record_generator(lines)
        self.current_record = None
        self.advance()

    def advance(self):
        self.current_record = next(self._generator)
