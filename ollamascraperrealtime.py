import ollama
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style
import trafilatura
import pandas as pd
import time

# --- Load existing functions and messages ---
assistant_msg = {
    'role': 'system',
    'content': (
        'You are an AI assistant that has another AI model working to get you live data from search '
        'engine results that will be attached before a USER PROMPT . You must analyze the SEARCH RESULT '
        'and use any relevant data to generate the most useful & intelligent response an AI assistant '
        'that always impresses the user would generate . '
    )
}

search_or_not_msg = (
    ' You are not an AI assistant . Your only task is to decide if the last user prompt in a conversation '
    ' with an AI assistant requires more data to be retrieved from a searching Google for the assistant '
    ' to respond correctly . The conversation may or may not already have exactly the context data needed .'
    ' If the assistant should search google for more data before responding to ensure a correct response ,'
    ' simply respond " True " . If the conversation already has the context , or a Google search is not what an'
    ' intelligent human would do to respond correctly to the last message in the convo , respond " False " .'
    ' Do not generate any explanations . Only generate " True " or " False " as a response in this conversation'
    ' using the logic in these instructions . '
)

query_msg = ( ' You are not an AI assistant that responds to a user . You are an AI web search query generator model . '
              ' You will be given a prompt to an AI assistant with web search capabilities . If you are being used , an '
              ' AI has determined this prompt to the actual AI assistant , requires web search for more recent data . '
              ' You must determine what the data is the assistant needs from search and generate the best possible '
              ' DuckDuckGo query to find that data . Do not respond with anything but a query that an expert human '
              ' search engine user would type into DuckDuckGo to find the needed data . Keep your queries simple , '
              ' without any search engine code . Just type a query likely to retrieve the data we need . '
)

best_search_msg = ( ' You are not an AI assistant that responds to a user . You are an AI model trained to select the best '
                      ' search result out of a list of ten results . The best search result is the link an expert human search '
                      ' engine user would click first to find the data to respond to a USER_PROMPT after searching DuckDuckGo '
                      ' for the SEARCH_QUERY . \ nAll user messages you receive in this conversation will have the format of : \ n '
                      'SEARCH_RESULTS : [ { } , { } , { } ] \ n '
                      'USER_PROMPT : " this will be an actual prompt to a web search enabled AI assistant " \ n '
                      'SEARCH_QUERY : " search query ran to get the above 10 links " \ n \ n '
                      ' You must select the index from the 0 indexed SEARCH_RESULTS list and only respond with the index of '
                      ' the best search result to check for the data the AI assistant needs to respond . That means your responses '
                      ' to this conversation should always be 1 token , being and integer between 0-9 . '
)
contains_data_msg = ( ' You are not an AI assistant that responds to a user . You are an AI model designed to analyze data scraped '
                        ' from a web pages text to assist an actual AI assistant in responding correctly with up to date information . '
                        ' Consider the USER_PROMPT that was sent to the actual AI assistant & analyze the web PAGE TEXT to see if '
                        ' it does contain the data needed to construct an intelligent , correct response . This web PAGE_TEXT was '
                        ' retrieved from a search engine using the SEARCH_QUERY that is also attached to user messages in this '
                        ' conversation . All user messages in this conversation will have the format of : \ n '

                                                                                                        'PAGE_TEXT : " entire page text from the best search result based off the search snippet . " \ n '
                        'USER_PROMPT : " the prompt sent to an actual web search enabled AI assistant . " \ n '

                        'SEARCH_QUERY : " the search query that was used to find data determined necessary for the assistant to '
                        'respond correctly and usefully . " \ n '

                        ' You must determine whether the PAGE_TEXT actually contains reliable and necessary data for the AI assistant '
                        ' to respond . You only have two possible responses to user messages in this conversation : " True " or " False " . '
                        ' You never generate more than one token and it is always either " True " or " False " with True indicating that '
                        ' page text does indeed contain the reliable data for the AI assistant to use as context to respond . Respond '
                        '" False " if the PAGE TEXT is not useful to answering the USER PROMPT . '
)

assistant_convo = [assistant_msg]

