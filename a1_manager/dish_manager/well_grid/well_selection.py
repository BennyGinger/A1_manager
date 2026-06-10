import re

from a1_manager.utils.utility_classes import WellCircleCoord, WellSquareCoord

ROWS = "ABCDEFGH"
COLS = range(1, 13)


def well_name(row, col):
    return f"{row}{col}"


def expand_part(part):
    part = part.strip().upper()

    # Allow ":" as range too
    part = part.replace(":", "-")

    # Single well: A1
    if re.fullmatch(r"[A-H](?:[1-9]|1[0-2])", part):
        return [part]

    # Single row: A
    if re.fullmatch(r"[A-H]", part):
        return [well_name(part, c) for c in COLS]

    # Single column: 1 or 12
    if re.fullmatch(r"(?:[1-9]|1[0-2])", part):
        col = int(part)
        return [well_name(r, col) for r in ROWS]

    # Range
    match = re.fullmatch(
        r"([A-H]?)([1-9]|1[0-2])?-([A-H]?)([1-9]|1[0-2])?",
        part
    )

    if not match:
        raise ValueError(f"Invalid well expression: {part}")

    r1, c1, r2, c2 = match.groups()

    # Row range only: A-C
    if r1 and r2 and not c1 and not c2:
        row_start = ROWS.index(r1)
        row_end = ROWS.index(r2)

        if row_start > row_end:
            row_start, row_end = row_end, row_start

        return [
            well_name(r, c)
            for r in ROWS[row_start:row_end + 1]
            for c in COLS
        ]

    # Column range only: 1-3
    if c1 and c2 and not r1 and not r2:
        col_start = int(c1)
        col_end = int(c2)

        if col_start > col_end:
            col_start, col_end = col_end, col_start

        return [
            well_name(r, c)
            for r in ROWS
            for c in range(col_start, col_end + 1)
        ]

    # Well rectangle: A1-C5
    if r1 and c1 and r2 and c2:
        row_start = ROWS.index(r1)
        row_end = ROWS.index(r2)
        col_start = int(c1)
        col_end = int(c2)

        if row_start > row_end:
            row_start, row_end = row_end, row_start

        if col_start > col_end:
            col_start, col_end = col_end, col_start

        return [
            well_name(r, c)
            for r in ROWS[row_start:row_end + 1]
            for c in range(col_start, col_end + 1)
        ]

    raise ValueError(f"Invalid range: {part}")


def parse_wells(user_input: str | list[str] | None) -> list[str]:
    """
    Parse a user input string specifying wells into a list of well names.
    The input can include:
    - Single wells (e.g., "A1")
    - Rows (e.g., "A")
    - Columns (e.g., "1")
    - Ranges (e.g., "A1-C5", "A-C", "1-3")
    Multiple specifications can be separated by commas (e.g., "A1,A3, B, 1-2").
    
    Note: "A1-C5" will create a rectangle of wells from A1 to C5, including all wells in between.
    """
    
    if user_input is None:
        return [well_name(r, c) for r in ROWS for c in COLS]
    else:
    
        if isinstance(user_input, list):
            wells = []
            for item in user_input:
                if not isinstance(item, str):
                    raise ValueError(f"Invalid item in well selection list: {item}. All items must be strings.")
                wells.extend(parse_wells(item))
                
            return list(dict.fromkeys(wells))
        
        if isinstance(user_input, str):
            if user_input.lower() == 'all':
                return [well_name(r, c) for r in ROWS for c in COLS]
        
            wells = []
            for part in user_input.split(","):
                wells.extend(expand_part(part))

            # Remove duplicates while preserving order
            return list(dict.fromkeys(wells))
        
if __name__ == "__main__":
    # Example usage
    print(parse_wells("A1, A3, B, 1-2, A1-C5"))