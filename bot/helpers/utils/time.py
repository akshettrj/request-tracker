from datetime import date, datetime, timedelta


def check_time_gap_crossed(curr_time: datetime, old_time: datetime, gap):

    if gap['type'] == 'd':
        time_diff = curr_time.date() - old_time.date()
        time_change = timedelta(days=gap['value'])
        appropriate_time = datetime.combine(old_time.date() + time_change, datetime.min.time())
        return time_diff.days >= gap['value'], appropriate_time

    elif gap['type'] == 'min':
        time_diff = curr_time - old_time
        mins = time_diff.seconds // 60
        time_change = timedelta(minutes=gap['value'])
        appropriate_time = (old_time + time_change)
        return mins >= gap['value'], appropriate_time

    elif gap['type'] == 's':
        time_diff = curr_time - old_time
        time_change = timedelta(seconds=gap['value'])
        appropriate_time = (old_time + time_change)
        return time_diff.seconds >= gap['value'], appropriate_time


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


def format_time_diff(t1: datetime|None, t2: datetime|None, t_diff=None):
    t_diff = t1 - t2 if t_diff is None else t_diff
    t_days = f"{t_diff.days} days " if t_diff.days > 0 else ""

    hours = (t_diff.seconds // 3600) % 24

    t_hours = f"{hours} hrs " if hours > 0 else ""

    mins = (t_diff.seconds // 60) % 60

    t_mins = ""
    if mins != 0:
        t_mins = f"{mins} mins "

    t_secs = f"{t_diff.seconds % 60} s "

    return f"{t_days}{t_hours}{t_mins}{t_secs}ago"
