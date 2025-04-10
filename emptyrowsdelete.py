import pandas as pd
import numpy as np

# Define the constant for the Excel file path
EXCEL_FILE_PATH = r"C:\Users\dell\Downloads\Clients list 4.xlsx"  # Replace with the actual path to your Excel file

def delete_empty_rows_excel(excel_filepath, save_to_original=True, output_filepath=None):
    """
    Deletes all empty rows from an Excel file.

    Args:
        excel_filepath (str): The path to the Excel file.
        save_to_original (bool): If True, saves the changes back to the original file.
                                   If False, saves the changes to a new file specified by output_filepath.
        output_filepath (str, optional): The path to save the updated Excel file if save_to_original is False.
                                         Required if save_to_original is False.
    """
    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(excel_filepath)

        # Identify empty rows
        # A row is considered empty if all its values are NaN or None or empty string
        empty_rows = df.apply(lambda row: row.isnull().all() or row.astype(str).str.isspace().all(), axis=1)

        # Delete the empty rows
        df_cleaned = df[~empty_rows]

        if save_to_original:
            # Save the updated DataFrame back to the original file
            df_cleaned.to_excel(excel_filepath, index=False)
            print(f"Successfully deleted empty rows from '{excel_filepath}'.")
        else:
            if output_filepath:
                # Save the updated DataFrame to a new file
                df_cleaned.to_excel(output_filepath, index=False)
                print(f"Successfully deleted empty rows and saved to '{output_filepath}'.")
            else:
                print("Error: output_filepath must be specified if save_to_original is False.")

    except FileNotFoundError:
        print(f"Error: Excel file not found at '{excel_filepath}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Use the constant for the Excel file path
    excel_file_path = EXCEL_FILE_PATH
    save_option = input("Save changes to the original file? (yes/no): ").lower()

    if save_option == 'yes':
        delete_empty_rows_excel(excel_file_path)
    elif save_option == 'no':
        output_file_path = input("Enter the path to save the new Excel file: ")
        delete_empty_rows_excel(excel_file_path, save_to_original=False, output_filepath=output_file_path)
    else:
        print("Invalid option. Please enter 'yes' or 'no'.")