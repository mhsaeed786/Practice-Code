import pandas as pd
import ollama
import time
import requests
from bs4 import BeautifulSoup

# Constants
EXCEL_FILE_PATH = r"C:\Users\dell\Downloads\Clients list 2_processed.xlsx"  # Replace with the actual path to your Excel file
COLUMN_TO_UPDATE = "Campaign Mail"  # Replace with the actual column name
PROMPT_FOR_OLLAMA = "Please update this campaign email based on the data returned through web search about the company info. Only give the email itself in the output , not the subject. All I should be actually we because it is a company doing the mail."  # Replace with your fixed prompt
OLLAMA_MODEL_NAME = "llama3.2:3b"  # Replace with the desired Ollama model name

def duckduckgo_search(query):
    """
    Searches DuckDuckGo for the given query and returns the top search results.

    Args:
        query (str): The search query.

    Returns:
        list: A list of dictionaries containing search result links and snippets.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    }
    url = f"https://html.duckduckgo.com/html/?q={query}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for result in soup.find_all("div", class_="result", limit=5):  # Limit to top 5 results
        title_tag = result.find("a", class_="result__a")
        snippet_tag = result.find("a", class_="result__snippet")
        if title_tag:
            link = title_tag["href"]
            snippet = snippet_tag.text.strip() if snippet_tag else "No description available"
            results.append({"link": link, "snippet": snippet})
    return results

def update_excel_column_with_ollama_realtime(excel_filepath, column_name, fixed_prompt, ollama_model='llama3.2:3b'):
    """
    Updates a specific column in an Excel file row by row in realtime using responses from an Ollama model.

    Args:
        excel_filepath (str): The path to the Excel file.
        column_name (str): The name of the column to update.
        fixed_prompt (str): The fixed prompt to send to Ollama for each row.
        ollama_model (str): The name of the Ollama model to use (default: 'llama3.2:3b').
    """
    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(excel_filepath)
        df.columns = df.columns.str.strip()

        # Check if the specified column exists
        if column_name not in df.columns:
            print(f"Error: Column '{column_name}' not found in the Excel file.")
            return

        # Iterate through each row of the specified column
        for index, row in df.iterrows():
            original_value = row[column_name]
            company_name = row.get("Company Name", "Unknown Company")  # Assuming a "Company Name" column exists
            search_query = f"{company_name} company overview"
            print(f"Searching for: {search_query}")

            # Perform DuckDuckGo search
            search_results = duckduckgo_search(search_query)
            if search_results:
                # Combine snippets from search results
                combined_snippets = " ".join([result["snippet"] for result in search_results])
                prompt = f"{fixed_prompt}\n\nOriginal Value: {original_value}\n\nCompany Info: {combined_snippets}"
            else:
                prompt = f"{fixed_prompt}\n\nOriginal Value: {original_value}\n\nCompany Info: No relevant information found."

            try:
                # Send the prompt to the Ollama model
                response = ollama.chat(
                    model=ollama_model,
                    messages=[
                        {
                            'role': 'user',
                            'content': prompt,
                        }
                    ]
                )
                # Get the Ollama's response
                ollama_response = response['message']['content']

                # Update the cell in the DataFrame
                df.loc[index, column_name] = ollama_response
                print(f"Updated row {index + 2} (Excel row number) of column '{column_name}'.")

                # Save the updated DataFrame back to the Excel file in realtime
                df.to_excel(excel_filepath, index=False)
                print(f"Saved updated Excel file.")
                time.sleep(1)  # Adding a small delay to observe the realtime update

            except ollama.OllamaAPIError as e:
                print(f"Error calling Ollama API for row {index + 2}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred for row {index + 2}: {e}")

        print(f"\nSuccessfully updated column '{column_name}' in '{excel_filepath}' in realtime.")

    except FileNotFoundError:
        print(f"Error: Excel file not found at '{excel_filepath}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    update_excel_column_with_ollama_realtime(EXCEL_FILE_PATH, COLUMN_TO_UPDATE, PROMPT_FOR_OLLAMA, OLLAMA_MODEL_NAME)