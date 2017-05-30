import logging
import re
import urllib.request
from datetime import datetime, timezone, timedelta, date
from typing import List, Tuple, Dict, Optional, Set

from bs4 import BeautifulSoup # type: ignore

BRISBANE_TIME_ZONE = timezone(timedelta(hours=10))

def get_whats_due(subjects: Set[str]) -> List[Dict[str, str]]:
    """
    Takes a list of course codes, finds their course profile id numbers, parses
    UQ's PHP gateway, then returns the coming assessment.
    """
    course_url = 'https://www.uq.edu.au/study/course.html?course_code='
    assessment_url = 'https://www.courses.uq.edu.au/student_section_report' +\
        '.php?report=assessment&profileIds='

    courses_id = []
    for course in subjects:
        try:
            response = urllib.request.urlopen(course_url + course.upper())
            html = response.read().decode('utf-8')
        except:
            continue  # Ignore in the case of failure
        try:
            profile_id_regex = re.compile('profileId=\d*')
            profile_id = profile_id_regex.search(html).group()
            if profile_id != None:
                # Slice to strip the 'profileID='
                courses_id.append(profile_id[10:])
        except:
            continue  # Ignore in the case of failure

    courses = ",".join(courses_id)
    response = urllib.request.urlopen(assessment_url + courses)
    html = response.read().decode('utf-8')
    html = re.sub('<br />', ' ', html)

    soup = BeautifulSoup(html, "html5lib")
    table = soup.find('table', attrs={'class': 'tblborder'})
    rows = table.find_all('tr')[1:]  # ignore the top row of the table

    due_soon = []
    passed_due_date = []
    for row in rows:
        cols = [ ele.text.strip() for ele in row.find_all('td') ]

        subject = cols[0].split(" ")[0] # Strip out irrelevant BS about the subject
        date = cols[2]

        # Some dates are ranges. We only care about the end
        if " - " in date:
            _, date = date.split(" - ")

        now = datetime.now(BRISBANE_TIME_ZONE)

        def try_parsing_date(xs: str) -> Optional[datetime]:
            """
            Brute force all the date formats I've seen UQ use.
            """
            # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
            for fmt in ("%d %b %Y: %H:%M", "%d %b %Y : %H:%M", "%d %b %y %H:%M"):
                try:
                    return datetime.strptime(xs, fmt).replace(tzinfo=BRISBANE_TIME_ZONE)
                except ValueError:
                    pass

            return None

        due = try_parsing_date(date)

        def make_assessment_piece(completed: bool) -> Dict[str, str]:
            return {"subject": subject, "description": cols[1],
                     "date": cols[2], "weighting": cols[3],
                     "completed": completed }

        if due and now > due:
            passed_due_date.append(make_assessment_piece(True))
        else:
            due_soon.append(make_assessment_piece(False))
    # For block ends here

    return due_soon + passed_due_date