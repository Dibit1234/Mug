# MUG — Company-Targeted Wordlist Generator

```
    ) ) )
  .-------.
  |       |--,
  |  MUG  |  )
  |       |--'
  '-------'
  Company-Targeted Wordlist Generator v1.0.0
  github.com/Dibit1234/Mug  |  For authorized testing only
```

Corporate password wordlists built from what you know about the target — company names, key people, technologies, ticker symbols, and more. Inspired by [cupp](https://github.com/Mebus/cupp).

**No external dependencies. Pure Python 3.**

---

## Features

- **Interactive wizard** (`-i`) — one question at a time, like cupp
- **CLI mode** — script-friendly, pipe-compatible
- **5 complexity levels** — from a few hundred to millions of candidates
- **Combination engine** — 2-word and 3-word permutations across all categories
- **Mutation engine** — leet speak, case variants, year appending, special char suffixes/prefixes
- **Email pattern generation** — corporate address formats for username enumeration
- **Quiet mode** (`-q`) — suppress banner, output only count + filename
- **Append mode** (`--append`) — add to an existing wordlist
- **New inputs**: ticker symbol, former names/aliases, phone (area code), ZIP code

---

## Requirements

- Python 3.6+
- No external libraries

---

## Installation

### System-wide command (recommended — Kali / Debian / Ubuntu)

```bash
git clone https://github.com/Dibit1234/Mug
cd Mug
chmod +x install.sh
./install.sh
```

The install script symlinks `mug.py` to `/usr/local/bin/mug` so `git pull` inside the repo automatically updates the command.

```bash
mug -i
mug --help
```

To uninstall:
```bash
sudo rm /usr/local/bin/mug
```

### pip (editable install — any platform)

```bash
git clone https://github.com/Dibit1234/Mug
cd Mug
pip install -e .
mug -i
```

To uninstall:
```bash
pip uninstall mug
```

### Manual (no install)

```bash
git clone https://github.com/Dibit1234/Mug
cd Mug
python3 mug.py -i
```

---

## Usage

### Interactive mode (recommended)
```bash
python3 mug.py -i
```
Walks through every section one field at a time. Asks for generation settings (complexity, length, output file) at the end and shows a full profile summary before generating.

### CLI mode
```bash
# Basic
python3 mug.py --company AcmeCorp --tech Azure SAP --ceo "John Smith" -c 4

# With all inputs
python3 mug.py \
  --company AcmeCorp \
  --short Acme \
  --ticker ACME \
  --domain acme.com \
  --ceo "John Smith" \
  --people "Jane Doe" "Bob Wilson" \
  --tech Azure SAP Python \
  --products CloudSuite \
  --keywords Titan GreenOps \
  --departments HR Finance ITSec \
  --aliases "Widget Inc" \
  --phone "020 7946 0123" \
  --zip "EC1A 1BB" \
  --founded 2005 \
  -c 4 --min 8 --max 20 \
  -o acme_wordlist.txt

# Email patterns for username enumeration
python3 mug.py --company AcmeCorp --domain acme.com --ceo "John Smith" --emails -c 3

# Separate mode — each word individually, no combining
python3 mug.py --company AcmeCorp -c 5 --separate --min 8 --max 16

# Append to existing wordlist (script-friendly)
python3 mug.py --company AcmeCorp -c 2 -q --append -o master_list.txt
```

---

## Complexity Levels

| Level | Name    | What it includes                                    | Approx. output        |
|-------|---------|-----------------------------------------------------|-----------------------|
| 1     | Minimal | Raw words + basic case variants                     | ~hundreds             |
| 2     | Low     | + numbers/years + basic special chars               | ~thousands            |
| 3     | Medium  | + leet speak + same-category 2-word combos          | ~tens of thousands    |
| 4     | High    | + cross-category combos + full mutation matrix      | ~hundreds of thousands|
| 5     | Massive | + 3-way combos + prefix/leet/suffix matrix          | ~millions             |

---

## All Options

```
run modes:
  -i, --interactive       Interactive wizard (one question at a time, like cupp -i)
  --list-complexity        Print complexity levels and exit
  -v, --version            Print version and exit

company inputs:
  --company NAME           Company full name (required for CLI mode)
  --short ABBR             Short name / abbreviation
  --ticker SYMBOL          Stock ticker (e.g. ACME) — gets same mutations as company name
  --domain DOMAIN          Primary domain (e.g. acme.com)
  --industry SECTOR        Industry / sector
  --city CITY              HQ city
  --country CTRY           Country
  --founded YEAR           Year founded
  --ceo NAME               CEO / Founder name
  --people NAME [NAME...]  Other key people
  --tech TECH [TECH...]    Technologies used
  --products PRODUCT...    Product/service names
  --keywords WORD...       Custom keywords (codenames, slogans, etc.)
  --departments DEPT...    Department names
  --aliases NAME...        Former names / acquired brands
  --phone NUMBER           Company phone — area code digits added to mutations
  --zip CODE               Postal / ZIP code

generation options:
  -c [1-5]                 Complexity level (default: 3)
  --min INT                Minimum password length (default: 6)
  --max INT                Maximum password length (default: 20)
  --separate               Treat each word individually — no combining
  --emails                 Generate corporate email patterns (requires --domain)
  --append                 Append to output file instead of overwriting
  -q, --quiet              Suppress banner and progress — outputs only count + filename
  -o FILE                  Output file (default: mug_wordlist.txt)
```

---

## Mutation Rules

| Mutation        | Example input | Example outputs                                   |
|-----------------|---------------|---------------------------------------------------|
| Case variants   | acme          | acme, ACME, Acme                                  |
| Leet speak      | acme          | @cme, @cm3                                        |
| Year appending  | Acme          | Acme2024, Acme2025, ACME2024!                     |
| Special suffixes| Acme          | Acme!, Acme123, Acme@123, Acme#                   |
| Combinations    | Acme + Azure  | AcmeAzure, Acme_Azure, Azure_Acme, AcmeAzure2024  |
| Ticker          | ACME          | ACME2024, Acme!, @cme123                          |
| Area code       | 020 7946 0123 | appended as suffix/prefix to other words          |

---

## Combining with Other Tools

```bash
# hashcat — straight dictionary attack
hashcat -a 0 -m 1000 hashes.txt mug_wordlist.txt

# hashcat — dictionary + rules (extends coverage further)
hashcat -a 0 -m 1000 hashes.txt mug_wordlist.txt -r /usr/share/hashcat/rules/best64.rule

# hydra — online brute force
hydra -L users.txt -P mug_wordlist.txt ssh://10.0.0.1

# john — format-aware cracking
john --wordlist=mug_wordlist.txt --format=NT hashes.txt

# medusa — service brute force
medusa -U users.txt -P mug_wordlist.txt -h 10.0.0.1 -M ssh
```

---

## Example Output

```
  Base words collected : 14
    company        AcmeCorp, Acme, ACME
    people         John, Smith, JohnSmith
    tech           Azure, SAP
    keywords       Titan

  Complexity           : 3  Medium
  Length filter        : 8-20 chars
  Mode                 : Combine inputs

  Building wordlist...

    [1/4]  Mutating base words                         1,228  entries
    [2/4]  Building word combinations                 18,430  entries
    [3/4]  Applying company/year patterns             18,516  entries
    [4/4]  Filtering to 8-20 chars                    14,293  kept

  [+] Passwords generated  : 14,293
  [+] Output file         : acme_wordlist.txt  (218.4 KB)
```

---

## Legal Disclaimer

**MUG is intended for authorized security testing only.**  
Use only against systems you own or have explicit written permission to test.  
Unauthorized use against third-party systems may be illegal in your jurisdiction.
