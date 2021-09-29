"""
`NACHA <http://www.regaltek.com/docs/NACHA%20Format.pdf>`_ is a fixed sized
record format used to represent financial transactions composed like this:

.. code::

    FileHeader
        CompanyBatchHeader
            EntryDetail
                EntryDetailAddendum
                ...
            ...
        CompanyBatchControl
        ...
    FileControl

which we express using `bryl3 <https://github.com/balanced/bryl3/>`_. Writing is
done like this:

.. code:: python

    with open('sample.nacha', 'w') as fo:
        writer = nacha.Writer(fo)
        with writer.begin_file(
             ...
             ):
             with writer.begin_company_batch(
                  ...
                  ):
                 writer.entry(...):
                 ...
            ...

Reading is done by iterating records like this:

.. code:: python

    with open('sample.nacha', 'r') as fo:
        reader = Reader(fo, include_terminal=True)
        for record, terminal in reader:
            ...

Or structured like this:

.. code:: python

    with open('sample.nacha', 'r') as fo:
        reader = Reader(fo)
        reader.file_header()
        for company_batch_header in reader.company_batches():
            for entry_detail, entry_addenda in reader.entries():
                ...
            reader.company_batch_control()
        reader.file_control()

"""

__all__ = [
    'ctx',
    'FileHeader',
    'CompanyBatchHeader',
    'EntryDetail',
    'EntryDetailAddendum',
    'EntryDetailAddendum',
    'POSAddendum',
    'IATAddendumFirst',
    'IATAddendumSecond',
    'IATAddendumThird',
    'IATAddendumFourth',
    'IATAddendumFifth',
    'IATAddendumSixth',
    'IATAddendumSeventh',
    'IATAddendumRemittance',
    'IATAddendumCorrespondentBank',
    'IATAddendumReturn',
    'CompanyBatchControl',
    'FileControl',
    'ServiceClassCodes',
    'StandardEntryClasses',
    'TransactionCodes',
    'Writer',
    'Reader',
]

import collections
import contextlib
import datetime
import itertools

from .packages import bryl3
from .packages.bryl3 import (
    Numeric,
    Date,
    Time,
    Alphanumeric,
    LineReader,
)


ctx = bryl3.ctx(alpha_upper=True)


class Enum(dict):

    def __init__(self, **kwargs):
        super(Enum, self).__init__(**kwargs)
        for k, v in list(kwargs.items()):
            setattr(self, k, v)


class Record(bryl3.Record):

    record_type = Alphanumeric(1)

    def copy(self):
        return type(self)(**self)
    
    @classmethod
    def specify(cls, data):
        return cls


class FileHeader(Record):

    record_type = Record.record_type.constant('1')

    priority_code = Numeric(2).constant(1)

    immediate_destination = Numeric(10, pad=' ')

    immediate_origin = Alphanumeric(10)

    file_creation_date = Date('YYMMDD')

    file_creation_time = Time('hhmm')

    @property
    def file_creation(self):
        return datetime.datetime.combine(
            self.file_creation_date, self.file_creation_time
        )

    file_id_modifier = Alphanumeric(1)

    record_size = Numeric(3).constant(94)

    blocking_factor = Numeric(2).constant(10)

    format_code = Numeric(1).constant(1)

    immediate_destination_name = Alphanumeric(23)

    immediate_origin_name = Alphanumeric(23)

    reference_code = Alphanumeric(8, default='')


ServiceClassCodes = Enum(
    MIXED_DEBITS_CREDITS=200,
    CREDITS=220,
    DEBITS=225,
)

