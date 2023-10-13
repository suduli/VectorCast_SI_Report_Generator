# VectorCast Report Generation Script

This script automates the process of generating various reports and test scripts for a given unit using VectorCast.

## Features

- Automatically creates necessary folders for storing reports.
- Extracts specific strings from a given environment file.
- Generates paths for different types of reports.
- Executes system commands to produce reports and test scripts.

## Prerequisites

- Ensure you have VectorCast installed and the `VECTORCAST_DIR` environment variable set.
- The script should be placed in the directory containing the unit for which reports are to be generated.

## How to Use

1. Navigate to the directory containing the script.
2. Run the script using Python:
   ```
   python script_name.py
   ```
3. You will be prompted to choose whether you want Compound Test Cases. Enter `1` for YES or `2` for NO.
4. The script will then generate the necessary reports and test scripts, and store them in the appropriate directories.

## Code Structure

- `create_folder(path, folder_name)`: Creates a folder and returns its path.
- `generate_report_path(main_path, unit_name, end_type)`: Generates a report path based on the unit name and type.
- `extract_strings_from_env(env_name)`: Extracts specific strings from the provided environment file.
- `main()`: The main function that orchestrates the entire process.

## Notes

- The script assumes the presence of an environment file named in the format `UNIT_NAME.env` in the current directory.
- Reports and test scripts are stored in a folder named `UNIT_NAME_VCAST_SI_Results` within the current directory.

---

You can save the above content in a file named `README.md` and place it alongside the script for documentation purposes.# VectorCast_SI_Report_Generator
Autometically Generate SI Reports from VectoCAST 
