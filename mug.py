#!/usr/bin/env python3
"""
mug - Company-Targeted Password Wordlist Generator
Inspired by cupp | Built for authorized penetration testing
"""

import argparse
import itertools
import os
import sys
from datetime import datetime
from typing import Dict, List, Set, Tuple

VERSION = "1.0.0"

BANNER = r"""
    ) ) )
  .-------.
  |       |--,
  |  MUG  |  )
  |       |--'
  '-------'
  Company-Targeted Wordlist Generator v{version}
  github.com/Dibit1234/Mug  |  For authorized testing only
""".format(version=VERSION)

COMPLEXITY_INFO = {
    1: ("Minimal", "raw words + basic case variants              (~hundreds)"),
    2: ("Low    ", "words + numbers/years + special chars        (~thousands)"),
    3: ("Medium ", "leet speak + same-category 2-word combos     (~tens of thousands)"),
    4: ("High   ", "cross-category combos + full mutations       (~hundreds of thousands)"),
    5: ("Massive", "3-way combos + full mutation matrix          (~millions)"),
}

LEET_MAP: Dict[str, List[str]] = {
    'a': ['@', '4'],
    'e': ['3'],
    'i': ['1', '!'],
    'o': ['0'],
    's': ['$', '5'],
    't': ['7'],
    'g': ['9'],
    'b': ['8'],
    'l': ['1'],
    'z': ['2'],
}

SUFFIXES_SMALL  = ['1', '!', '123', '1234', '@123', '2024', '2025']
SUFFIXES_MEDIUM = SUFFIXES_SMALL + ['12', '12345', '#', '$', '!!', '!@#', '01', '007', '!123', '#123']
SUFFIXES_LARGE  = SUFFIXES_MEDIUM + [
    '1!', '2!', '@', '2020', '2021', '2022', '2023',
    '@2024', '@2025', '!2024', '!2025', '123!', '1234!', '123@', '0', '00', '000',
]

PREFIXES_SMALL  = ['']
PREFIXES_MEDIUM = ['', '1', '!', 'The']
PREFIXES_LARGE  = ['', '1', '!', '@', '123', 'The', 'My', 'our']

SEPARATORS_SMALL  = ['', '_']
SEPARATORS_MEDIUM = ['', '_', '-']
SEPARATORS_LARGE  = ['', '_', '-', '@', '.']

CURRENT_YEAR = str(datetime.now().year)
RECENT_YEARS = [str(y) for y in range(int(CURRENT_YEAR) - 4, int(CURRENT_YEAR) + 2)]


# ---------------------------------------------------------------------------
# Terminal helpers
# ---------------------------------------------------------------------------

def _init_color() -> bool:
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return True

_COLOR = _init_color()

def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR else text

def _green(t: str)  -> str: return _c(t, '32')
def _yellow(t: str) -> str: return _c(t, '33')
def _cyan(t: str)   -> str: return _c(t, '36')
def _bold(t: str)   -> str: return _c(t, '1')
def _dim(t: str)    -> str: return _c(t, '2')
def _red(t: str)    -> str: return _c(t, '31')
def _magenta(t: str)-> str: return _c(t, '35')


def _section(title: str) -> None:
    width = 44
    bar = _dim('-' * width)
    print(f"\n  {_bold(_cyan('[*]'))} {_bold(title)}")
    print(f"  {bar}")


def _added(val: str) -> None:
    print(f"  {_dim('  added ->  ' + val)}")


def _ask(label: str, hint: str = "", required: bool = False) -> str:
    if hint:
        print(_dim(f"  ( {hint} )"))
    prompt_str = f"  {_green('[>]')} {label}: "
    while True:
        try:
            val = input(prompt_str).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Interrupted.")
            sys.exit(0)
        if val or not required:
            return val
        print(f"  {_red('[!]')} This field is required.")


def _ask_yn(label: str, default_yes: bool = False) -> bool:
    default_str = _dim("[Y/n]" if default_yes else "[y/N]")
    prompt_str = f"  {_green('[>]')} {label} {default_str}: "
    try:
        val = input(prompt_str).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Interrupted.")
        sys.exit(0)
    if val in ('y', 'yes'):
        return True
    if val in ('n', 'no'):
        return False
    return default_yes