StandardEntryClasses = Enum(
    ARC='ARC',  # Accounts Receivable Entry
    CIE='CIE',  # Customer Initiated Entry
    MTE='MTE',  # Machine Transfer Entry
    PBR='PBR',  # Consumer Cross-Border Payment
    POP='POP',  # Point-of-Purchase
    PPD='PPD',  # Prearranged Payment & Deposit
    POS='POS',  # Point of Sale Entry/Shared Network Transaction
    SHR='SHR',  # Point of Sale Entry/Shared Network Transaction
    RCK='RCK',  # Re-presented Check Entry
    TEL='TEL',  # Telephone-Initiated Entry
    WEB='WEB',  # Internet-Initiated Entry
    CBR='CBR',  # Corporate Cross-Border Payment
    IAT='IAT',  # International ACH Transaction
    CCD='CCD',  # Cash Concentration or Disbursement
    CTX='CTX',  # Corporate Trade Exchange
    ACK='ACK',  # Acknowledgment Entries
    ATX='ATX',  # Acknowledgment Entries
    ADV='ADV',  # Automated Accounting Advice
    COR='COR',  # Automated Notification of Change or Refused Notification of Change
    DNE='DNE',  # Death Notification Entry
    ENR='ENR',  # Automated Enrollment Entry
    TRC='TRC',  # Truncated Entries
    TRX='TRX',  # Truncated Entries
    XCK='XCK',  # Destroyed Check Entry'
)


class BaseCompanyBatchHeader(Record):

    record_type = Record.record_type.constant('5')

    service_class_code = Numeric(3, enum=ServiceClassCodes)

    company_name = Alphanumeric(length=16)

    @classmethod
    def specify(cls, data=None, company_name=None):
        if company_name is None:
            company_name = cls.load(data).company_name
        if company_name == '' or company_name.isspace():
            return IATCompanyBatchHeader
        return CompanyBatchHeader


class CompanyBatchHeader(BaseCompanyBatchHeader):

    company_discretionary_data = Alphanumeric(length=20, required=False)

    company_id = Alphanumeric(10)

    standard_entry_class = Alphanumeric(3, enum=StandardEntryClasses)

    company_entry_description = Alphanumeric(10)

    company_descriptive_date = Alphanumeric(6, required=False)

    effective_entry_date = Date('YYMMDD')

    # NOTE: this field is reserved for the banks
    settlement_date = Alphanumeric(3, required=False)

    originator_status = Numeric(1).constant(1)

    originating_dfi_id = Numeric(8)

    batch_number = Numeric(7)


class IATCompanyBatchHeader(BaseCompanyBatchHeader):

    company_name = BaseCompanyBatchHeader.company_name.reserved()

    foreign_exchange_indicator = Alphanumeric(2)

    foreign_exchange_reference_indicator = Alphanumeric(1)

    foreign_exchange_reference = Alphanumeric(15)

    iso_destination_country_code = Alphanumeric(2)

    company_id = Alphanumeric(10)

    standard_entry_class = Alphanumeric(3).constant('IAT')

    company_entry_description = Alphanumeric(10)

    iso_originating_currency_code = Alphanumeric(3)

    iso_destination_currency_code = Alphanumeric(3)

    effective_entry_date = Date('YYMMDD')

    # NOTE: this field is reserved for the banks
    settlement_date = Alphanumeric(3, required=False)

    originator_status = Numeric(1).constant(1)

    originating_dfi_id = Numeric(8)

    batch_number = Numeric(7)


TransactionCodes = Enum(
    # credit checking
    CHECKING_RETURNED_CREDIT=21,
    CHECKING_CREDIT=22,
    CHECKING_PRE_NOTE_CREDIT=23,

    # debit checking
    CHECKING_RETURNED_DEBIT=26,
    CHECKING_DEBIT=27,
    CHECKING_PRE_NOTE_DEBIT=28,

    # credit savings
    SAVINGS_RETURNED_CREDIT=31,
    SAVINGS_CREDIT=32,
    SAVINGS_PRE_NOTE_CREDIT=33,

    # debit savings
    SAVINGS_RETURNED_DEBIT=36,
    SAVINGS_DEBIT=37,
    SAVINGS_PRE_NOTE_DEBIT=38,

    GL_DEPOSIT_CREDIT=42,
    PN_GL_DEPOSIT_CREDIT=43,
    GL_WITHDRAWAL_DEBIT=47,
    PN_GL_WITHDRAWAL_CREDIT=48,
    LOAN_DEPOSIT_CREDIT=52,
    PN_LOAN_DEPOSIT_CREDIT=53,
    LOAN_REVERSAL_DEBIT=55,

)


