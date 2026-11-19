"""36 English sentences that are hard to read aloud, 4 per category.

Each item has `keys`: facts the listener must get. A fact is a list of acceptable spoken or written forms; it counts as
heard when any form, after Whisper's English normaliser and with spaces removed, appears in the transcript (also
normalised, spaces removed). An item passes only when every fact is heard. Whisper writes British times with a dot
("7.45"), so both forms count.
All names, codes and figures are made up.
"""

ITEMS = [
    # currency
    ("currency", "The invoice total is £1,249.50 including VAT.",
     [["£1,249.50", "one thousand two hundred and forty nine pounds fifty"], ["VAT", "V A T"]]),
    ("currency", "Tickets start at $18.99 each.",
     [["$18.99", "eighteen dollars ninety nine"]]),
    ("currency", "We paid €3.2 million for the site.",
     [["€3.2 million", "3.2 million euros", "three point two million euros"]]),
    ("currency", "The fee rose from £45 to £60.",
     [["£45", "forty five pounds"], ["£60", "sixty pounds"]]),
    # dates
    ("dates", "Check-in is on 14/02/2027.",
     [["14th of February", "February 14th", "14 February", "February 14", "14 2"], ["2027"]]),
    ("dates", "The deadline is 3 March 2027.",
     [["3rd of March", "March 3rd", "3 March", "March 3"], ["2027"]]),
    ("dates", "The meeting moved to Tue 9 Feb.",
     [["Tuesday"], ["9th of February", "February 9th", "9 February", "February 9", "9th February"]]),
    ("dates", "Founded in 1998, rebuilt in 2004.",
     [["1998"], ["2004"]]),
    # times
    ("times", "Your train leaves at 07:45.",
     [["7:45", "7.45", "quarter to eight", "seven forty five"]]),
    ("times", "The shop is open 9am-5:30pm.",
     [["9am", "9 a.m.", "nine o'clock"], ["5:30pm", "5.30pm", "5:30 p.m.", "half past five", "five thirty"]]),
    ("times", "Call back at 18:00 UK time.",
     [["18:00", "6pm", "6 p.m.", "six o'clock", "eighteen hundred"], ["UK", "U K"]]),
    ("times", "The run took 2h 15m.",
     [["two hours"], ["fifteen minutes"]]),
    # percentages and decimals
    ("decimals", "Occupancy rose 12.5% this quarter.",
     [["12.5%", "twelve point five percent"]]),
    ("decimals", "The error rate fell to 0.03%.",
     [["0.03%", ".03%", "zero point zero three percent", "point zero three percent"]]),
    ("decimals", "Pi is about 3.14159.",
     [["3.14159", "three point one four one five nine"]]),
    ("decimals", "Use a ratio of 3:1.",
     [["3 to 1", "3:1", "three to one"]]),
    # codes
    ("codes", "Your booking reference is QX7-42B.",
     [["QX742B", "Q X 7 4 2 B"]]),
    ("codes", "Flight BA2490 departs from gate 23.",
     [["BA2490", "B A 2490"], ["gate 23"]]),
    ("codes", "Enter code 4417 when asked.",
     [["4417", "four four one seven", "forty four seventeen"]]),
    ("codes", "The postcode is SW1A 1AA.",
     [["SW1A 1AA", "S W 1 A 1 A A"]]),
    # units
    ("units", "The site is 5 km from the airport.",
     [["5 km", "five kilometres", "five kilometers"]]),
    ("units", "Set the oven to 180°C.",
     [["180 degrees", "180°", "one hundred and eighty degrees"]]),
    ("units", "The file is 2.4 GB.",
     [["2.4 GB", "2.4 gigabytes", "two point four gigabytes", "2.4 gig"]]),
    ("units", "Add 250 ml of milk.",
     [["250 ml", "250 millilitres", "250 milliliters", "two hundred and fifty millilitres"]]),
    # ordinals and ranges
    ("ordinals", "She finished 21st out of 300.",
     [["21st", "twenty first"], ["300"]]),
    ("ordinals", "Read chapters 3-7 first.",
     [["3 to 7", "3 through 7", "three to seven"]]),
    ("ordinals", "Rooms 101–110 are on the 1st floor.",
     [["101 to 110", "101 through 110"], ["1st floor", "first floor"]]),
    ("ordinals", "It's the 2nd time this week.",
     [["2nd time", "second time"]]),
    # abbreviations and acronyms
    ("abbreviations", "Dr. Smith works at St. James Hospital.",
     [["Doctor Smith", "Dr Smith"], ["Saint James", "St James"]]),
    ("abbreviations", "The API returns JSON over HTTPS.",
     [["API", "A P I"], ["JSON", "Jason"], ["HTTPS", "H T T P S"]]),
    ("abbreviations", "Our ETA is approx. 10 min.",
     [["ETA", "E T A"], ["approximately"], ["ten minutes"]]),
    ("abbreviations", "Send the PDF to the HR team ASAP.",
     [["PDF", "P D F"], ["HR", "H R"], ["ASAP", "as soon as possible", "A S A P"]]),
    # large numbers and years
    ("large numbers", "The city has 8,945,000 residents.",
     [["8,945,000", "eight million nine hundred and forty five thousand"]]),
    ("large numbers", "Revenue hit $2.7bn in 2026.",
     [["$2.7 billion", "2.7 billion dollars", "two point seven billion dollars"], ["2026"]]),
    ("large numbers", "Population grew by 1,200 to 15,750.",
     [["1,200", "twelve hundred"], ["15,750", "fifteen thousand seven hundred and fifty"]]),
    ("large numbers", "The year 1066 changed England.",
     [["1066", "ten sixty six"]]),
]
