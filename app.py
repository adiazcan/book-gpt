import json
import os
import random
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

model_choice = os.getenv('MODEL_CHOICE', 'gpt-4')
token_limit = os.getenv('TOKEN_LIMIT', 128000)
# chapter_length = os.getenv('CHAPTER_LENGTH', 20)
chapter_length = os.getenv('CHAPTER_LENGTH', 4)

# desired_pages = os.getenv('DESIRED_PAGES', 200)
desired_pages = os.getenv('DESIRED_PAGES', 20)

pad_amount = os.getenv('PAD_AMOUNT', 500)

client = AzureOpenAI(
    azure_endpoint=os.getenv("OPENAI_API_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
)

def main(): 
    state = {
        'desired_pages': desired_pages,
        'chapters': desired_pages / chapter_length,
        'plot_genre': '',
        'raw_outline': '',
        'plot_outline': '',
        'main_characters': [],
        'minor_characters': [],
        'writing_style': '',
        'writing_adjectives': '',
        'plot_settings': [],
        'chapter_by_chapter_summary_string': '',
        'chapter_summary_array': [],
        'filename': '',
        'full_text': [],
        'page_summaries': [],
    }
    
    state['plot_genre'] = 'Dystopian Science Fiction'
    state['filename'] = f"{state['plot_genre']}{model_choice}{round(random.random()*100)}.txt"
    state['raw_outline'] = outline_generator(state)
    state = state_populator(state)
    state['chapter_by_chapter_summary_string'] = plot_summary_by_chapter(state)
    state['chapter_summary_array'] = chapter_summary_array(state)
    state['page_summaries'] = page_generator(state)
    
def outline_generator(state):
    outline_prompt =  f"""Generate the outline of an original {state['desired_pages']}-page {state['plot_genre']} fiction book 
        about AI in the Workplace where the AI dominate the digital world but not dominate the physical world 
        where the AI needs human to operate machines and robots. 
        Imagine and then carefully label the following: a detailed plot, characters with names, settings and writing style. 
        You have {token_limit - (40 + pad_amount)} words remaining to write the outline. 
        It is CRITICAL you generate as many words as possible."""

    print("Generating Outline:\n") 

    outline = chat_completion(outline_prompt, 'writer', model_choice, (token_limit - (40 + pad_amount)), 0.9)

    print("Here is the raw outline:\n")
    print(outline)
    
    return outline

def state_populator(state):
    print('\nPopulating state from raw outline.\n')

    items_to_populate_hash_map = {
        'plot_outline': 'plot',
        'main_characters': 'main characters list',
        'minor_characters': 'minor characters list',
        'plot_settings': 'setting',
        'writing_style': 'writing style',
        'writing_adjectives': 'writing adjectives list'
    }

    for key, key_val in items_to_populate_hash_map.items():
        state_populator_prompt = f"""I'm going to give you the outline of a book. From this outline, tell me the {key_val}. 
            Use close to {token_limit - (500 + len(state['raw_outline']) + pad_amount)} words for this page. 
            Here is the outline: {state['raw_outline']}"""
        state_populator_result = chat_completion(state_populator_prompt, 'writer', model_choice, (token_limit - (len(state['raw_outline']) + pad_amount)), 0.9)

        print(state_populator_result)

        state[key] = state_populator_result
        print(f"\n here is the {key_val}: {state_populator_result}\n")

    print("\nHere is the state object:\n")
    text_to_save = '\n' + json.dumps(state) + '\n'
    write_to_file(state['filename'], text_to_save)
    print(state)
    return state

def plot_summary_by_chapter(state):
    print('\nGenerating chapter-by-chapter plot summary.\n')
    
    prompt = f"""You are writing a book with this plot summary: {state['plot_outline']}. The book is {state['desired_pages']} pages long. 
          Write a specific and detailed plot SUMMARY for each of the {state['chapters']} chapters of the book. 
          You must use at least a few paragraphs per chapter summary and can use up to one page or more per chapter. 
          Name any unnamed major or minor characters. Use the first few chapter summaries to introduce the characters 
          and set the story. Use the next few chapter summaries for action and character development. 
          Use the last few chapters for dramatic twists in the plot and conclusion. 
          You have {token_limit - (len(state['plot_outline']) + 500 + pad_amount)} tokens (or words) left for the summaries. 
          Try to use all the words you have available."""
          
    chapter_summary_text = chat_completion(
        prompt, 
        'writer', 
        model_choice, 
        (token_limit - (len(state['plot_outline']) + pad_amount)), 
        0.9
    )

    try:
        print(chapter_summary_text)
        chapter_summary_text = [x for x in chapter_summary_text.split('\n') if len(x) > 5]
        print(f"\nChapter-By-Chapter Plot Summary: {chapter_summary_text}\n")
        text_to_save = f"\n\nChapter-By-Chapter Plot Summary: {chapter_summary_text}\n"
        write_to_file(state['filename'], text_to_save)

        return chapter_summary_text
    except Exception as err:
        print(f"Error generating chapter summary: {err}")
        return None
        
def write_to_file(filename, text):
    with open(filename, 'a') as f:
        f.write(text)

def chapter_summary_array(state):
    chapter_summary_array = []

    for i in range(int(state['chapters'])):
        print('\033[36mGenerating chapter summaries to populate chapterSummaryArray.\n')

        while True:
            try:
                print(f'\nGenerating short summary of Chapter {i+1}:\n')

                prompt = f"""You are writing a summary of Chapter {i+1} of a {state['chapters']} chapter {state['plot_genre']} book. 
                    The entire plot summary is {state['plot_outline']} The chapter-by-chapter summary for the entire book is: 
                    {state['chapter_by_chapter_summary_string']}\n Using those summaries, write a several page SUMMARY of 
                    ONLY chapter {i+1}. Write the best summary you can, you may add new subplots, character development, 
                    character background, planned dialogue and plot development that you would typically find in such a work. 
                    You are NOT writing the actual book right now, you ARE writing an outline and SUMMARY of what will happen in 
                    this chapter. You have to write {token_limit - (500 + len(state['plot_outline']) + len(state['chapter_by_chapter_summary_string']) + pad_amount)} words.""", 

                short_summary_text = chat_completion(
                    prompt,
                    'writer', 
                    model_choice, 
                    (token_limit - (len(state['plot_outline']) + len(state['chapter_by_chapter_summary_string']) + pad_amount)), 
                    0.9
                )

                short_summary_text = short_summary_text.replace('\n', '')
                chapter_summary_array.append(short_summary_text)
                print(f"Here is the chapter summary: \n{chapter_summary_array[i]}\n")
                text_to_save = f"\nChapter {i} Summary" + chapter_summary_array[i] + '\n'
                write_to_file(state['filename'], text_to_save)
                break
            except Exception as err:
                print(err)
    return chapter_summary_array

async def generate_page_summary(page, model_choice):
    try:
        prompt = f"Here is a full page of text. Please summarize it in a few sentences. Text to summarize: {page}"
        page_summary_text = chat_completion(prompt, 'machine', model_choice, (token_limit - (len(page) + pad_amount)), 0.5)

        return page_summary_text
    
    except Exception as err:
        print(err)
        return None
            
def page_generator(state):
    print('\nEntering Page Generation module.\n')

    for i in range(int(state['chapters'])):
        for j in range(20):
            amendment = create_page_query_amendment(state, i, j)

            print(f'\nCurrent amendment is: {amendment}\n')
            print(f'\nGenerating final full text for chapter {i+1} page {j+1}\n')

            while True:
                try:
                    prompt = f"""You are an author writing page {j+1} in chapter {i+1} of a {state['chapters']}-chapter {state['plot_genre']} novel. 
                        The plot summary for this chapter is {state['chapter_summary_array'][i]}. {amendment}. 
                        As you continue writing the next page, be sure to develop the characters' background thoroughly, include dialogue and detailed literary descriptions 
                        of the scenery, and develop the plot. Do not mention page or chapter numbers! Do not jump to the end of the plot and make sure there is plot continuity. 
                        Carefully read the summaries of the prior pages before writing new plot. Make sure you fill an entire page of writing. 
                        Use the chapter summary and the reads from the previous page to write the current page."""
                        
                    page_gen_text = chat_completion(
                        prompt, 
                        'writer', 
                        model_choice, 
                        (token_limit - (len(state['chapter_summary_array'][i]) + len(amendment))), 
                        0.9
                    )

                    page_gen_text = page_gen_text.replace('\n', '')
                    state['full_text'].append((page_gen_text + "\n"))
                    
                    print(f"\n\n\nChapter {i+1}\n\nPage {j+1}\n\n {page_gen_text}\n\n")

                    header = f"\n\nChapter {i + 1}, Page {j + 1}\n\n"
                    write_to_file(state['filename'], header + page_gen_text)

                    page_summary = generate_page_summary(page_gen_text, model_choice)
                    state['page_summaries'].append(page_summary)
                    break
                
                except Exception as err:
                    print(err)
                    
def create_page_query_amendment(state, i, j):
    amendment = ""

    if j == 0:
        amendment = "This is the first page of the chapter."
    elif j == 1:
        amendment = f"Page 1 of this chapter reads as follows: \n{state['full_text'][i*chapter_length + j-1]}\n"
    elif j == 2:
        amendment = f"Pages {j-1} reads as follows: \n{state['full_text'][i*chapter_length + j-2]}\n Page {j} reads as follows: {state['full_text'][i*chapter_length + j-1]}\n"
    else:
        prior_pages = ''.join([f"\nChapter {i+1}, Page {k+1}: {state['page_summaries'][i*chapter_length + k]}\n" for k in range(j)])
        if j > 2:
            amendment = f"Here are the page summaries of the chapter thus far: {prior_pages}. The full text of pages {j-2},{j-1} and {j} read as follows: Page {j-2}: {state['full_text'][i*chapter_length + j-3]} Page {j-1}: {state['full_text'][i*chapter_length + j-2]} Page {j}: {state['full_text'][i*chapter_length + j-1]}"

    return amendment


def chat_completion(prompt, role, model, max_tokens, temperature):
    role_contents = {
        'machine': "You are a computer program attempting to comply with the user's wishes.",
        'writer': "You are a professional fiction writer who is a best-selling author. You use all of the rhetorical devices you know to write a compelling book.",
        'default': "You are an ChatGPT-powered chat bot."
    }

    role_content = role_contents.get(role, role_contents['default'])

    prompt += '. RESPONSE ALWAYS IN SPANISH LANGUAGE.'

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system", "content": role_content    
            },
            {
                "role": "user", "content": prompt
            }
        ],
        # max_tokens=max_tokens,
        temperature=temperature
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    main()