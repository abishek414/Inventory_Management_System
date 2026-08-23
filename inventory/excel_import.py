import openpyxl

from .models import Item, StockTransaction

REQUIRED_HEADERS = {'sku', 'name'}

HEADER_ALIASES = {
    'sku': 'sku',
    'name': 'name',
    'description': 'description',
    'track quantity': 'track_quantity',
    'track_quantity': 'track_quantity',
    'unit': 'unit',
    'quantity': 'quantity',
    'qty': 'quantity',
    'location': 'location',
    'location description': 'location_description',
    'location_description': 'location_description',
    'reorder level': 'reorder_level',
    'reorder_level': 'reorder_level',
    'allow take': 'allow_take',
    'allow_take': 'allow_take',
    'allow borrow': 'allow_borrow',
    'allow_borrow': 'allow_borrow',
}

TRUE_STRINGS = {'yes', 'y', 'true', '1'}
FALSE_STRINGS = {'no', 'n', 'false', '0'}


def _parse_bool(value, default):
    if value is None or str(value).strip() == '':
        return default
    text = str(value).strip().lower()
    if text in TRUE_STRINGS:
        return True
    if text in FALSE_STRINGS:
        return False
    return default


def _parse_int(value, default):
    if value is None or str(value).strip() == '':
        return default
    try:
        return max(0, int(float(value)))
    except (TypeError, ValueError):
        return default


class ExcelImportError(Exception):
    pass


def import_items_from_excel(file_obj, organization, user):
    try:
        workbook = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    except Exception as exc:
        raise ExcelImportError(
            f"Couldn't read that file as an Excel workbook ({exc}). Make sure it's a real .xlsx file."
        )

    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)

    try:
        header_row = next(rows)
    except StopIteration:
        raise ExcelImportError('That file looks empty — no header row found.')

    column_map = {}
    for index, raw_header in enumerate(header_row):
        if raw_header is None:
            continue
        normalized = str(raw_header).strip().lower()
        field = HEADER_ALIASES.get(normalized)
        if field:
            column_map[index] = field

    found_fields = set(column_map.values())
    missing_required = REQUIRED_HEADERS - found_fields
    if missing_required:
        raise ExcelImportError(
            f"Missing required column(s): {', '.join(sorted(missing_required))}. "
            "Download the template below to see the exact headers expected."
        )

    created = 0
    updated = 0
    skipped = []

    for row_number, row in enumerate(rows, start=2):
        if row is None or all(cell in (None, '') for cell in row):
            continue

        values = {}
        for index, field in column_map.items():
            values[field] = row[index] if index < len(row) else None

        sku = str(values.get('sku') or '').strip()
        name = str(values.get('name') or '').strip()
        if not sku or not name:
            skipped.append((row_number, 'missing SKU or Name'))
            continue

        location_name = str(values.get('location') or '').strip()
        location_description = str(values.get('location_description') or '').strip()

        item = Item.objects.filter(organization=organization, sku=sku).first()

        track_quantity = _parse_bool(
            values.get('track_quantity'),
            default=item.track_quantity if item is not None else True,
        )
        row_quantity = 0 if not track_quantity else _parse_int(values.get('quantity'), default=0)

        if item is None:
            item = Item.objects.create(
                organization=organization,
                sku=sku,
                name=name,
                description=str(values.get('description') or ''),
                track_quantity=track_quantity,
                unit=str(values.get('unit') or 'pcs').strip() or 'pcs',
                quantity=row_quantity,
                location_name=location_name,
                location_description=location_description,
                reorder_level=(
                    0 if not track_quantity else _parse_int(values.get('reorder_level'), default=0)
                ),
                allow_take=track_quantity and _parse_bool(values.get('allow_take'), default=True),
                allow_borrow=track_quantity and _parse_bool(values.get('allow_borrow'), default=False),
            )
            StockTransaction.objects.create(
                item=item,
                transaction_type=StockTransaction.EXCEL_IMPORT,
                quantity_change=row_quantity,
                new_location_name=location_name,
                performed_by=user,
                note='Created via Excel import',
            )
            created += 1
        else:
            item.name = name
            item.description = str(values.get('description') or item.description)
            item.track_quantity = track_quantity
            if values.get('unit'):
                item.unit = str(values['unit']).strip()
            previous_location_name = item.location_name
            if location_name:
                item.location_name = location_name
            if location_description:
                item.location_description = location_description
            if not track_quantity:
                item.reorder_level = 0
                item.allow_take = False
                item.allow_borrow = False
            else:
                item.reorder_level = _parse_int(values.get('reorder_level'), default=item.reorder_level)
                item.allow_take = _parse_bool(values.get('allow_take'), default=item.allow_take)
                item.allow_borrow = _parse_bool(values.get('allow_borrow'), default=item.allow_borrow)
            item.quantity += row_quantity
            item.save()
            StockTransaction.objects.create(
                item=item,
                transaction_type=StockTransaction.EXCEL_IMPORT,
                quantity_change=row_quantity,
                previous_location_name=previous_location_name,
                new_location_name=item.location_name,
                performed_by=user,
                note='Updated via Excel import',
            )
            updated += 1

    return {'created': created, 'updated': updated, 'skipped': skipped}


def build_template_workbook():
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Inventory'
    sheet.append([
        'SKU', 'Name', 'Description', 'Track Quantity', 'Unit', 'Quantity', 'Location',
        'Location Description', 'Reorder Level', 'Allow Take', 'Allow Borrow',
    ])
    sheet.append([
        'DRILL-001', 'Cordless drill', '18V, comes with 2 batteries', 'Yes', 'pcs', 10,
        'Main warehouse', 'Aisle 3, shelf B', 2, 'No', 'Yes',
    ])
    sheet.append([
        'SAND-BULK', 'Sand (bulk pile)', 'Not counted individually', 'No', '', '',
        'Yard 2', 'Behind the main building', '', '', '',
    ])
    return workbook