class EntryDetail(Record):

    record_type = Record.record_type.constant('6')

    @classmethod
    def transaction_code_for(cls,
                             amount,
                             receiving_type,
                             is_return=False,
                             is_prenote=False,
        ):
        if is_return:
            code = TransactionCodes.CHECKING_RETURNED_CREDIT
        elif is_prenote or amount == 0:
            code = TransactionCodes.CHECKING_PRE_NOTE_CREDIT
        else:
            code = TransactionCodes.CHECKING_CREDIT
        if amount < 0:
            code += 5
        if receiving_type.lower() == 'checking':
            pass
        elif receiving_type.lower() == 'savings':
            code += 10
        else:
            raise ValueError(
                'Invalid receiving_type={0!r}'.format(receiving_type)
            )
        return code

    transaction_code = Numeric(2, enum=TransactionCodes)

    receiving_dfi_trn = Numeric(8)

    receiving_dfi_trn_check_digit = Numeric(1)

    receiving_dfi_account_number = Alphanumeric(17, align=Alphanumeric.RIGHT)

    amount = Numeric(10)

    # TODO: has dependencies
    individual_id = Alphanumeric(15)

    # TODO: has dependencies
    individual_name = Alphanumeric(22)

    # TODO: specific to wells fargo
    discretionary_data = Alphanumeric(2, required=False)

    addenda_record_indicator = Numeric(1)

    trace_number = Numeric(15)

    @property
    def is_checking(self):
        return int(self.transaction_code / 10) == 2

    @property
    def is_savings(self):
        return int(self.transaction_code / 10) == 3

    @property
    def is_credit(self):
        return self.transaction_code % 10 in (1, 2, 3)

    @property
    def is_debit(self):
        return self.transaction_code % 10 in (6, 7, 8)

    @property
    def is_prenote(self):
        return self.transaction_code % 10 in (3, 8)

    @property
    def is_returned(self):
        return self.transaction_code % 10 in (1, 6)

    @property
    def receiving_dfi_routing_number(self):
        return (self.receiving_dfi_trn * 10) + self.receiving_dfi_trn_check_digit

    def mask(self):
        self.receiving_dfi_account_number = (
            'X' * type(self).receiving_dfi_account_number.length
        )
        return self


class BaseEntryDetailAddendum(Record):

    record_type = Record.record_type.constant('7')

    addenda_type = Alphanumeric(2)

    @classmethod
    def create(self, **kwargs):
        correct_addendum_class = self.specify(addenda_type=kwargs["addenda_type"])
        correct_fields = [field.name for field in correct_addendum_class.fields]
        for k in list(kwargs.keys()):
            if k not in correct_fields:
                del kwargs[k]
        return self.specify(addenda_type=kwargs["addenda_type"])(**kwargs)
    
    @classmethod
    def specify(cls, data=None, addenda_type=None):
        addenda_types = dict(
            (addenda_cls.addenda_type.value, addenda_cls)
            for addenda_cls in [
                EntryDetailAddendum,
                POSAddendum,
                IATAddendumFirst,
                IATAddendumSecond,
                IATAddendumThird,
                IATAddendumFourth,
                IATAddendumFifth,
                IATAddendumSixth,
                IATAddendumSeventh,
                IATAddendumRemittance,
                IATAddendumCorrespondentBank,
                NOCAddendum,
                IATAddendumReturn,
            ]
        )
        if addenda_type is None:
            addenda_type = cls.load(data).addenda_type
        if addenda_type in addenda_types:
            return addenda_types[addenda_type]


