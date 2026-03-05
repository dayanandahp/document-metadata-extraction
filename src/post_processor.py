"""
Post-Processing Module
Cleans and normalizes extracted metadata
"""

import re
from datetime import datetime


def post_process(metadata: dict) -> dict:
    """Clean and normalize the extracted metadata"""
    
    cleaned = {}
    
    cleaned['Agreement Value'] = clean_agreement_value(
        metadata.get('agreement_value', '')
    )
    
    cleaned['Agreement Start Date'] = clean_date(
        metadata.get('agreement_start_date', '')
    )
    
    cleaned['Agreement End Date'] = clean_date(
        metadata.get('agreement_end_date', '')
    )
    
    cleaned['Renewal Notice (Days)'] = clean_renewal_days(
        metadata.get('renewal_notice_days', '')
    )
    
    cleaned['Party One'] = clean_party_name(
        metadata.get('party_one', '')
    )
    
    cleaned['Party Two'] = clean_party_name(
        metadata.get('party_two', '')
    )
    
    return cleaned


def clean_agreement_value(value) -> str:
    """Extract numeric value only"""
    if not value or value == "" or str(value).lower() == "nan":
        return ""
    
    value_str = str(value)
    value_str = value_str.replace('Rs', '').replace('rs', '')
    value_str = value_str.replace('₹', '').replace('/-', '')
    value_str = value_str.replace(',', '').replace(' ', '')
    
    numbers = re.findall(r'\d+', value_str)
    if numbers:
        return numbers[0]
    
    return str(value)


def clean_date(date_str) -> str:
    """Normalize date to DD.MM.YYYY format"""
    if not date_str or date_str == "" or str(date_str).lower() == "nan":
        return ""
    
    date_str = str(date_str).strip()
    
    if re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_str):
        return date_str
    
    date_formats = [
        '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y',
        '%Y-%m-%d', '%d %B %Y', '%d %b %Y',
        '%B %d, %Y', '%d.%m.%y',
    ]
    
    for fmt in date_formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime('%d.%m.%Y')
        except ValueError:
            continue
    
    return date_str


def clean_renewal_days(value) -> str:
    """Ensure renewal notice is a plain number in days"""
    if not value or value == "" or str(value).lower() == "nan" or str(value).lower() == "null":
        return ""
    
    value_str = str(value).strip()
    
    numbers = re.findall(r'\d+', value_str)
    if numbers:
        return numbers[0]
    
    return ""


def _strip_titles(name: str) -> str:
    """Remove honorific titles from names.
    
    Only strip when the title is followed by a SPACE so that
    names like 'MR.K.Kuttan' (where MR is part of the written name) are preserved.
    Also strips bare-word titles (SRI, SHRI, SMT) that appear without a period.
    """
    # Titles with period — require at least one whitespace after so we don't
    # break names like "MR.K.Kuttan" or "MRS.Asha" where the LLM already decided
    # the title is part of the name format.
    dotted_title_patterns = [
        r'Prof\.\s+', r'Dr\.\s+', r'Sri\.\s+', r'Smt\.\s+',
        r'Shri\.\s+', r'Mrs\.\s+', r'Mr\.\s+', r'Ms\.\s+',
        r'PROF\.\s+', r'DR\.\s+', r'SRI\.\s+', r'SMT\.\s+',
        r'SHRI\.\s+', r'MRS\.\s+', r'MR\.\s+', r'MS\.\s+',
    ]
    
    # Bare-word titles (no period) — always require a trailing space
    bare_title_patterns = [
        r'SRI\s+', r'SHRI\s+', r'SMT\s+',
        r'Sri\s+', r'Shri\s+', r'Smt\s+',
    ]
    
    all_patterns = dotted_title_patterns + bare_title_patterns
    
    for pattern in all_patterns:
        # Strip from beginning of name
        name = re.sub(r'^' + pattern, '', name)
        # Strip after "& " (for multi-party names)
        name = re.sub(r'(?<=& )' + pattern, '', name)
        # Strip after "and/or "
        name = re.sub(r'(?<=and/or )' + pattern, '', name)
    return name


def clean_party_name(name) -> str:
    """Clean party names - strip titles and normalize whitespace"""
    if not name or name == "" or str(name).lower() == "nan":
        return ""
    
    name = str(name).strip()
    
    # Step 1: Strip honorific titles (Mr., Mrs., Prof., Sri., etc.)
    name = _strip_titles(name)
    
    # Step 2: Remove trailing period ONLY if it's at the very end and not part of abbreviation
    # e.g., "GALINATO." → "GALINATO" but "Balaji.R" stays
    if name.endswith('.') and not re.match(r'.*\.\w+\.$', name):
        # Check if the dot is after a full word (not abbreviation)
        if len(name) > 2 and name[-2] != '.':
            name = name[:-1]
    
    # Step 3: Normalize whitespace
    name = ' '.join(name.split())
    
    # Step 4: Normalize "&" spacing
    name = re.sub(r'\s*&\s*', ' & ', name)
    
    # Step 5: Strip leading/trailing whitespace again after all transformations
    name = name.strip()
    
    return name


# ===== TEST =====
if __name__ == "__main__":
    # Test title stripping
    print("Testing title stripping:")
    title_tests = [
        ("Mr. Balaji.R", "Balaji.R"),
        ("Prof. K. Parthasarathy", "K. Parthasarathy"),
        ("Sri. P.M. Narayana Namboodri", "P.M. Narayana Namboodri"),
        ("MR.K.Kuttan", "MR.K.Kuttan"),  # MR. glued to name → preserved
        ("Mr. P. JohnsonRavikumar", "P. JohnsonRavikumar"),
        ("Mr. Saravanan BV", "Saravanan BV"),
        ("SRI VYSHNAVI DAIRY SPECIALITIES Private Ltd.", "VYSHNAVI DAIRY SPECIALITIES Private Ltd"),
    ]
    for input_name, expected in title_tests:
        result = clean_party_name(input_name)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{input_name}' → '{result}' (expected: '{expected}')")
    print()
    test_cases = [
        "Mr. P C MATHEW",
        "Mr. L GOPINATH",
        "Prof. K. Parthasarathy",
        "Mr. Saravanan BV",
        "Antonio Levy S. Ingles. Jr. and/or Mary Rose C. Ingles",
        "GERALDINE O. GALINATO.",
        "Mr. P. JohnsonRavikumar",
        "Balaji.R",
        "MR.K.Kuttan",
        "SRI VYSHNAVI DAIRY SPECIALITIES Private Ltd.",
    ]
    
    print("Testing party name cleaning:")
    for name in test_cases:
        cleaned = clean_party_name(name)
        print(f"  '{name}' → '{cleaned}'")