def _ask_int(label: str, default: int, lo: int, hi: int) -> int:
    while True:
        raw = _ask(label, hint=f"enter {lo}-{hi}, blank = {default}")
        if not raw:
            return default
        try:
            val = int(raw)
            if lo <= val <= hi:
                return val
            print(f"  {_red('[!]')} Enter a number between {lo} and {hi}.")
        except ValueError:
            print(f"  {_red('[!]')} Please enter a number.")


def _ask_list(item_label: str, hint: str = "") -> List[str]:
    """Collect a list one item at a time with add-another loops."""
    results: List[str] = []
    if hint:
        print(_dim(f"  ( {hint} )"))
    first = _ask(f"First {item_label}  (blank to skip)")
    if not first:
        return []
    results.append(first)
    _added(first)
    while True:
        if not _ask_yn(f"Add another {item_label}?"):
            break
        nxt = _ask(item_label, required=True)
        results.append(nxt)
        _added(nxt)
    return results


# ---------------------------------------------------------------------------
# Interactive profile wizard — one question at a time (cupp-style)
# ---------------------------------------------------------------------------

def collect_profile() -> Tuple[dict, dict]:
    """Walk through the company profile interactively. Returns (profile, settings)."""
    profile: dict = {}

    print(f"\n  {_dim('Fill in what you know. Blank entries are skipped.')}")
    print(f"  {_dim('For list fields, add items one at a time.')}")

    # ── Company basics ───────────────────────────────────────────────────────
    _section("Company Info")

    profile['company_name']  = _ask("Company full name", required=True)
    profile['company_short'] = _ask("Short name / abbreviation",
                                    hint="e.g. MS for Microsoft")
    profile['ticker']        = _ask("Stock ticker symbol",
                                    hint="e.g. ACME, MSFT, GOOG")
    if profile['ticker']:
        _added(profile['ticker'])
    profile['domain']        = _ask("Primary domain", hint="e.g. acme.com")
    profile['industry']      = _ask("Industry / sector",
                                    hint="e.g. finance, healthcare, defence")
    profile['city']          = _ask("HQ city")
    profile['country']       = _ask("Country")
    profile['founded_year']  = _ask("Year founded", hint="e.g. 1998")

    # ── Key people ───────────────────────────────────────────────────────────
    _section("Key People")

    profile['ceo'] = _ask("CEO / Founder name",
                           hint="first name, last name, or both")
    if profile['ceo']:
        _added(profile['ceo'])

    profile['other_names'] = _ask_list(
        "key person",
        hint="other executives, founders, sysadmins — first/last or both"
    )

    # ── Technologies & products ──────────────────────────────────────────────
    _section("Technologies & Products")

    profile['technologies'] = _ask_list(
        "technology",
        hint="e.g. Azure, SAP, Python, Oracle, Cisco, VMware"
    )
    profile['products'] = _ask_list(
        "product or service",
        hint="product lines, SaaS tools, internal platforms"
    )

    # ── Departments & keywords ───────────────────────────────────────────────
    _section("Departments & Keywords")

    profile['departments'] = _ask_list(
        "department name",
        hint="e.g. HR, Finance, ITSec, Legal, Ops"
    )
    profile['keywords'] = _ask_list(
        "keyword",
        hint="project codenames, slogans, internal nicknames, anything relevant"
    )

    # ── Extra details ────────────────────────────────────────────────────────
    _section("Extra Details")
    print(_dim("  ( optional — improves coverage )"))
    print()

    profile['aliases'] = _ask_list(
        "alias or former name",
        hint="acquired brands, former company names, trading names"
    )
    profile['phone'] = _ask("Company phone number",
                             hint="area code digits will be added to mutations")
    if profile['phone']:
        _added(profile['phone'])
    profile['zipcode'] = _ask("Postal / ZIP code",
                               hint="e.g. 90210 or EC1A 1BB")
    if profile['zipcode']:
        _added(profile['zipcode'])

    # ── Generation settings ──────────────────────────────────────────────────
    _section("Generation Settings")

    print(f"\n  {_bold('Complexity levels:')}\n")
    for k, (name, desc) in COMPLEXITY_INFO.items():
        bullet = _cyan(str(k))
        print(f"    {bullet}  {_bold(name)}  {_dim(desc)}")
    print()

    complexity = _ask_int("Complexity level", default=3, lo=1, hi=5)
    min_len    = _ask_int("Minimum password length", default=6, lo=1, hi=64)
    max_len    = _ask_int("Maximum password length", default=20,
                          lo=min_len + 1, hi=128)
    separate   = not _ask_yn("Combine inputs into multi-word passwords?",
                              default_yes=True)

    emails = False
    if profile.get('domain'):
        emails = _ask_yn("Generate corporate email address patterns?")

    merge_raw  = _ask("Merge with an existing wordlist",
                      hint="path to existing .txt file, blank to skip")
    merge_file = merge_raw.strip() if merge_raw else ""

    out_default = (
        (profile['company_name'] or 'mug').lower().replace(' ', '_') + '_wordlist.txt'
    )
    out_raw     = _ask("Output filename", hint=f"blank = {out_default}")
    output_file = out_raw if out_raw else out_default

    settings = {
        'complexity':  complexity,
        'min_len':     min_len,
        'max_len':     max_len,
        'separate':    separate,
        'emails':      emails,
        'merge_file':  merge_file,
        'output_file': output_file,
    }

    # ── Profile summary ──────────────────────────────────────────────────────
    _section("Profile Summary")
    _print_summary(profile, settings)
    print()

    if not _ask_yn("Generate wordlist with these settings?", default_yes=True):
        print("\n  Aborted.")
        sys.exit(0)

    return profile, settings


