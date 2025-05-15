# Dell Warranty Checker

A tool for retrieving warranty information for Dell products using service tags without using Dell's web interface.

## Features

- Look up warranty end dates for individual service tags
- Process bulk service tag lookups from CSV files
- Returns key information:
  - Model
  - Service Tag
  - Ship Date
  - Warranty End Date

## Requirements

- Python 3.x
- Required packages (install via `pip install -r requirements.txt`):
  - requests
  - pandas (for CSV processing)

## Installation

```bash
# Clone the repository
git clone https://github.com/kunalrai/dell_warranty.git

# Change to project directory
cd dell_warranty

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Single Service Tag Lookup

```bash
python dell_warranty.py -s SERVICE_TAG
```

### Bulk Lookup from CSV

```bash
python dell_warranty.py -f path/to/service_tags.csv
```

The CSV file should contain a column with service tags.

## Output

Results will be displayed in the console and can optionally be exported to a CSV file:

```bash
python dell_warranty.py -f input.csv -o results.csv
```

## License

[MIT License](LICENSE)

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
