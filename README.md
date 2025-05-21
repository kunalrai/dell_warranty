# Dell Warranty Checker1.0

A tool for retrieving warranty information for Dell products using service tags without using Dell's web interface. https://dell-warranty.azurewebsites.net
![image](https://github.com/user-attachments/assets/79761f2b-5f81-4564-8165-8441979ac3fa)
![image](https://github.com/user-attachments/assets/65301104-90f6-431d-afc3-424e2ee89a52)
![image](https://github.com/user-attachments/assets/e424d180-b469-46a2-8acb-738c23d31156)
![image](https://github.com/user-attachments/assets/6dee58c4-1cc1-4469-ae44-bc7afd064c5a)
![image](https://github.com/user-attachments/assets/cb3cec11-67ca-42d5-b015-3c69895d1986)


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