def _print_summary(profile: dict, settings: dict) -> None:
    def _row(label: str, value: str) -> None:
        if not value or value == '-':
            return
        print(f"  {_cyan(label.ljust(16))} {value}")

    company = profile.get('company_name', '')
    if profile.get('company_short'):
        company += f"  ({profile['company_short']})"
    if profile.get('ticker'):
        company += f"  [{profile['ticker']}]"

    print()
    _row("Company",      company)
    _row("Domain",       profile.get('domain', ''))
    _row("Industry",     profile.get('industry', ''))
    loc = ", ".join(filter(None, [profile.get('city'), profile.get('country')]))
    _row("Location",     loc)
    _row("Founded",      profile.get('founded_year', ''))
    _row("CEO/Founder",  profile.get('ceo', ''))
    _row("Key people",   ", ".join(profile.get('other_names', [])))
    _row("Technologies", ", ".join(profile.get('technologies', [])))
    _row("Products",     ", ".join(profile.get('products', [])))
    _row("Departments",  ", ".join(profile.get('departments', [])))
    _row("Keywords",     ", ".join(profile.get('keywords', [])))
    _row("Aliases",      ", ".join(profile.get('aliases', [])))
    _row("Phone",        profile.get('phone', ''))
    _row("ZIP/Postal",   profile.get('zipcode', ''))

    print()
    lvl = settings['complexity']
    _row("Complexity",   f"{lvl} - {COMPLEXITY_INFO[lvl][0].strip()}")
    _row("Length",       f"{settings['min_len']}-{settings['max_len']} chars")
    _row("Mode",         "Separate words only" if settings['separate'] else "Combine inputs")
    _row("Email patterns", "yes" if settings.get('emails') else "no")
    _row("Merge file",   settings.get('merge_file', ''))
    _row("Output file",  settings['output_file'])


# ---------------------------------------------------------------------------
# Word extraction
# ---------------------------------------------------------------------------

def _split_entry(text: str) -> List[str]:
    """'John Smith' -> ['John', 'Smith', 'JohnSmith']"""
    parts = text.split()
    result = parts[:]
    if len(parts) > 1:
        result.append(''.join(parts))
    return result


