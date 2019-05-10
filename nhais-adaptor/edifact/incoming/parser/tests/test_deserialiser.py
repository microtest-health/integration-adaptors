import unittest

from testfixtures import compare

import edifact.incoming.parser.deserialiser as deserialiser
from edifact.incoming.models.interchange import InterchangeHeader, Interchange
from edifact.incoming.models.message import MessageSegmentBeginningDetails, MessageSegment, Messages
from edifact.incoming.models.transaction import Transactions, Transaction, TransactionRegistrationDetails, \
    TransactionPatientDetails
from edifact.incoming.parser import EdifactDict


class TestDeserialiser(unittest.TestCase):

    def test_extract_relevant_lines(self):
        original_dict = EdifactDict([
            ("UNB", "UNOA:2+SO01+ROO5+190429:1756+00016288++FHSREG+++FHSA EDI TRANSFERS"),
            ("UNH", "00024986+FHSREG:0:1:FH:FHS001"),
            ("BGM", "++507"),
            ("NAD", "FHS+SO:954"),
            ("DTM", "137:201904291755:203"),
            ("RFF", "950:F4"),
            ("S01", "1"),
            ("RFF", "TN:211102"),
            ("NAD", "GP+1231231,PLP348:900"),
            ("S02", "2"),
            ("PNA", "PAT+9876556789:OPI"),
            ("UNT", "11+00024986"),
            ("UNZ", "1+00016288"),
        ])

        with self.subTest("When the trigger key is UNB (the interchange header)"):
            expected = EdifactDict([
                ("UNB", "UNOA:2+SO01+ROO5+190429:1756+00016288++FHSREG+++FHSA EDI TRANSFERS")
            ])

            interchange_header_dict = deserialiser.extract_relevant_lines(original_dict, 0, ["UNH"])

            compare(interchange_header_dict, expected)

        with self.subTest("When the trigger key is BGM (the message beginning section)"):
            expected = EdifactDict([
                ("BGM", "++507"),
                ("NAD", "FHS+SO:954"),
                ("DTM", "137:201904291755:203"),
                ("RFF", "950:F4")
            ])

            message_beginning_dict = deserialiser.extract_relevant_lines(original_dict, 2, ["S01"])

            compare(message_beginning_dict, expected)

        with self.subTest("When the trigger key is S01 (the message registration section)"):
            expected = EdifactDict([
                ("S01", "1"),
                ("RFF", "TN:211102"),
                ("NAD", "GP+1231231,PLP348:900")
            ])

            message_registration_dict = deserialiser.extract_relevant_lines(original_dict, 6, ["S02"])

            compare(message_registration_dict, expected)

        with self.subTest("When the trigger key is S02 (the message patient section)"):
            expected = EdifactDict([
                ("S02", "2"),
                ("PNA", "PAT+9876556789:OPI"),
            ])

            message_registration_dict = deserialiser.extract_relevant_lines(original_dict, 9, ["UNT"])

            compare(message_registration_dict, expected)

    def test_convert_to_dict(self):
        with self.subTest("Without duplicate keys"):
            expected = EdifactDict([
                ("UNB", "UNOA:2+SO01+ROO5+190429:1756+00016288++FHSREG+++FHSA EDI TRANSFERS"),
                ("UNH", "00024986+FHSREG:0:1:FH:FHS001"),
                ("BGM", "++507")
            ])

            input_lines = [
                "UNB+UNOA:2+SO01+ROO5+190429:1756+00016288++FHSREG+++FHSA EDI TRANSFERS",
                "UNH+00024986+FHSREG:0:1:FH:FHS001",
                "BGM+++507"
            ]
            converted_dict = deserialiser.convert_to_dict(input_lines)

            compare(converted_dict, expected)

        with self.subTest("With duplicate keys"):
            expected = EdifactDict([
                ("NAD", "FHS+SO:954"),
                ("DTM", "137:201904291755:203"),
                ("NAD", "GP+1231231,PLP348:900")
            ])

            input_lines = [
                "NAD+FHS+SO:954",
                "DTM+137:201904291755:203",
                "NAD+GP+1231231,PLP348:900",
            ]
            converted_dict = deserialiser.convert_to_dict(input_lines)

            compare(converted_dict, expected)

    def test_convert(self):
        with self.subTest("When the edifact incoming message does not have a patient section (S02)"):
            expected = Interchange(InterchangeHeader("SO01", "ROO5", "190429:1756"),
                                   Messages([
                                       MessageSegment(MessageSegmentBeginningDetails("F4"),
                                                      Transactions([
                                                          Transaction(
                                                              TransactionRegistrationDetails("211102")
                                                          )
                                                      ]))
                                   ]))

            input_lines = [
                "UNB+UNOA:2+SO01+ROO5+190429:1756+00016288++FHSREG+++FHSA EDI TRANSFERS",
                "UNH+00024986+FHSREG:0:1:FH:FHS001",
                "BGM+++507",
                "NAD+FHS+SO:954",
                "DTM+137:201904291755:203",
                "RFF+950:F4",
                "S01+1",
                "RFF+TN:211102",
                "NAD+GP+1231231,PLP348:900",
                "UNT+9+00024986",
                "UNZ+1+00016288",
            ]

            result = deserialiser.convert(input_lines)
            compare(result, expected)

        with self.subTest("When the edifact incoming message does have a patient section (SO2)"):
            expected = Interchange(InterchangeHeader("SO01", "ROO5", "190429:1756"),
                                   Messages([
                                       MessageSegment(MessageSegmentBeginningDetails("F4"),
                                                      Transactions([
                                                          Transaction(
                                                              TransactionRegistrationDetails("211102"),
                                                              TransactionPatientDetails("9876556789")
                                                          )
                                                      ]))
                                   ]))

            input_lines = [
                "UNB+UNOA:2+SO01+ROO5+190429:1756+00016288++FHSREG+++FHSA EDI TRANSFERS",
                "UNH+00024986+FHSREG:0:1:FH:FHS001",
                "BGM+++507",
                "NAD+FHS+SO:954",
                "DTM+137:201904291755:203",
                "RFF+950:F4",
                "S01+1",
                "RFF+TN:211102",
                "NAD+GP+1231231,PLP348:900",
                "S02+2",
                "PNA+PAT+9876556789:OPI",
                "UNT+9+00024986",
                "UNZ+1+00016288",
            ]

            result = deserialiser.convert(input_lines)
            compare(result, expected)

        with self.subTest("When the edifact incoming interchange has a message with multiple transactions"):
            expected = Interchange(InterchangeHeader("SO01", "ROO5", "190429:1756"),
                                   Messages([
                                       MessageSegment(MessageSegmentBeginningDetails("F4"),
                                                      Transactions([
                                                          Transaction(
                                                              TransactionRegistrationDetails("211102"),
                                                              TransactionPatientDetails("9876556789")
                                                          ),
                                                          Transaction(
                                                              TransactionRegistrationDetails("211103")
                                                          ),
                                                      ]))
                                   ]))

            input_lines = [
                "UNB+UNOA:2+SO01+ROO5+190429:1756+00016288++FHSREG+++FHSA EDI TRANSFERS",
                "UNH+00024986+FHSREG:0:1:FH:FHS001",
                "BGM+++507",
                "NAD+FHS+SO:954",
                "DTM+137:201904291755:203",
                "RFF+950:F4",
                "S01+1",
                "RFF+TN:211102",
                "NAD+GP+1231231,PLP348:900",
                "S02+2",
                "PNA+PAT+9876556789:OPI",
                "S01+1",
                "RFF+TN:211103",
                "NAD+GP+1231231,PLP348:900",
                "UNT+9+00024986",
                "UNZ+1+00016288",
            ]

            result = deserialiser.convert(input_lines)
            compare(result, expected)

        with self.subTest("When the edifact incoming interchange has a 2 messages with multiple transactions"):
            expected = Interchange(InterchangeHeader("SO01", "ROO5", "190429:1756"),
                                   Messages([
                                       MessageSegment(MessageSegmentBeginningDetails("F4"),
                                                      Transactions([
                                                          Transaction(
                                                              TransactionRegistrationDetails("211102"),
                                                              TransactionPatientDetails("9876556789")
                                                          ),
                                                          Transaction(
                                                              TransactionRegistrationDetails("211103")
                                                          ),
                                                      ])),
                                       MessageSegment(MessageSegmentBeginningDetails("F2"),
                                                      Transactions([
                                                          Transaction(
                                                              TransactionRegistrationDetails("211104"),
                                                              TransactionPatientDetails("111111111")
                                                          ),
                                                          Transaction(
                                                              TransactionRegistrationDetails("211105"),
                                                              TransactionPatientDetails("2222222222")
                                                          ),
                                                      ]))
                                   ]))

            input_lines = [
                "UNB+UNOA:2+SO01+ROO5+190429:1756+00016288++FHSREG+++FHSA EDI TRANSFERS",
                "UNH+00024986+FHSREG:0:1:FH:FHS001",
                "BGM+++507",
                "NAD+FHS+SO:954",
                "DTM+137:201904291755:203",
                "RFF+950:F4",
                "S01+1",
                "RFF+TN:211102",
                "NAD+GP+1231231,PLP348:900",
                "S02+2",
                "PNA+PAT+9876556789:OPI",
                "S01+1",
                "RFF+TN:211103",
                "NAD+GP+1231231,PLP348:900",
                "UNT+14+00024986",
                "UNH+00024987+FHSREG:0:1:FH:FHS001",
                "BGM+++507",
                "NAD+FHS+XX1:954",
                "DTM+137:199201251235:203",
                "RFF+950:F2",
                "S01+1",
                "RFF+TN:211104",
                "NAD+GP+2750922,295:900",
                "GIS+1:ZZZ",
                "DTM+961:19920125:102",
                "S02+2",
                "PNA+PAT+111111111:OPI",
                "S01+1",
                "RFF+TN:211105",
                "NAD+GP+2750922,295:900",
                "GIS+1:ZZZ",
                "DTM+961:19920125:102",
                "S02+2",
                "PNA+PAT+2222222222:OPI",
                "UNT+13+00024987",
                "UNZ+1+00016288",
            ]

            result = deserialiser.convert(input_lines)
            compare(result, expected)
