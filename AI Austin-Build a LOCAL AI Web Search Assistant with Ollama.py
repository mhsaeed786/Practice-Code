import ollama 
import requests
from bs4 import BeautifulSoup
from colorama import  Fore, Style, Fore
import trafilatura

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

query_msg = (  ' You are not an AI assistant that responds to a user . You are an AI web search query generator model . '
               ' You will be given a prompt to an AI assistant with web search capabilities . If you are being used , an '
               ' AI has determined this prompt to the actual AI assistant , requires web search for more recent data . '
               ' You must determine what the data is the assistant needs from search and generate the best possible '
               ' DuckDuckGo query to find that data . Do not respond with anything but a query that an expert human '
               ' search engine user would type into DuckDuckGo to find the needed data . Keep your queries simple , '
               ' without any search engine code . Just type a query likely to retrieve the data we need . '
)

best_search_msg = (  ' You are not an AI assistant that responds to a user . You are an AI model trained to select the best '
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
contains_data_msg = (  ' You are not an AI assistant that responds to a user . You are an AI model designed to analyze data scraped '
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


assistant_convo = [assistant_msg]  # Corrected the spelling here
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

def query_generator():
    sys_msg = query_msg  # Use the global variable query_msg
    local_query_msg = f'CREATE A SEARCH QUERY FOR THIS PROMPT : \n {assistant_convo[-1]}'
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
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    for i, result in enumerate(soup.find_all('div', class_='result'), start=1):
        if i > 10:
            break
        title_tag = result.find('a', class_='result__a')
        if not title_tag:
           continue

        link = title_tag['href']
        snippet_tag = result.find('a', class_='result__snippet')
        snippet = snippet_tag.text.strip() if snippet_tag else 'No description available'
        results.append ( {
                                                  'id': i,
                                                  'link': link,
                                                  'search_description': snippet
                                                  })
    return results

def best_search_result(s_results, query):
    sys_msg = best_search_msg
    best_msg = f'SEARCH_RESULTS : {s_results} \nUSER_PROMPT : {assistant_convo[-1]} \nSEARCH_QUERY : {query}'

    for _ in range(2):
        try:
            response = ollama.chat(
                model='llama3.1:8b',
                messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': best_msg}]
            )
            result = int(response['message']['content'])
            if result is not None:
                return result
        except:
            continue
    return 0
def scrape_webpage(url):
    try:
        downloaded = trafilatura.fetch_url(url=url)
        return trafilatura.extract(downloaded, include_formatting=True, include_links=True)
    except Exception as e:
        return None

def ai_search():
    """
    This function is responsible for generating a search query based on the user's input,
    running a search with duckduckgo, and then determining which search result is most relevant
    to the user's query.

    The function begins by generating a search query using the query_generator function.
    It then runs a search with duckduckgo using the duckduckgo_search function, and stores
    the results in the search_results variable.

    The function then enters a loop where it prompts the user to identify the most relevant
    search result. If the user indicates that a search result is relevant, the function sets
    context_found to True and stores the relevant search result in the context variable.

    If the user does not indicate any search results are relevant, the function sets
    context_found to False.

    The function returns the context variable. If context_found is False, the function
    returns None. If context_found is True, the function returns the relevant search result.
    """


    context = None
    print (f'{Fore.LIGHTRED_EX}' 'GENERATING SEARCH QUERY .{Style.RESET_ALL} ' )
    search_query = query_generator()
    print (f'{Fore.LIGHTRED_EX}' 'SEARCHING DuckDuckGo FOR : {search_query}{Style.RESET_ALL} ' )
    if search_query [ 0 ] == '"':
        search_query = search_query [ 1 : -1 ]

    search_results = duckduckgo_search(search_query)
    context_found = False
    while not context_found and len(search_results) > 0:
        best_result = best_search_result(s_results=search_results, query=search_query)
        try:
            page_link = search_results[best_result]['link']
           
        except:
            print(f'{Fore.LIGHTRED_EX}FAILED TO SELECT BEST SEARCH RESULT, TRYING AGAIN.{Style.RESET_ALL}')
            continue
        page_text = scrape_webpage(page_link)
        search_results.pop(best_result)
        if page_text and contains_data_needed ( search_content = page_text , query = search_query ) :
                    context = page_text
                    context_found = True
    return context

def contains_data_needed(search_content, query):

    sys_msg = "Please analyze if this webpage content contains the information needed to answer the user's query. Only respond with 'true' or 'false'."
    needed_prompt = f'PAGE_TEXT : {search_content} \nUSER_PROMPT : {assistant_convo[-1]} \nSEARCH_QUERY : {query}'
    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': needed_prompt}]
    )
    content = response['message']['content']
    if 'true' in content.lower():
        print (f'{Fore.LIGHTRED_EX}' 'FOUND DATA .{Style.RESET_ALL} ' )
        return True   
          
    else:
        print (f'{Fore.LIGHTRED_EX}' 'NO DATA FOUND .{Style.RESET_ALL} ' )
        return False 
        
        
def stream_assistant_response():
    global assistant_convo
    response_stream = ollama.chat(model='llama3.1:8b', messages=assistant_convo, stream=True)
    complete_response = ''
    print('Assistant: ')
    for chunk in response_stream:
        print(f'{Fore.WHITE}{chunk['message']['content']}{Style.RESET_ALL}', end='', flush=True)
        complete_response += chunk['message']['content']

    assistant_convo.append({'role': 'assistant', 'content': complete_response})
    print('\n\n')

def main():
    global assistant_convo

    while True:
        user_input = input(f'{Fore.LIGHTGREEN_EX}USER: ')
        assistant_convo.append({'role': 'user', 'content': user_input})
        if search_or_not():
           context = ai_search()

           if search_or_not():
               context = ai_search()
               assistant_convo = assistant_convo[:-1]
               if context:
                  prompt = f'SEARCH RESULT : {context} \n\nUSER PROMPT : {prompt}'
               else:
                 prompt = (
                    f'USER PROMPT : \n {prompt} \n\nFAILED SEARCH : \nThe '
                'AI search model was unable to extract any reliable data. Explain that '
                'and ask if the user would like you to search again or respond '
                'without web search context. Do not respond if a search was needed '
                'and you are getting this message with anything but the above request '
                'of how the user would like to proceed'
            )
        stream_assistant_response()


if __name__ == '__main__':
    main()
