
from pathlib import Path
import pandas as pd


def load_dataset(file_path):
    """
    Load the approved LastMile AI Master Dataset.

    This function reads the Excel workbook without
    modifying the original file.
    """

    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}"
        )

    # Load all Excel sheets
    with pd.ExcelFile(file_path) as excel_file:
        data = {
            sheet_name: pd.read_excel(
                excel_file,
                sheet_name=sheet_name
            )
            for sheet_name in excel_file.sheet_names
        }

    # Separate actual channels from documentation notes
    channels = data["Channels"]

    channel_mask = (
        channels["Channel ID"]
        .astype("string")
        .str.fullmatch(r"CH\d{2}", na=False)
    )

    data["Channel Records"] = (
        channels.loc[channel_mask].copy()
    )

    data["Channel Notes"] = (
        channels.loc[
            channels["Channel ID"].notna() & ~channel_mask
        ].copy()
    )

    return data


if __name__ == "__main__":

    dataset_path = (
        Path(__file__).resolve().parents[2]
        / "data" / "reference" / "LastMile_AI_Step1_Master_Dataset.xlsx"
    )

    data = load_dataset(dataset_path)

    print("LastMile AI Dataset Loaded Successfully!")

    print("\nResidents:", len(data["Residents"]))
    print("Warning Channels:", len(data["Channel Records"]))
    print("Documentation Notes:", len(data["Channel Notes"]))

    print("\nAvailable Sheets:")
    for sheet_name in data:
        print("-", sheet_name)
