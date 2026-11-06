"""Translate the approved read-only Residents sheet to Salma's contracts.

This is an integration-only data adapter. It does not implement an agent,
infer accessibility from disability, or modify the source workbook.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from lastmile_ai.schemas import RESIDENT_COUNT, ResidentProfile
from .load_dataset import load_dataset

MASTER_WORKBOOK = (Path(__file__).resolve().parents[2] / 'data' / 'reference'
                   / 'LastMile_AI_Step1_Master_Dataset.xlsx')

COLUMN_MAP = {
    'Resident ID': 'resident_id',
    'Zone': 'zone',
    'Age': 'age',
    'Elderly 65+': 'elderly_65_plus',
    'Hearing impairment': 'hearing_impairment',
    'Visual impairment': 'visual_impairment',
    'Limited internet': 'limited_internet',
    'Weak mobile coverage': 'weak_mobile_coverage',
    'Emergency app installed': 'emergency_app_installed',
    'In siren area': 'in_siren_area',
    'In signage area': 'in_signage_area',
    'SMS failed EV01': 'sms_failed_ev01',
    'Voice usable': 'voice_usable',
    'Signage readable': 'signage_readable',
    'Policy Age 60+': 'policy_age_60_plus',
}
_TEXT_COLUMNS = {'Resident ID', 'Zone'}
_INTEGER_COLUMNS = {'Age'}

def _as_yes_no(value: Any, *, column: str, resident: str) -> bool:
    if not isinstance(value, str) or value.strip().lower() not in ('yes', 'no'):
        raise ValueError(f'{resident}: {column} must be Yes or No, got {value!r}')
    return value.strip().lower() == 'yes'

def load_resident_profiles(workbook_path: str | Path = MASTER_WORKBOOK) -> tuple[ResidentProfile, ...]:
    """Return validated typed profiles for all 1,000 synthetic residents."""
    residents = load_dataset(workbook_path)['Residents']
    if len(residents) != RESIDENT_COUNT:
        raise ValueError(f'Expected {RESIDENT_COUNT} residents, got {len(residents)}')
    missing_columns = set(COLUMN_MAP) - set(residents.columns)
    if missing_columns:
        raise ValueError(f'Missing resident columns: {sorted(missing_columns)}')
    profiles = []
    for record in residents[list(COLUMN_MAP)].to_dict(orient='records'):
        resident_id = str(record['Resident ID']).strip()
        data = {}
        for source_name, field_name in COLUMN_MAP.items():
            value = record[source_name]
            if source_name in _TEXT_COLUMNS:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f'{resident_id}: {source_name} is empty')
                data[field_name] = value.strip()
            elif source_name in _INTEGER_COLUMNS:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not float(value).is_integer():
                    raise ValueError(f'{resident_id}: invalid age {value!r}')
                data[field_name] = int(value)
            else:
                data[field_name] = _as_yes_no(value, column=source_name, resident=resident_id)
        profiles.append(ResidentProfile(**data))
    ids = [r.resident_id for r in profiles]
    if len(ids) != len(set(ids)):
        raise ValueError('Resident IDs must be unique')
    return tuple(profiles)
