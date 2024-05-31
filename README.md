# RecursiveModulator

## Overview

RecursiveModulator is a tool designed to split Python scripts into individual modules. Each function and class in the script is separated into its own file. This modular approach maximizes token efficiency when working with AI pair programmers, making it easier to manage and understand the codebase.

## How It Works

The `splitter.py` script processes a given Python script and performs the following actions:
1. Identifies all functions and classes in the script.
2. Creates a separate file for each function and class.
3. Updates the original script to import these functions and classes from their respective files.
4. Optionally, if the script is part of a Git repository, it creates a new branch, commits the changes, and provides a message indicating the changes.

## Usage

To use the splitter, run the following command:

```bash
python splitter.py <script_path>
```

Replace `<script_path>` with the path to the Python script you want to split.

## Example

```bash
python splitter.py my_script.py
```

This command will split `my_script.py` into individual function and class files and update `my_script.py` to import them.

## Requirements

- Python 3.x
- Git (optional, for version control features)

## License

This project is licensed under the MIT License.