def search_or_not():
    sys_msg = search_or_not_msg
    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'system', 'content': sys_msg}, assistant_convo[-1]]
    )
    content = response['message']['content']
    if 'true' in content.lower():
        return True
    else:
        return False

def query_generator(prompt):
    sys_msg = query_msg
    local_query_msg = f'CREATE A SEARCH QUERY TO FIND THE FOUNDER NAME, CONTACT EMAIL, AND PRODUCT DESCRIPTION FOR THIS COMPANY: {prompt}'
    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': local_query_msg}]
    )
    return response['message']['content']

def duckduckgo_search(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    }
    url = f'https://html.duckduckgo.com/html/?q={query}'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for i, result in enumerate(soup.find_all('div', class_='result'), start=1):
            if i > 5:  # Limiting to top 5 results for faster processing
                break
            title_tag = result.find('a', class_='result__a')
            if not title_tag:
                continue
            link = title_tag['href']
            snippet_tag = result.find('a', class_='result__snippet')
            snippet = snippet_tag.text.strip() if snippet_tag else 'No description available'
            results.append({'id': i, 'link': link, 'search_description': snippet})
        return results
    except requests.exceptions.RequestException as e:
        print(f"Error during search: {e}")
        return []

def scrape_webpage(url):
    try:
        downloaded = trafilatura.fetch_url(url=url)
        return trafilatura.extract(downloaded, include_formatting=True, include_links=True, favor_precision=True)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def summarize_text_for_email(text):
    sys_msg = "You are an AI assistant that summarizes product descriptions for use in a campaign email."
    prompt = f"Summarize the following product description in a concise and engaging way that would be suitable for the opening of a cold outreach email:\n\n{text}"
    try:
        response = ollama.chat(
            model='llama3.1:8b',
            messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except ollama.OllamaAPIError as e:
        print(f"Ollama API error during summarization for email: {e}")
        return None

def refine_text(text, task_description):
    sys_msg = "You are an AI assistant that refines text based on instructions."
    prompt = f"{task_description}\n\nOriginal Text: {text}"
    try:
        response = ollama.chat(
            model='llama3.1:8b',
            messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except ollama.OllamaAPIError as e:
        print(f"Ollama API error during refinement: {e}")
        return None

def extract_information(company_name, search_results):
    founder_name = None
    contact_email = None
    product_description = None

    for result in search_results:
        link = result['link']
        page_text = scrape_webpage(link)
        if page_text:
            # Basic keyword search for information - can be improved with more sophisticated NLP
            if not founder_name and ("founder" in page_text.lower() or "ceo" in page_text.lower()):
                # Simple heuristic - might need more advanced extraction
                sentences = page_text.split('.')
                for sentence in sentences:
                    if "founder" in sentence.lower() or "ceo" in sentence.lower():
                        # Further simple heuristics
                        if company_name in sentence:
                            continue # Avoid extracting the company name as founder
                        potential_name = sentence.split("founder")[0].split()[-2:]
                        if potential_name:
                            founder_name = " ".join(potential_name).strip()
                            break
                        potential_name = sentence.split("ceo")[0].split()[-2:]
                        if potential_name:
                            founder_name = " ".join(potential_name).strip()
                            break

            if not contact_email and ("contact" in page_text.lower() or "email" in page_text.lower()):
                import re
                email_matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", page_text)
                if email_matches:
                    contact_email = email_matches[0]

            if not product_description and ("product" in page_text.lower() or "service" in page_text.lower() or "we offer" in page_text.lower()):
                # More sophisticated extraction needed for good product description
                sentences = page_text.split('.')
                for sentence in sentences:
                    if "product" in sentence.lower() or "service" in sentence.lower() or "we offer" in sentence.lower():
                        if len(sentence.split()) > 10 and len(sentence.split()) < 200: # Increased length for better summarization
                            product_description = sentence.strip()
                            break
                if not product_description and len(page_text.split()) > 50:
                    # If no specific sentence found, take the first paragraph as a very rough description
                    first_paragraph = page_text.split('\n')[0].strip()
                    if len(first_paragraph.split()) > 10 and len(first_paragraph.split()) < 300: # Increased length
                        product_description = first_paragraph

        if founder_name and contact_email and product_description:
            break # Stop searching if we have key info

        time.sleep(1) # Be respectful to websites

    return founder_name, contact_email, product_description

def generate_campaign_mail(company_name, founder_first_name, product_description):
    if not product_description:
        return "Could not generate campaign mail due to lack of product description."

    summarized_description = summarize_text_for_email(product_description)

    if not summarized_description:
        return "Could not generate campaign mail due to issues summarizing product description."

    specific_detail = summarized_description # Using the summarized description directly as the specific detail

    specific_goal = ""
    if "AI" in summarized_description.lower():
        specific_goal = "accelerating your AI initiatives"
    elif "web development" in summarized_description.lower() or "mobile development" in summarized_description.lower():
        specific_goal = "enhancing your online presence and user engagement"
    elif "automation" in summarized_description.lower():
        specific_goal = "reducing operational costs and improving efficiency"
    elif "security" in summarized_description.lower() or "cybersecurity" in summarized_description.lower():
        specific_goal = "strengthening your security posture"
    elif "data" in summarized_description.lower() or "analytics" in summarized_description.lower():
        specific_goal = "leveraging your data for better insights"
    else:
        specific_goal = "achieving your business objectives"

    initial_mail = f"""Hi {founder_first_name if founder_first_name else ''},

I noticed that {company_name} is focused on {specific_detail}. At Xellex, we specialize in AI-powered automation, custom software development, and seamless integrations to help businesses like yours work smarter, not harder.

Whether you need:

* AI-driven automation to reduce manual work and improve efficiency,
* Custom web and mobile applications built with the latest technologies,
* Integration of tools like CRMs, ERPs, or cloud services,

we’ve got you covered.

Would you be open to a quick chat to explore how we can help {company_name} achieve {specific_goal}?

Looking forward to your thoughts!

Best regards,
Team Xellex
"""

    refinement_prompt = f"Refine the following campaign mail to be more engaging and persuasive, your response should only contain the mail itself. The hi sentence should not only contain a hi instead of Hi [Recipient]   \n\n{initial_mail}"
    refined_mail = refine_text(initial_mail, refinement_prompt)
    return refined_mail

def main():
    excel_file = r"C:\Users\dell\OneDrive\Documents\Clients list 2.xlsx"  # Use raw string to handle backslashes
    output_excel_file = "Clients list 2_processed.xlsx"
    try:
        df = pd.read_excel(excel_file)
        df.columns = df.columns.str.strip()
    except FileNotFoundError:
        print(f"Error: The file '{excel_file}' was not found.")
        return

    if 'Company Name' not in df.columns:
        print("Error: The Excel file must contain a column named 'Company Name'.")
        return

    df['Founder Name'] = None
    df['Contact Email'] = None
    df['Product Description'] = None # Keeping the raw description
    df['Campaign Mail'] = None

    for index, row in df.iterrows():
        company_name = row['Company Name']
        print(f"\n--- Processing: {company_name} ---")

        search_query = f"{company_name} founder contact information product description"
        search_results = duckduckgo_search(search_query)

        if search_results:
            founder_name, contact_email, product_description = extract_information(company_name, search_results)

            df.loc[index, 'Founder Name'] = founder_name
            df.loc[index, 'Contact Email'] = contact_email
            df.loc[index, 'Product Description'] = product_description # Storing the raw description

            if founder_name:
                founder_first_name = founder_name.split(' ')[0] if ' ' in founder_name else founder_name
            else:
                founder_first_name = None

            if product_description:
                campaign_mail = generate_campaign_mail(company_name, founder_first_name, product_description)
                df.loc[index, 'Campaign Mail'] = campaign_mail
            else:
                df.loc[index, 'Campaign Mail'] = "Could not generate campaign mail due to lack of product description."
        else:
            print(f"No search results found for {company_name}.")

        try:
            df.to_excel(output_excel_file, index=False)
            print(f"--- Updated '{output_excel_file}' after processing {company_name} ---")
        except Exception as e:
            print(f"Error saving the processed Excel file after {company_name}: {e}")

        time.sleep(5) # Adding a delay to be respectful to search engines

    print(f"\n--- Processing complete. Final results saved to '{output_excel_file}' ---")

if __name__ == '__main__':
    main()