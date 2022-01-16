from datetime import date, datetime


def time_gap_not_crossed(curr_time: datetime, old_time: datetime, gap):

    print(gap['value'])
    if gap['type'] == 'd':
        time_diff = curr_time.date() - old_time.date()
        return time_diff.days < gap['value']

    elif gap['type'] == 'min':
        time_diff = curr_time - old_time
        mins = time_diff.seconds // 60
        return mins < gap['value']

    elif gap['type'] == 's':
        time_diff = curr_time - old_time
        return time_diff.seconds < gap['value']


def format_date(d: date):

    date_string = ""

    if d.day < 10:
        date_string += f"0{d.day}"
    else:
        date_string += f"{d.day}"

    date_string += "-"

    if d.month < 10:
        date_string += f"0{d.month}"
    else:
        date_string += f"{d.month}"

    date_string += f"-{d.year}"

    return date_string


def format_time_diff(t1: datetime, t2: datetime):
    t_diff = t1 - t2
    t_days = f"{t_diff.days} days " if t_diff.days > 0 else ""

    hours = (t_diff.seconds // 3600) % 24

    t_hours = f"{hours} hrs " if hours > 0 else ""

    mins = (t_diff.seconds // 60) % 60

    t_mins = ""
    if t_diff.days == 0 and mins != 0:
        t_mins = f"{mins} mins "

    t_secs = ""
    if t_diff.days == 0 and hours == 0 and mins == 0:
        t_secs = f"{t_diff.seconds % 60} s "

    return f"{t_days}{t_hours}{t_mins}{t_secs}ago"