def extract_words(profile: dict) -> Dict[str, List[str]]:
    cats: Dict[str, List[str]] = {}

    def add(cat: str, *values) -> None:
        words: List[str] = []
        for v in values:
            if isinstance(v, list):
                for item in v:
                    if item:
                        words.extend(_split_entry(item))
            elif v:
                words.extend(_split_entry(v))
        cleaned = [w for w in words if w and len(w) >= 2]
        if cleaned:
            cats[cat] = list(dict.fromkeys(cleaned))

    # Core company words — name, abbreviation, ticker all get same mutations
    add('company',     profile.get('company_name', ''),
                       profile.get('company_short', ''),
                       profile.get('ticker', ''))

    # Former names / acquired brands — same mutation depth as company
    add('aliases',     profile.get('aliases', []))

    add('domain',      (profile.get('domain', '') or '').split('.')[0])
    add('industry',    profile.get('industry', ''))
    add('location',    profile.get('city', ''), profile.get('country', ''))
    add('people',      profile.get('ceo', ''), profile.get('other_names', []))
    add('tech',        profile.get('technologies', []))
    add('products',    profile.get('products', []))
    add('keywords',    profile.get('keywords', []))
    add('departments', profile.get('departments', []))

    # Phone — extract area code and last-4 digits for suffix mutations
    phone_raw = profile.get('phone', '')
    if phone_raw:
        digits = ''.join(c for c in phone_raw if c.isdigit())
        if len(digits) >= 3:
            phone_words: List[str] = []
            if len(digits) >= 10:
                phone_words += [digits[:3], digits[:4], digits[-4:], digits[-3:]]
            elif len(digits) >= 6:
                phone_words += [digits[:3], digits[-4:]]
            else:
                phone_words.append(digits)
            cats['phone'] = list(dict.fromkeys(w for w in phone_words if len(w) >= 3))

    # ZIP / postal code
    zip_raw = profile.get('zipcode', '')
    if zip_raw:
        zip_clean  = zip_raw.replace(' ', '')
        zip_parts  = zip_raw.split()
        zip_words  = [zip_clean]
        if len(zip_parts) > 1:
            zip_words.append(zip_parts[0])
        cats['zipcode'] = list(dict.fromkeys(z for z in zip_words if len(z) >= 3))

    # Years (kept separate — not fed into the combination engine directly)
    years = list(dict.fromkeys(
        ([profile['founded_year']] if profile.get('founded_year') else []) + RECENT_YEARS
    ))
    cats['years'] = years

    return {k: v for k, v in cats.items() if v}


# ---------------------------------------------------------------------------
# Mutation engine
# ---------------------------------------------------------------------------

def case_variants(word: str) -> List[str]:
    variants = [word.lower(), word.upper(), word.capitalize()]
    if len(word) > 4:
        variants.append(word[0].upper() + word[1:])
    return list(dict.fromkeys(variants))


def leet_primary(word: str) -> str:
    result = list(word.lower())
    for i, ch in enumerate(result):
        if ch in LEET_MAP:
            result[i] = LEET_MAP[ch][0]
    return ''.join(result)


def leet_variants(word: str) -> List[str]:
    primary = leet_primary(word)
    if primary == word.lower():
        return []
    return [primary, primary.capitalize()]