class EntryDetailAddendum(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('05')

    payment_related_information = Alphanumeric(80)

    addenda_sequence_number = Numeric(4)

    entry_detail_sequence_number = Numeric(7)


class POSAddendum(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('02')

    reference_information_1 = Alphanumeric(7)

    reference_information_2 = Alphanumeric(3)

    terminal_identification_code = Alphanumeric(6)

    transaction_serial_number = Alphanumeric(6)

    transaction_date = Date('MMDD')

    authorization_code = Alphanumeric(6)

    terminal_location = Alphanumeric(27)

    terminal_city = Alphanumeric(15)

    terminal_state = Alphanumeric(2)

    trace_number = Numeric(15)


class IATAddendumFirst(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('10')

    transaction_type_code = Alphanumeric(3)

    foreign_payment_amount = Numeric(18)

    foreign_trace_number = Alphanumeric(22)

    receiving_company_name = Alphanumeric(35)

    reserved = Alphanumeric(6).reserved()

    entry_detail_sequence_number = Numeric(7)


class IATAddendumSecond(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('11')

    originator_name = Alphanumeric(35)

    originator_street_address = Alphanumeric(35)

    reserved = Alphanumeric(14).reserved()

    entry_detail_sequence_number = Numeric(7)


class IATAddendumThird(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('12')

    originator_city_and_state = Alphanumeric(35)

    originator_country_and_postal_code = Alphanumeric(35)

    reserved = Alphanumeric(14).reserved()

    entry_detail_sequence_number = Numeric(7)


class IATAddendumFourth(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('13')

    originating_dfi_name = Alphanumeric(35)

    originating_dfi_identification_qualifier = Alphanumeric(2)

    originating_dfi_identification = Alphanumeric(34)

    originating_dfi_branch_country_code = Alphanumeric(3)

    reserved = Alphanumeric(10).reserved()

    entry_detail_sequence_number = Numeric(7)


class IATAddendumFifth(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('14')

    receiving_dfi_name = Alphanumeric(35)

    receiving_dfi_identification_qualifier = Alphanumeric(2)

    receiving_dfi_identification = Alphanumeric(34)

    receiving_dfi_branch_country_code = Alphanumeric(3)

    reserved = Alphanumeric(10).reserved()

    entry_detail_sequence_number = Numeric(7)


class IATAddendumSixth(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('15')

    receiver_identification_number = Alphanumeric(15)

    receiver_street_address = Alphanumeric(35)

    reserved = Alphanumeric(34).reserved()

    entry_detail_sequence_number = Numeric(7)


class IATAddendumSeventh(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('16')

    receiver_city_and_state = Alphanumeric(35)

    receiver_country_and_postal_code = Alphanumeric(35)

    reserved = Alphanumeric(14).reserved()

    entry_detail_sequence_number = Numeric(7)


class IATAddendumRemittance(EntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('17')


class IATAddendumCorrespondentBank(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('18')

    correspondent_bank_name = Alphanumeric(35)

    correspondent_bank_identification_qualifier = Alphanumeric(2)

    correspondent_bank_identification = Alphanumeric(34)

    correspondent_bank_branch_country_code = Alphanumeric(3)

    reserved = Alphanumeric(6).reserved()

    addenda_sequence_number = Numeric(4)

    entry_detail_sequence_number = Numeric(7)


class NOCAddendum(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('98')

    change_code = Alphanumeric(3)

    original_trace_number = Numeric(15)

    reserved = Alphanumeric(6).reserved()

    original_dfi = Alphanumeric(8)

    corrected_data = Alphanumeric(29)

    second_reserved = Alphanumeric(15).reserved()

    trace_number = Numeric(15)


class IATAddendumReturn(BaseEntryDetailAddendum):

    addenda_type = BaseEntryDetailAddendum.addenda_type.constant('99')

    return_reason_code = Alphanumeric(3)

    original_trace_number = Numeric(15)

    date_of_death = Date('YYMMDD')

    original_dfi = Alphanumeric(8)

    original_payment_amount = Numeric(10)

    addenda_information = Alphanumeric(34)

    trace_number = Numeric(15)


class Entry(collections.namedtuple('Entry', ['detail', 'addenda'])):

    @property
    def is_rejection(self):
        return self.detail.is_rejection

    def mask(self):
        self.detail.mask()
        return self

    @classmethod
    def load(cls, raw):
        detail = EntryDetail.load(raw)
        raw = raw[EntryDetail.length + len(Writer.RECORD_TERMINAL):]
        addenda = []
        while raw:
            addendum = EntryDetailAddendum.load(raw)
            addenda.append(addendum)
            raw = raw[EntryDetailAddendum.length + len(Writer.RECORD_TERMINAL):]
        return cls(detail=detail, addenda=addenda)

    def dump(self):
        return Writer.RECORD_TERMINAL.join(
            [self.detail.dump()] +
            [addendum.dump() for addendum in self.addenda]
        )


class CompanyBatchControl(Record):

    record_type = Record.record_type.constant('8')

    service_class_code = Numeric(3)

    entry_addenda_count = Numeric(6)

    entry_hash = Numeric(10)

    total_batch_debit_entry_amount = Numeric(12)

    total_batch_credit_entry_amount = Numeric(12)

    company_id = Alphanumeric(10)

    message_authentication_code = Alphanumeric(19).reserved()

    blank = Alphanumeric(6).reserved()

    originating_dfi_id = Numeric(8)

    batch_number = Numeric(7)


class FileControl(Record):

    record_type = Record.record_type.constant('9')

    batch_count = Numeric(6)

    block_count = Numeric(6)

    entry_addenda_record_count = Numeric(8)

    entry_hash_total = Numeric(10)

    total_file_debit_entry_amount = Numeric(12)

    total_file_credit_entry_amount = Numeric(12)

    filler = Alphanumeric(39)


class BlockBuffer(bryl3.Record):

    filler = Alphanumeric(94).constant('9' * 94)


class Writer(object):

    RECORD_TERMINAL = '\n'

    HASH_MOD = 10 ** 10

    entry_detail_cls = EntryDetail

    entry_addendum_cls = BaseEntryDetailAddendum

    def __init__(self, fo):
        self.fo = fo
        self.created_at = None
        self._ctxs = []
        self._batch_numbers = itertools.count(1)
        self._default_at = None
        self._entry_count = 0
        self._total_blocks = 0

    def write(self, record):
        self.fo.write(record.dump())
        self.fo.write(self.RECORD_TERMINAL)
        self._total_blocks += 1

    def begin_file(
        self,
        immediate_destination,
        immediate_destination_name,
        immediate_origin,
        immediate_origin_name,
        created_at=None,
        file_id_modifier='A',
        reference_code=None,
    ):
        if self._ctxs:
            raise Exception('Cannot be in context')

        self._default_at = created_at = created_at or datetime.datetime.utcnow()

        self.file_header = FileHeader(
            file_creation_date=created_at.date(),
            file_creation_time=created_at.time(),
            immediate_destination=immediate_destination,
            immediate_destination_name=immediate_destination_name,
            immediate_origin=immediate_origin,
            immediate_origin_name=immediate_origin_name,
            file_id_modifier=file_id_modifier or 'A',
            reference_code=reference_code,
        )
        self.created_at = created_at
        self.write(self.file_header)

        # file control
        self.file_control = FileControl(
            batch_count=0,
            block_count=0,
            entry_addenda_record_count=0,
            entry_hash_total=0,
            total_file_debit_entry_amount=0,
            total_file_credit_entry_amount=0,
            filler='',
        )

        return self._push(self.end_file)

    def in_file_context(self):
        return self._ctxs and self._ctxs[-1] == self.end_file

    def begin_company_batch(
        self,
        **kwargs,
    ):
        batch_number = next(self._batch_numbers)
        self._company_batch_header = BaseCompanyBatchHeader.specify(
            company_name=kwargs["company_name"]
        )(
            **kwargs,
            batch_number=batch_number,
        )
        self.write(self._company_batch_header)

        # company control
        self._company_batch_control = CompanyBatchControl(
            service_class_code=kwargs["service_class_code"],
            entry_addenda_count=0,
            entry_hash=0,
            total_batch_debit_entry_amount=0,
            total_batch_credit_entry_amount=0,
            company_id=kwargs["company_id"],
            originating_dfi_id=kwargs["originating_dfi_id"],
            batch_number=batch_number,
        )

        return self._push(self.end_company_batch)

    def in_company_batch_context(self):
        return self._ctxs and self._ctxs[-1] == self.end_company_batch

    def entry(self,
              transaction_code,
              receiving_dfi_routing_number,
              receiving_dfi_account_number,
              amount,
              individual_id,
              individual_name,
              trace_number=None,
              discretionary_data=None,
              addenda=None,
        ):
        with self.begin_entry(
                 transaction_code,
                 receiving_dfi_routing_number,
                 receiving_dfi_account_number,
                 amount,
                 individual_id,
                 individual_name,
                 trace_number,
                 discretionary_data,
             ):
            if addenda:
                for addednum in addenda:
                    self.entry_addendum(**addednum)
            detail, addenda = self._entry_detail, self._entry_addenda
        return detail, addenda

    def begin_entry(self,
                    transaction_code,
                    receiving_dfi_routing_number,
                    receiving_dfi_account_number,
                    amount,
                    individual_id,
                    individual_name,
                    trace_number=None,
                    discretionary_data=None,
        ):
        if not self.in_company_batch_context():
            raise Exception('Not in company batch context')
        self._entry_addenda = []
        dfi_str_temp = str(receiving_dfi_routing_number)
        if len(dfi_str_temp) > 9:
            raise ValueError(
                f'receiving_dfi_routing_number {dfi_str_temp} length > 9'
            )
        receiving_dfi_routing_number = dfi_str_temp.rjust(9, '0')
        self._entry_detail = self.entry_detail_cls(
            transaction_code=transaction_code,
            receiving_dfi_trn=int(receiving_dfi_routing_number[:8]),
            receiving_dfi_trn_check_digit=int(receiving_dfi_routing_number[-1]),
            receiving_dfi_account_number=receiving_dfi_account_number,
            amount=amount,
            individual_id=individual_id,
            individual_name=individual_name,
            trace_number=trace_number or self._trace_number(),
            discretionary_data=discretionary_data,
            addenda_record_indicator=0,
        )
        return self._push(self.end_entry)

    def in_entry_context(self):
        return self._ctxs and self._ctxs[-1] == self.end_entry

    def entry_addendum(self, **kwargs):
        if not self.in_entry_context:
            raise Exception('Not in entry context')

        self._entry_detail.addenda_record_indicator = 1
        kwargs["addenda_sequence_number"]=len([
            addenda for addenda in self._entry_addenda
            if getattr(addenda, "addenda_sequence_number", None) is not None
        ]) + 1
        kwargs["entry_detail_sequence_number"]=str(self._entry_detail.trace_number)[-7:]
        record = self.entry_addendum_cls.create(**kwargs)
        self._entry_addenda.append(record)

    def end_entry(self, ex=None):
        if not self.in_entry_context:
            raise Exception('Not in entry context')
        try:
            if ex is None:
                self._entry_detail.addenda_record_indicator = 1 if self._entry_addenda else 0
                self.write(self._entry_detail)
                for entry_addedum in self._entry_addenda:
                    self.write(entry_addedum)

                # company batch control
                if self._entry_detail.is_debit:
                    self._company_batch_control.total_batch_debit_entry_amount += self._entry_detail.amount
                elif self._entry_detail.is_credit:
                    self._company_batch_control.total_batch_credit_entry_amount += self._entry_detail.amount
                self._company_batch_control.entry_addenda_count += 1 + len(self._entry_addenda)
                self._company_batch_control.entry_hash = (
                    self._company_batch_control.entry_hash + self._entry_detail.receiving_dfi_trn
                ) % self.HASH_MOD

                # file control
                if self._entry_detail.is_debit:
                    self.file_control.total_file_debit_entry_amount += self._entry_detail.amount
                elif self._entry_detail.is_credit:
                    self.file_control.total_file_credit_entry_amount += self._entry_detail.amount
                self.file_control.entry_addenda_record_count += 1 + len(self._entry_addenda)
                self.file_control.entry_hash_total = (
                    self.file_control.entry_hash_total + self._entry_detail.receiving_dfi_trn
                ) % self.HASH_MOD

                self._entry_count += 1
        finally:
            self._pop(self.end_entry)

    def end_company_batch(self, ex=None):
        if not self.in_company_batch_context:
            raise Exception('Not in company batch context')
        try:
            if ex is None:
                self.write(self._company_batch_control)

                # file control
                self._entry_count = 0
                self.file_control.batch_count += 1
        finally:
            self._pop(self.end_company_batch)

    def end_file(self, ex=None):
        if not self.in_file_context:
            raise Exception('Not in file context')
        try:
            if ex is None:
                # file control
                self.file_control.block_count = self._total_blocks // self.file_header.blocking_factor + 1

                self.write(self.file_control)
                while self._total_blocks % self.file_header.blocking_factor != 0:
                    self.write(BlockBuffer())
        finally:
            self._pop(self.end_file)

    # internals

    def _trace_number(self):
        return '{0:0>8}{1:0>7}'.format(
            self._company_batch_header.originating_dfi_id,
            self._entry_count + 1
        )

    def _push(self, close):
        self._ctxs.append(close)
        return self._close(close)

    def _pop(self, expected):
        if not self._ctxs:
            raise Exception('No context')
        if self._ctxs[-1] != expected:
            raise Exception('Unexpected context {0} != {1}'.format(
                self._ctxs[-1].__name__, expected.__name__
            ))
        return self._ctxs.pop()

    @contextlib.contextmanager
    def _close(self, close):
        try:
            yield
        except Exception as ex:
            close(ex)
            raise
        else:
            close()


class Malformed(ValueError):

    def __init__(self, file_name, line_num, reason):
        self.file_name = file_name
        self.line_num = line_num
        self.reason = reason
        super(Malformed, self).__init__(
            "{0} @ {1} - {2}".format(file_name, line_num, reason)
        )


class Reader(LineReader):
    error_types = (Malformed, Record.field_type.error_type)

    record_types = dict(
        (record_cls.record_type.value, record_cls)
        for record_cls in [
            FileHeader,
            BaseCompanyBatchHeader,
            EntryDetail,
            BaseEntryDetailAddendum,
            CompanyBatchControl,
            FileControl,
        ]
    )

    def filter(self, *record_types):
        for record in self:
            if any(
                   isinstance(record, record_type)
                   for record_type in record_types
                ):
                yield record

    record_type = Record

    @staticmethod
    def as_record_type(reader, data, offset):
        record_type = reader.record_type.load(data).record_type
        if record_type in reader.record_types:
            return reader.record_types[record_type].specify(data)
        raise reader.malformed(
            offset, 'unexpected record_type {0}'.format(record_type),
        )

    # structured

    def file_header(self):
        return self.next_record(FileHeader)

    def company_batches(self):
        while True:
            header = self.next_record(CompanyBatchHeader, None)
            if not header:
                break
            yield header

    def entries(self):
        while True:
            detail = self.entry_detail()
            if not detail:
                break
            addenda = self.entry_addenda()
            yield Entry(detail=detail, addenda=addenda)

    def entry_detail(self, default=None):
        return self.next_record(EntryDetail, default)

    def entry_addenda(self, default=None):
        addenda = []
        while True:
            record = self.next_record(EntryDetailAddendum, None)
            if not record:
                break
            addenda.append(record)
        return addenda

    def company_batch_control(self):
        return self.next_record(CompanyBatchControl)

    def file_control(self):
        return self.next_record(FileControl)
