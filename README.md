# README.md

# Python Project

This is a Python project that serves as a template for building applications with a single entry point. 

## Project Structure

```
python-project
├── src
│   ├── main.py          # Entry point of the application
│   └── utils
│       └── __init__.py  # Utility functions and classes
├── tests
│   └── __init__.py      # Test setup code
├── .gitignore            # Git ignore file
├── requirements.txt      # Project dependencies
├── README.md             # Project documentation
└── .envrc                # Environment variables
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd python-project
   ```


2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python src/main.py
   ```

## Environment Variables

Make sure to set up your environment variables in the `.envrc` file as needed for your application.

## Testing

To run tests, ensure your virtual environment is activated and use the following command:
```bash
pytest
```

## License

This project is licensed under the MIT License.