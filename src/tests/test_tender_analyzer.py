# tests/test_tender_analyzer.py
import pytest
from src.tender_analyzer import extract_dates_fallback


# Test cases for different date formats
@pytest.mark.parametrize(
    "file_content, file_name, expected_output",
    [
        # DD.MM.YYYY format
        (
            "The deadline is 21.04.2021 for submission.",
            "test.pdf",
            "- 21.04.2021, The deadline is for submission, Source: test.pdf",
        ),
        (
            "Meeting on 01.01.2023 at 9h to discuss plans.",
            "test.pdf",
            "- 01.01.2023 at 9h, Meeting on to discuss plans, Source: test.pdf",
        ),
        # YYYY-MM-DD format
        (
            "Event scheduled for 2021-04-21 in the morning.",
            "test.pdf",
            "- 2021-04-21, Event scheduled for in the morning, Source: test.pdf",
        ),
        (
            "Start date: 2023-01-01 for the project.",
            "test.pdf",
            "- 2023-01-01, Start date: for the project, Source: test.pdf",
        ),
        # D Month YYYY format
        (
            "The event is on 1 January 2021 at the venue.",
            "test.pdf",
            "- 1 January 2021, The event is on at the venue, Source: test.pdf",
        ),
        (
            "Deadline: 21 April 2021 for all submissions.",
            "test.pdf",
            "- 21 April 2021, Deadline: for all submissions, Source: test.pdf",
        ),
        # Month YYYY format (for all months)
        (
            "Published in January 2021 by the committee.",
            "test.pdf",
            "- January 2021, Published in by the committee, Source: test.pdf",
        ),
        (
            "Event in February 2021 was successful.",
            "test.pdf",
            "- February 2021, Event in was successful, Source: test.pdf",
        ),
        (
            "Scheduled for March 2021 to start.",
            "test.pdf",
            "- March 2021, Scheduled for to start, Source: test.pdf",
        ),
        (
            "April 2021 is the target date.",
            "test.pdf",
            "- April 2021, is the target date, Source: test.pdf",
        ),
        (
            "May 2021 marks the end of the phase.",
            "test.pdf",
            "- May 2021, marks the end of the phase, Source: test.pdf",
        ),
        (
            "June 2021 is the deadline.",
            "test.pdf",
            "- June 2021, is the deadline, Source: test.pdf",
        ),
        (
            "July 2021 for the next meeting.",
            "test.pdf",
            "- July 2021, for the next meeting, Source: test.pdf",
        ),
        (
            "August 2021 is the start date.",
            "test.pdf",
            "- August 2021, is the start date, Source: test.pdf",
        ),
        (
            "September 2021 for the event.",
            "test.pdf",
            "- September 2021, for the event, Source: test.pdf",
        ),
        (
            "October 2021 is the deadline.",
            "test.pdf",
            "- October 2021, is the deadline, Source: test.pdf",
        ),
        (
            "November 2021 for submission.",
            "test.pdf",
            "- November 2021, for submission, Source: test.pdf",
        ),
        (
            "December 2021 is the final date.",
            "test.pdf",
            "- December 2021, is the final date, Source: test.pdf",
        ),
        # DD/MM/YYYY format
        (
            "Submit by 21/04/2021 to the office.",
            "test.pdf",
            "- 21/04/2021, Submit by to the office, Source: test.pdf",
        ),
        (
            "Start on 01/01/2023 for the project.",
            "test.pdf",
            "- 01/01/2023, Start on for the project, Source: test.pdf",
        ),
        # Case sensitivity for month names
        (
            "Event on 1 january 2021 at the venue.",
            "test.pdf",
            "- 1 January 2021, Event on at the venue, Source: test.pdf",
        ),
        (
            "Event on 1 JANUARY 2021 at the venue.",
            "test.pdf",
            "- 1 January 2021, Event on at the venue, Source: test.pdf",
        ),
        # Multiple dates in the same sentence
        (
            "From 01.01.2021 to 31.12.2021, the project runs.",
            "test.pdf",
            "- 01.01.2021, From to 31.12.2021 the project runs, Source: test.pdf\n- 31.12.2021, From 01.01.2021 to the project runs, Source: test.pdf",
        ),
        # No dates
        (
            "No dates in this text.",
            "test.pdf",
            "NO_INFO_FOUND",
        ),
        # Invalid dates
        (
            "Invalid date 32.04.2021 in the text.",
            "test.pdf",
            "NO_INFO_FOUND",
        ),
        (
            "Invalid date 2021-13-01 in the text.",
            "test.pdf",
            "NO_INFO_FOUND",
        ),
        (
            "Invalid date 0 January 2021 in the text.",
            "test.pdf",
            "NO_INFO_FOUND",
        ),
        (
            "Invalid date January 999 in the text.",
            "test.pdf",
            "NO_INFO_FOUND",
        ),
        (
            "Invalid date 00/00/2021 in the text.",
            "test.pdf",
            "NO_INFO_FOUND",
        ),
        # Dates near sentence boundaries
        (
            "Sentence one. The deadline is 21.04.2021 for submission. Another sentence.",
            "test.pdf",
            "- 21.04.2021, The deadline is for submission, Source: test.pdf",
        ),
        # Dates with special characters
        (
            "Deadline: 21.04.2021! Submit now.",
            "test.pdf",
            "- 21.04.2021, Deadline: Submit now, Source: test.pdf",
        ),
    ],
    ids=[
        "DD.MM.YYYY",
        "DD.MM.YYYY with time",
        "YYYY-MM-DD",
        "YYYY-MM-DD single digit",
        "D Month YYYY single digit",
        "D Month YYYY double digit",
        "Month YYYY January",
        "Month YYYY February",
        "Month YYYY March",
        "Month YYYY April",
        "Month YYYY May",
        "Month YYYY June",
        "Month YYYY July",
        "Month YYYY August",
        "Month YYYY September",
        "Month YYYY October",
        "Month YYYY November",
        "Month YYYY December",
        "DD/MM/YYYY",
        "DD/MM/YYYY single digit",
        "Month YYYY lowercase",
        "Month YYYY uppercase",
        "Multiple dates in sentence",
        "No dates",
        "Invalid date DD.MM.YYYY",
        "Invalid date YYYY-MM-DD",
        "Invalid date D Month YYYY",
        "Invalid date Month YYYY",
        "Invalid date DD/MM/YYYY",
        "Date near sentence boundary",
        "Date with special characters",
    ],
)
def test_extract_dates_fallback(file_content, file_name, expected_output):
    """Test the extract_dates_fallback function with various date formats."""
    result = extract_dates_fallback(file_content, file_name)
    assert result == expected_output, f"Expected:\n{expected_output}\nGot:\n{result}"
