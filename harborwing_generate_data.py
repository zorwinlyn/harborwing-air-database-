"""
HarborWing Air synthetic data generator
Generates at least 50 rows in each of the 11 core tables.

Requirements:
    pip install Faker mysql-connector-python

IMPORTANT:
- Back up your database before running.
- This script introspects the existing schema and uses its real column names.
- It generates fictional/demo data only.
- It will not delete existing records.
- If a column or constraint has unusual business rules, adjust the generated value
  after reviewing the schema. Always verify row counts after running.
"""

import random
import re
from datetime import date, datetime, timedelta, time
from decimal import Decimal
import mysql.connector
from faker import Faker

SEED = 20261016
ROWS_PER_TABLE = 50
DB_NAME = "harborwing_air"

random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

TABLES = [
    "booking_agent",
    "passenger",
    "airport",
    "calendar_date",
    "flight_schedule",
    "reservation",
    "payment",
    "flight_leg",
    "flight_cost",
    "reservation_payment",
    "reservation_leg",
]

# Update these connection values if your local MySQL settings differ.
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "winwin19",  # Enter your MySQL root password between the quotes if needed.
    "database": DB_NAME,
}

def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")

    # Inspect columns, primary keys, and foreign keys from the real schema.
    meta = {}
    for table in TABLES:
        cur.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE,
                   COLUMN_DEFAULT, EXTRA, COLUMN_KEY
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s
            ORDER BY ORDINAL_POSITION
        """, (DB_NAME, table))
        cols = cur.fetchall()
        if not cols:
            raise RuntimeError(f"Table '{table}' was not found in {DB_NAME}. Check SHOW TABLES.")
        cur.execute("""
            SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s
              AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (DB_NAME, table))
        fks = cur.fetchall()
        meta[table] = {"cols": cols, "fks": fks}

    # Generate the calendar first, including a broad validity range.
    today = date.today()
    calendar_dates = [today + timedelta(days=i) for i in range(-365, 365)]
    calendar_dates = list(dict.fromkeys(calendar_dates))
    # The table needs 50+ rows, but more dates make flight/cost dates easier to satisfy.

    # Table-specific candidate rows use common names from the assignment.
    data = {t: [] for t in TABLES}
    agent_ids, passenger_ids, airport_codes, flight_numbers = [], [], [], []
    reservation_ids, payment_ids, leg_ids = [], [], []

    # Helpers: get column names and insert values only into non-generated columns.
    def colnames(table):
        return [c["COLUMN_NAME"] for c in meta[table]["cols"]]

    def choose_col(table, *candidates):
        mapping = {norm(c): c for c in colnames(table)}
        for cand in candidates:
            if norm(cand) in mapping:
                return mapping[norm(cand)]
        return None

    def insert_rows(table, rows):
        if not rows:
            return
        cols = list(rows[0].keys())
        sql = f"INSERT IGNORE INTO `{table}` ({','.join('`'+c+'`' for c in cols)}) VALUES ({','.join(['%s']*len(cols))})"
        cur.executemany(sql, [tuple(row.get(c) for c in cols) for row in rows])
        conn.commit()
        print(f"{table}: attempted {len(rows)} rows")

    def add(table, row):
        # Fill unspecified nullable columns with None; don't supply auto-increment fields.
        out = {}
        for c in meta[table]["cols"]:
            name = c["COLUMN_NAME"]
            if "auto_increment" in (c["EXTRA"] or "").lower():
                continue
            if name in row:
                out[name] = row[name]
            elif c["IS_NULLABLE"] == "YES" or c["COLUMN_DEFAULT"] is not None:
                continue
            else:
                # generic required-value fallback based on datatype/name
                out[name] = generic_value(table, c)
        data[table].append(out)

    def generic_value(table, c):
        n, typ = c["COLUMN_NAME"].lower(), c["DATA_TYPE"].lower()
        if "email" in n: return fake.unique.email()
        if "phone" in n: return fake.numerify("09#########")
        if "first" in n: return fake.first_name()
        if "last" in n: return fake.last_name()
        if "name" in n: return fake.word().title()
        if "address" in n: return fake.street_address()
        if "city" in n: return fake.city()
        if "country" in n: return fake.country()
        if "state" in n or "province" in n: return fake.state()
        if "status" in n: return random.choice(["CONFIRMED", "PENDING", "CANCELLED"])
        if "code" in n: return fake.unique.bothify("??##").upper()
        if "amount" in n or "cost" in n or "price" in n: return Decimal(str(round(random.uniform(25, 900), 2)))
        if "party" in n or "day_of_month" in n or "day" == n: return random.randint(1, 28)
        if typ in ("int", "bigint", "smallint", "mediumint", "tinyint"): return random.randint(1, 1000)
        if typ in ("decimal", "numeric", "float", "double"): return Decimal("100.00")
        if typ == "date": return today
        if typ in ("datetime", "timestamp"): return datetime.now().replace(microsecond=0)
        if typ == "time": return time(12, 0)
        if typ == "year": return today.year
        if typ in ("tinyint", "bit"): return 1
        if typ in ("varchar", "char", "text", "mediumtext", "longtext"): return fake.word()[:40]
        return None

    # First, populate parent/reference tables.
    t = "booking_agent"
    for i in range(ROWS_PER_TABLE):
        row = {}
        for candidates, value in [
            (("agent_id", "booking_agent_id"), i + 1),
            (("first_name",), fake.first_name()),
            (("last_name",), fake.last_name()),
            (("name", "agent_name"), fake.name()),
            (("email", "email_address"), f"agent{i+1}@example.test"),
            (("phone", "phone_number"), f"09{random.randint(100000000,999999999)}"),
            (("details", "additional_details", "other_details"), "Fictional demo booking agent"),
        ]:
            c = choose_col(t, *candidates)
            if c and c not in row: row[c] = value
        add(t, row)
    insert_rows(t, data[t])
    data[t] = []

    t = "passenger"
    for i in range(ROWS_PER_TABLE):
        row = {}
        for candidates, value in [
            (("passenger_id",), i + 1),
            (("first_name",), fake.first_name()),
            (("second_name", "middle_name"), fake.first_name()),
            (("last_name",), fake.last_name()),
            (("phone", "phone_number"), f"09{random.randint(100000000,999999999)}"),
            (("email", "email_address"), f"passenger{i+1}@example.test"),
            (("address_line1", "address_line_1", "address"), fake.street_address()),
            (("address_line2", "address_line_2"), fake.secondary_address()),
            (("city",), fake.city()),
            (("state_province_county", "state", "province"), fake.state()),
            (("country",), "Philippines"),
            (("other_details", "details"), "Fictional synthetic passenger"),
        ]:
            c = choose_col(t, *candidates)
            if c and c not in row: row[c] = value
        add(t, row)
    insert_rows(t, data[t]); data[t] = []

    t = "airport"
    codes = ["MNL", "CEB", "PPS", "ILO", "DVO", "BCD", "KLO", "TAG", "USU", "MPH",
             "LAO", "TUG", "CGY", "ZAM", "GES", "BXU", "DGT", "SJI", "ENI", "RXS",
             "BAG", "SUG", "TAC", "VRC", "MBT", "CRM", "CYZ", "LGP", "OZC", "DPL",
             "SFE", "WNP", "DRP", "TBH", "OMC", "PAG", "CBO", "IPE", "TWT", "BPA",
             "MRQ", "RGT", "SFS", "SWL", "JOL", "TDG", "IGN", "KSR", "TGB", "LLC"]
    locations = [fake.city() for _ in codes]
    for i, code in enumerate(codes):
        row = {}
        for candidates, value in [
            (("airport_code", "code"), code),
            (("airport_name", "name"), f"{locations[i]} Regional Airport"),
            (("location",), locations[i]),
            (("other_details", "details"), "Fictional/demo airport record"),
        ]:
            c = choose_col(t, *candidates)
            if c: row[c] = value
        add(t, row)
    insert_rows(t, data[t]); data[t] = []

    t = "calendar_date"
    date_col = choose_col(t, "calendar_date", "date", "date_value")
    day_col = choose_col(t, "day_of_month", "day")
    business_col = choose_col(t, "is_business_day", "business_day", "business_day_indicator")
    for d in calendar_dates:
        row = {}
        if date_col: row[date_col] = d
        if day_col: row[day_col] = d.day
        if business_col: row[business_col] = 1 if d.weekday() < 5 else 0
        add(t, row)
    insert_rows(t, data[t]); data[t] = []

    # Get IDs/codes actually present after insertion, including any pre-existing rows.
    def values(table, *candidate_names):
        c = choose_col(table, *candidate_names)
        if not c: return []
        cur.execute(f"SELECT `{c}` FROM `{table}`")
        return [r[c] for r in cur.fetchall()]

    agent_ids = values("booking_agent", "agent_id", "booking_agent_id")
    passenger_ids = values("passenger", "passenger_id")
    airport_codes = values("airport", "airport_code", "code")
    date_values = values("calendar_date", "calendar_date", "date", "date_value")

    if not (agent_ids and passenger_ids and airport_codes and date_values):
        raise RuntimeError("Could not detect IDs/codes in parent tables. Review table column names.")

    # Flights/schedules
    t = "flight_schedule"
    flight_numbers = []
    for i in range(ROWS_PER_TABLE):
        origin = airport_codes[i % len(airport_codes)]
        dest = airport_codes[(i + 1) % len(airport_codes)]
        dep = datetime.combine(today + timedelta(days=i % 180), time(random.choice([6, 9, 12, 15, 18])))
        arr = dep + timedelta(hours=random.randint(1, 5))
        row = {}
        fields = [
            (("flight_number", "flight_no", "flight_id"), f"HW{100+i}"),
            (("airline_code",), "HW"),
            (("usual_aircraft_type_code", "aircraft_type_code", "aircraft_code"), random.choice(["AT72", "A320", "E190", "B738"])),
            (("origin_airport_code", "origin_airport", "origin_code"), origin),
            (("destination_airport_code", "destination_airport", "destination_code"), dest),
            (("scheduled_departure_datetime", "scheduled_departure", "scheduled_departure_time"), dep),
            (("scheduled_arrival_datetime", "scheduled_arrival", "scheduled_arrival_time"), arr),
        ]
        for candidates, value in fields:
            c = choose_col(t, *candidates)
            if c: row[c] = value
        add(t, row)
    insert_rows(t, data[t]); data[t] = []
    flight_numbers = values("flight_schedule", "flight_number", "flight_no", "flight_id")

    # Reservations
    t = "reservation"
    reservation_ids = []
    rid_col = choose_col(t, "reservation_id")
    for i in range(ROWS_PER_TABLE):
        row = {}
        fields = [
            (("reservation_id",), i + 1),
            (("passenger_id",), passenger_ids[i % len(passenger_ids)]),
            (("agent_id", "booking_agent_id"), agent_ids[i % len(agent_ids)] if i % 2 else None),
            (("reservation_status_code", "status_code", "reservation_status"), random.choice(["CONFIRMED", "PENDING", "CANCELLED"])),
            (("ticket_type_code",), random.choice(["STD", "FLEX", "SAVER"])),
            (("travel_class_code",), random.choice(["ECO", "BUS", "FST"])),
            (("created_at", "creation_datetime", "creation_date_time", "reservation_datetime"), datetime.now().replace(microsecond=0) - timedelta(days=random.randint(1, 180))),
            (("party_size", "number_in_party"), random.randint(1, 5)),
            (("reservation_code", "code"), f"HW{SEED%10000}{i+1:04d}"),
        ]
        for candidates, value in fields:
            c = choose_col(t, *candidates)
            if c: row[c] = value
        add(t, row)
    insert_rows(t, data[t]); data[t] = []
    reservation_ids = values("reservation", "reservation_id")

    # Payments
    t = "payment"
    for i in range(ROWS_PER_TABLE):
        row = {}
        fields = [
            (("payment_id",), i + 1),
            (("payment_status_code", "status_code", "payment_status"), random.choice(["PAID", "PENDING", "REFUNDED"])),
            (("payment_date",), today - timedelta(days=random.randint(0, 180))),
            (("payment_amount", "amount"), Decimal(str(round(random.uniform(50, 1200), 2)))),
        ]
        for candidates, value in fields:
            c = choose_col(t, *candidates)
            if c: row[c] = value
        add(t, row)
    insert_rows(t, data[t]); data[t] = []
    payment_ids = values("payment", "payment_id")

    # Flight legs
    t = "flight_leg"
    for i in range(ROWS_PER_TABLE):
        origin = airport_codes[i % len(airport_codes)]
        dest = airport_codes[(i + 1) % len(airport_codes)]
        dep = datetime.combine(today + timedelta(days=i % 180), time(8, 0)) + timedelta(minutes=15*i)
        arr = dep + timedelta(hours=2)
        row = {}
        fields = [
            (("leg_id",), i + 1),
            (("flight_number", "flight_no", "flight_id"), flight_numbers[i % len(flight_numbers)]),
            (("origin_airport_code", "origin_airport", "origin_code"), origin),
            (("destination_airport_code", "destination_airport", "destination_code"), dest),
            (("actual_departure_datetime", "actual_departure", "actual_departure_time"), dep),
            (("actual_arrival_datetime", "actual_arrival", "actual_arrival_time"), arr),
        ]
        for candidates, value in fields:
            c = choose_col(t, *candidates)
            if c: row[c] = value
        add(t, row)
    insert_rows(t, data[t]); data[t] = []
    leg_ids = values("flight_leg", "leg_id")

    # Flight costs, with a composite key and valid date references.
    t = "flight_cost"
    flight_col = choose_col(t, "flight_number", "flight_no", "flight_id")
    aircraft_col = choose_col(t, "aircraft_type_code", "aircraft_code")
    from_col = choose_col(t, "valid_from_date", "valid_from")
    to_col = choose_col(t, "valid_to_date", "valid_to")
    cost_col = choose_col(t, "cost_amount", "cost", "amount")
    for i in range(ROWS_PER_TABLE):
        dfrom = today - timedelta(days=180) + timedelta(days=i)
        dto = dfrom + timedelta(days=90)
        row = {}
        if flight_col: row[flight_col] = flight_numbers[i % len(flight_numbers)]
        if aircraft_col: row[aircraft_col] = random.choice(["AT72", "A320", "E190", "B738"])
        if from_col: row[from_col] = dfrom
        if to_col: row[to_col] = dto
        if cost_col: row[cost_col] = Decimal(str(round(random.uniform(75, 900), 2)))
        add(t, row)
    insert_rows(t, data[t]); data[t] = []

    # Unique link pairs; make 50+ distinct pairs for each bridge table.
    t = "reservation_payment"
    rcol = choose_col(t, "reservation_id")
    pcol = choose_col(t, "payment_id")
    pairs = set()
    i = 0
    while len(pairs) < ROWS_PER_TABLE:
        pairs.add((reservation_ids[i % len(reservation_ids)], payment_ids[(i * 7 + 3) % len(payment_ids)]))
        i += 1
    for r, p in pairs:
        row = {}
        if rcol: row[rcol] = r
        if pcol: row[pcol] = p
        add(t, row)
    insert_rows(t, data[t]); data[t] = []

    t = "reservation_leg"
    rcol = choose_col(t, "reservation_id")
    lcol = choose_col(t, "leg_id")
    pairs = set()
    i = 0
    while len(pairs) < ROWS_PER_TABLE:
        pairs.add((reservation_ids[i % len(reservation_ids)], leg_ids[(i * 9 + 2) % len(leg_ids)]))
        i += 1
    for r, l in pairs:
        row = {}
        if rcol: row[rcol] = r
        if lcol: row[lcol] = l
        add(t, row)
    insert_rows(t, data[t]); data[t] = []

    # Report final counts.
    print("\nFINAL ROW COUNTS")
    for table in TABLES:
        cur.execute(f"SELECT COUNT(*) AS n FROM `{table}`")
        count = cur.fetchone()["n"]
        print(f"{table:24s} {count}")
        if count < ROWS_PER_TABLE:
            print(f"  WARNING: fewer than {ROWS_PER_TABLE} rows. Check schema/constraints and any errors above.")

    cur.close()
    conn.close()
    print("\nFinished. Review all warnings and verify your data in MySQL Workbench.")

if __name__ == "__main__":
    main()