def mutate(words: List[str], complexity: int) -> Set[str]:
    result: Set[str] = set()

    if complexity >= 1:
        for w in words:
            result.update(case_variants(w))

    if complexity >= 2:
        for w in words:
            for base in case_variants(w):
                for suf in SUFFIXES_SMALL:
                    result.add(base + suf)
            for yr in RECENT_YEARS[-2:]:
                result.add(w.capitalize() + yr)
                result.add(w.lower() + yr)

    if complexity >= 3:
        for w in words:
            leets = leet_variants(w)
            result.update(leets)
            for leet in leets:
                for suf in SUFFIXES_SMALL:
                    result.add(leet + suf)
        for w in words:
            for base in case_variants(w):
                for suf in SUFFIXES_MEDIUM:
                    result.add(base + suf)
            for yr in RECENT_YEARS:
                result.add(w.capitalize() + yr)
                result.add(w.lower() + yr)
                result.add(w.upper() + yr)

    if complexity >= 4:
        for w in words:
            for leet in leet_variants(w):
                for suf in SUFFIXES_MEDIUM:
                    result.add(leet + suf)
                    result.add(leet.capitalize() + suf)
        for w in words:
            for base in case_variants(w) + leet_variants(w):
                for suf in SUFFIXES_LARGE:
                    result.add(base + suf)
            for yr in RECENT_YEARS:
                result.add(w.capitalize() + yr + '!')
                result.add(w.capitalize() + '@' + yr)
                result.add(w.lower() + yr + '!')

    if complexity >= 5:
        for w in words:
            all_bases = case_variants(w) + leet_variants(w)
            for pre in PREFIXES_LARGE:
                for base in all_bases:
                    for suf in SUFFIXES_LARGE:
                        result.add(pre + base + suf)

    return result


# ---------------------------------------------------------------------------
# Combination engine
# ---------------------------------------------------------------------------

def combine(word_pool: List[str], years: List[str], complexity: int,
            separate: bool) -> Set[str]:
    result: Set[str] = set()

    if separate:
        return set(word_pool)

    separators = SEPARATORS_SMALL
    if complexity >= 4:
        separators = SEPARATORS_MEDIUM
    if complexity >= 5:
        separators = SEPARATORS_LARGE

    if complexity >= 3:
        for a, b in itertools.permutations(word_pool, 2):
            for sep in separators:
                combo = a + sep + b
                result.add(combo)
                result.add(combo.capitalize())
                if complexity >= 4:
                    result.add(a.capitalize() + sep + b.capitalize())
                    result.add(a.lower() + sep + b.lower())
                    result.add(a.upper() + sep + b.upper())

    if complexity >= 2:
        yr_pool = years[-3:] if complexity < 4 else years
        for w in word_pool:
            for yr in yr_pool:
                for sep in separators[:2]:
                    result.add(w.capitalize() + sep + yr)
                    result.add(w.lower() + sep + yr)

    if complexity >= 5:
        pool = word_pool[:15]
        for triple in itertools.permutations(pool, 3):
            for sep in ['', '_', '-']:
                result.add(sep.join(triple))
                result.add(sep.join(w.capitalize() for w in triple))

    return result


# ---------------------------------------------------------------------------
# Email pattern generation
# ---------------------------------------------------------------------------

def email_patterns(profile: dict, categories: Dict[str, List[str]]) -> Set[str]:
    patterns: Set[str] = set()
    domain = profile.get('domain', '')
    if not domain:
        return patterns

    raw_names = ([profile.get('ceo', '')] if profile.get('ceo') else [])
    raw_names += (profile.get('other_names') or [])

    full_names: List[Tuple[str, str]] = []
    for name in raw_names:
        parts = name.split()
        if len(parts) >= 2:
            full_names.append((parts[0], parts[-1]))
        elif parts:
            full_names.append((parts[0], ''))

    for first, last in full_names:
        f, l = first.lower(), last.lower()
        if l:
            for fmt in [
                f"{f}.{l}@{domain}",
                f"{f}{l}@{domain}",
                f"{f[0]}{l}@{domain}",
                f"{f}.{l[0]}@{domain}",
                f"{l}.{f}@{domain}",
                f"{l}{f[0]}@{domain}",
                f"{f[0]}.{l}@{domain}",
            ]:
                patterns.add(fmt)
        else:
            patterns.add(f"{f}@{domain}")

    return patterns


# ---------------------------------------------------------------------------
# Progress display
# ---------------------------------------------------------------------------

def _step(n: int, total: int, msg: str, count: int, quiet: bool = False) -> None:
    if quiet:
        return
    label  = f"[{n}/{total}]"
    count_str = f"{count:>10,}  entries"
    line   = f"    {_cyan(label)}  {msg:<38} {_dim(count_str)}"
    print(line)


