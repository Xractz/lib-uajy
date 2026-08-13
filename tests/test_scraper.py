from scrapling.parser import Selector

from app.booking.scraper import BookingScraper, ScraperError

HTML_JADWAL = """
<table class="GridViewStyle" id="MainContent_gvTransaksi">
  <tr class="HeaderStyle"><th>No</th><th>RUANG</th><th>TANGGAL</th><th>JAM</th><th>PEMESAN</th></tr>
  <tr class="RowStyle">
    <td class="grid_cell">1</td><td>Discussion Room 1</td><td>13/08/2026</td><td>08.00 - 09.30 WIB</td><td>EDHI HERI</td>
  </tr>
  <tr class="AltRowStyle">
    <td class="grid_cell">2</td><td>Discussion Room 2</td><td>13/08/2026</td><td>09.30 - 11.00 WIB</td><td>Legio Novelni</td>
  </tr>
  <tr class="PagerStyle"><td colspan="5"><a>1</a> <a>2</a> <a>3</a></td></tr>
</table>
"""

HTML_TOKEN_DEFAULT = """
<form>
<input type="hidden" id="__VIEWSTATE" value="ABC123">
<input type="hidden" id="__VIEWSTATEGENERATOR" value="GEN1">
<input type="hidden" id="__EVENTVALIDATION" value="EV1">
</form>
"""

HTML_TOKEN_JADWAL = """
<form>
<input type="hidden" id="__VIEWSTATE" value="ABC123">
<input type="hidden" id="__VIEWSTATEGENERATOR" value="GEN1">
</form>
"""


def test_parse_schedule_rows_captures_both_row_styles():
    page = Selector(HTML_JADWAL)
    rows = BookingScraper.parse_schedule_rows(page)
    assert len(rows) == 2
    assert rows[0] == {"room": "Discussion Room 1", "date": "13/08/2026", "time": "08.00 - 09.30 WIB", "name": "EDHI HERI"}
    assert rows[1]["room"] == "Discussion Room 2"


def test_parse_max_page():
    page = Selector(HTML_JADWAL)
    assert BookingScraper.parse_max_page(page) == 3


def test_parse_max_page_defaults_to_one():
    page = Selector("<html><body>tidak ada pager</body></html>")
    assert BookingScraper.parse_max_page(page) == 1


def test_parse_token_with_eventvalidation():
    page = Selector(HTML_TOKEN_DEFAULT)
    token = BookingScraper.parse_token(page)
    assert token["__VIEWSTATE"] == "ABC123"
    assert token["__EVENTVALIDATION"] == "EV1"


def test_parse_token_without_eventvalidation():
    page = Selector(HTML_TOKEN_JADWAL)
    token = BookingScraper.parse_token(page)
    assert token["__EVENTVALIDATION"] == ""


def test_parse_token_raises_when_no_viewstate():
    page = Selector("<html><body></body></html>")
    try:
        BookingScraper.parse_token(page)
        assert False, "harusnya raise ScraperError"
    except ScraperError:
        pass
