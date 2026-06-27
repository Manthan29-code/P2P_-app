# Cloud File Relay

A simple Streamlit app for moving a file between two devices through a temporary in-memory relay. Upload a file, get a share code, then enter that code on another device to download the file.

## Features

- Temporary server-side storage in memory only
- Random 8-character share codes
- Automatic expiry after 30 minutes
- Optional delete-after-first-download behavior
- Supports files up to 200 MB

## How It Works

1. The sender uploads a file in the app.
2. The app stores the file in shared application memory and generates a share code.
3. The receiver enters the code on another device.
4. The file is offered as a download and can optionally be removed after the first click.

## Requirements

- Python 3.10 or newer
- Streamlit

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Run Locally

Start the app with:

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal.

## Usage

### Send a file

1. Open the app.
2. In the left-side Send panel, choose a file.
3. Keep or change the "Delete after first download" option.
4. Click "Create share code".
5. Share the generated code with the receiver.

### Receive a file

1. Open the same app URL on another device.
2. Enter the share code in the Receive panel.
3. Click "Download file".

## Limits And Notes

- Files live only in the running app's memory.
- Restarting the app clears all active transfers.
- Expired files are removed automatically.
- The app is designed for temporary transfers, not long-term storage.

## Project Structure

- `app.py` - Streamlit application entry point and file relay logic
- `requirements.txt` - Python dependency list
- `plan/doc.md` - Architecture notes for the Streamlit relay design

## License

No license has been specified for this project.