# ---------------------------------------------------------------------------
# Main generation pipeline
# ---------------------------------------------------------------------------

def generate(profile: dict, complexity: int, min_len: int, max_len: int,
             separate: bool, output_file: str, emails: bool,
             quiet: bool = False, merge_file: str = '') -> None:

    categories = extract_words(profile)

    non_year_cats = {k: v for k, v in categories.items() if k != 'years'}
    word_pool: List[str] = []
    for words in non_year_cats.values():
        word_pool.extend(words)
    word_pool = list(dict.fromkeys(word_pool))

    years = categories.get('years', RECENT_YEARS)

    if not quiet:
        print(f"\n  {_bold('Base words collected')} : {_cyan(str(len(word_pool)))}")
        # Show per-category breakdown
        for cat, words in non_year_cats.items():
            print(f"    {_dim(cat.ljust(14))} {', '.join(words[:6])}"
                  f"{'...' if len(words) > 6 else ''}")
        lvl = complexity
        print(f"\n  {_bold('Complexity')}           : "
              f"{_cyan(str(lvl))}  {COMPLEXITY_INFO[lvl][0]}  "
              f"{_dim(COMPLEXITY_INFO[lvl][1])}")
        print(f"  {_bold('Length filter')}        : {min_len}-{max_len} chars")
        print(f"  {_bold('Mode')}                 : "
              f"{'Separate words only' if separate else 'Combine inputs'}")
        if emails:
            print(f"  {_bold('Email patterns')}       : enabled")
        if merge_file:
            exists = os.path.exists(merge_file)
            note   = f"  {_dim('(file found)' if exists else '(file not found yet — will create)')}"
            print(f"  {_bold('Merge file')}           : {merge_file}{note}")

    if complexity == 5 and not quiet:
        print(f"\n  {_yellow('[!]')} Complexity 5 (Massive) may take several minutes and produce millions of entries.")
        confirm = input(f"  {_green('[>]')} Continue? [y/N]: ").strip().lower()
        if confirm not in ('y', 'yes'):
            print("  Aborted.")
            sys.exit(0)

    if not quiet:
        print(f"\n  {_bold('Building wordlist...')}\n")

    total_steps = 4
    wordset: Set[str] = set()

    # Step 1 — mutate individual words
    wordset.update(mutate(word_pool, complexity))
    _step(1, total_steps, "Mutating base words", len(wordset), quiet)

    # Step 2 — build combinations and mutate them
    if not separate and complexity >= 2:
        combos = combine(word_pool, years, complexity, separate)
        depth  = min(complexity, 3 if complexity < 5 else 4)
        wordset.update(mutate(list(combos), depth))
    _step(2, total_steps, "Building word combinations", len(wordset), quiet)

    # Step 3 — company + year matrix (always included)
    company_words = categories.get('company', [])
    alias_words   = categories.get('aliases', [])
    for cw in company_words + alias_words:
        for yr in years:
            wordset.add(cw.capitalize() + yr)
            wordset.add(cw.lower() + yr)
            wordset.add(cw.upper() + yr)
            wordset.add(cw.capitalize() + yr + '!')
            wordset.add(cw.capitalize() + '@' + yr)
            if complexity >= 2:
                wordset.add(cw.capitalize() + yr + '!!')
                wordset.add(cw.lower() + yr + '!')
                wordset.add(leet_primary(cw) + yr)
    _step(3, total_steps, "Applying company/year patterns", len(wordset), quiet)

    # Step 4 — length filter
    filtered = sorted(w for w in wordset if min_len <= len(w) <= max_len)
    _step(4, total_steps, f"Filtering to {min_len}-{max_len} chars", len(filtered), quiet)

    # Email patterns
    email_list: List[str] = []
    if emails and profile.get('domain'):
        email_set  = email_patterns(profile, categories)
        email_list = sorted(email_set)

    # Resolve output destination:
    #   --merge given, no -o  → write back to merge file (in-place)
    #   --merge given, -o set → write combined result to -o
    #   no --merge            → write to -o (or default filename)
    if merge_file and not output_file:
        dest = merge_file
    else:
        dest = output_file or 'mug_wordlist.txt'

    # Read existing wordlist if merging
    existing: List[str] = []
    if merge_file and os.path.exists(merge_file):
        with open(merge_file, 'r', encoding='utf-8', errors='ignore') as f:
            existing = [ln.rstrip('\n') for ln in f
                        if ln.strip() and not ln.startswith('#')]

    # Combine: existing first, then new-only entries (deduped)
    seen: Set[str] = set(existing)
    new_only = [w for w in filtered if w not in seen]
    combined = existing + new_only

    with open(dest, 'w', encoding='utf-8', errors='ignore') as f:
        for word in combined:
            f.write(word + '\n')
        if email_list:
            f.write('\n# --- email patterns ---\n')
            for e in email_list:
                f.write(e + '\n')

    size_kb  = os.path.getsize(dest) / 1024
    size_str = f"{size_kb / 1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.1f} KB"

    if merge_file:
        verb = f"merged  ({len(existing):,} existing + {len(new_only):,} new)"
    else:
        verb = "saved"

    if quiet:
        print(f"{len(combined):,}  {dest}")
    else:
        print()
        print(f"  {_green('[+]')} {_bold('New passwords added')}  : {_cyan(f'{len(new_only):,}')}")
        if merge_file:
            print(f"  {_green('[+]')} {_bold('Total in file')}       : {_cyan(f'{len(combined):,}')}")
        if email_list:
            print(f"  {_green('[+]')} {_bold('Email patterns')}      : {_cyan(str(len(email_list)))}")
        print(f"  {_green('[+]')} {_bold('Output file')}         : "
              f"{_yellow(dest)}  {_dim(f'({size_str}, {verb})')}")
        print(f"\n  {_dim('hashcat:  hashcat -a 0 -m <hash-type> hashes.txt ' + dest)}")
        print(f"  {_dim('hydra:    hydra -L users.txt -P ' + dest + ' <target> ssh')}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog='mug',
        description='Company-targeted password wordlist generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "complexity levels:\n" +
            "\n".join(
                f"  {k}  {v[0]}  {v[1]}"
                for k, v in COMPLEXITY_INFO.items()
            ) +
            "\n\nexamples:\n"
            "  python3 mug.py -i\n"
            "  python3 mug.py --company AcmeCorp --tech Azure SAP --ceo 'John Smith' -c 4\n"
            "  python3 mug.py --company AcmeCorp --ticker ACME --aliases 'Widget Inc' -c 3\n"
            "  python3 mug.py --company AcmeCorp --domain acme.com --emails --min 8 --max 16\n"
            "  python3 mug.py --company AcmeCorp -c 5 --separate -o custom_out.txt\n"
        )
    )

    meta = parser.add_argument_group('run modes')
    meta.add_argument('-i', '--interactive', action='store_true',
                      help='Interactive wizard (one question at a time, like cupp -i)')
    meta.add_argument('--list-complexity', action='store_true',
                      help='Print complexity levels and exit')
    meta.add_argument('-v', '--version', action='store_true',
                      help='Print version and exit')

    inp = parser.add_argument_group('company inputs (used with or without -i)')
    inp.add_argument('--company',     metavar='NAME',   help='Company full name')
    inp.add_argument('--short',       metavar='ABBR',   help='Short name / abbreviation')
    inp.add_argument('--ticker',      metavar='SYMBOL', help='Stock ticker (e.g. ACME)')
    inp.add_argument('--domain',      metavar='DOMAIN', help='Primary domain (e.g. acme.com)')
    inp.add_argument('--industry',    metavar='SECTOR', help='Industry / sector')
    inp.add_argument('--city',        metavar='CITY',   help='HQ city')
    inp.add_argument('--country',     metavar='CTRY',   help='Country')
    inp.add_argument('--founded',     metavar='YEAR',   help='Year founded')
    inp.add_argument('--ceo',         metavar='NAME',   help='CEO / Founder name')
    inp.add_argument('--people',      nargs='+', metavar='NAME',    help='Other key people')
    inp.add_argument('--tech',        nargs='+', metavar='TECH',    help='Technologies used')
    inp.add_argument('--products',    nargs='+', metavar='PRODUCT', help='Product/service names')
    inp.add_argument('--keywords',    nargs='+', metavar='WORD',    help='Custom keywords')
    inp.add_argument('--departments', nargs='+', metavar='DEPT',    help='Department names')
    inp.add_argument('--aliases',     nargs='+', metavar='NAME',    help='Former names / acquired brands')
    inp.add_argument('--phone',       metavar='NUMBER', help='Company phone (area code used in mutations)')
    inp.add_argument('--zip',         metavar='CODE',   help='Postal / ZIP code')

    gen = parser.add_argument_group('generation options')
    gen.add_argument('-c', '--complexity', type=int, choices=range(1, 6), default=3,
                     metavar='[1-5]', help='Complexity 1-5 (default: 3)')
    gen.add_argument('--min', type=int, default=6,  dest='min_len',
                     help='Minimum password length (default: 6)')
    gen.add_argument('--max', type=int, default=20, dest='max_len',
                     help='Maximum password length (default: 20)')
    gen.add_argument('--separate', action='store_true',
                     help='Treat each word independently — no combining')
    gen.add_argument('--emails', action='store_true',
                     help='Generate corporate email patterns (requires --domain)')
    gen.add_argument('--merge', metavar='FILE',
                     help='Existing wordlist to merge with — reads it, combines with generated output, dedupes, writes result to -o (or back to FILE if -o not given)')
    gen.add_argument('-q', '--quiet', action='store_true',
                     help='Suppress banner and verbose output (script-friendly)')
    gen.add_argument('-o', '--output', default=None, metavar='FILE',
                     help='Output file (default: mug_wordlist.txt, or merge file if --merge given)')

    args = parser.parse_args()

    if args.version:
        print(f"mug v{VERSION}")
        sys.exit(0)

    if not args.quiet:
        print(BANNER)

    if args.list_complexity:
        print("Complexity levels:\n")
        for k, (name, desc) in COMPLEXITY_INFO.items():
            print(f"  {k}  {name}  {desc}")
        print()
        sys.exit(0)

    if args.interactive:
        profile, settings = collect_profile()
        generate(
            profile=profile,
            complexity=settings['complexity'],
            min_len=settings['min_len'],
            max_len=settings['max_len'],
            separate=settings['separate'],
            output_file=settings['output_file'],
            emails=settings['emails'],
            quiet=False,
            merge_file=settings['merge_file'],
        )

    elif args.company:
        if args.min_len >= args.max_len:
            print("[!] --min must be less than --max")
            sys.exit(1)
        if args.emails and not args.domain:
            print("[!] --emails requires --domain")
            sys.exit(1)

        profile = {
            'company_name':  args.company,
            'company_short': args.short or '',
            'ticker':        args.ticker or '',
            'domain':        args.domain or '',
            'industry':      args.industry or '',
            'city':          args.city or '',
            'country':       args.country or '',
            'founded_year':  args.founded or '',
            'ceo':           args.ceo or '',
            'other_names':   args.people or [],
            'technologies':  args.tech or [],
            'products':      args.products or [],
            'keywords':      args.keywords or [],
            'departments':   args.departments or [],
            'aliases':       args.aliases or [],
            'phone':         args.phone or '',
            'zipcode':       args.zip or '',
        }
        generate(
            profile=profile,
            complexity=args.complexity,
            min_len=args.min_len,
            max_len=args.max_len,
            separate=args.separate,
            output_file=args.output,
            emails=args.emails,
            quiet=args.quiet,
            merge_file=args.merge or '',
        )

    else:
        print("[!] Provide --company <name> or use -i for interactive mode.\n")
        parser.print_help()
        sys.exit(1)

    if not args.quiet:
        print(f"\n  {_dim('[!] Only test systems you own or have written authorization to test.')}")


if __name__ == '__main__':
    main()
