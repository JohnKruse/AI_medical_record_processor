import logging
import requests
import time
import fitz  # PyMuPDF

def extract_text_from_pdf(file_path):
    text = ''
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text(file_path):
    file_type = file_path.split('.')[-1].lower()
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return None

def query_openai_gptX_with_schema(text, questions, role_prompt, model_name, api_key, file_path=None, function_schema=None, max_tokens=2000, temperature=0.3):
    logging.info("Starting query_openai_gptX_with_schema function.")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    responses = {}

    if file_path:
        logging.info(f"Processing file input from {file_path}.")
        extracted_text = extract_text(file_path)
        if extracted_text is None:
            logging.error("Unsupported file type. Only PDF and TXT files are supported.")
            return {"error": "Unsupported file type. Only PDF and TXT files are supported."}
        text += "\n" + extracted_text
        logging.info("Text extracted and appended to main text.")

    for question in questions:
        logging.info(f"Preparing to submit question: {question}")
        prompt = f"{role_prompt}\n{text}\n\n###\n\n{question}\nAnswer:"
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if function_schema:
            data["functions"] = [function_schema]

        try:
            logging.info("Sending request to OpenAI API.")
            response = requests.post(url, headers=headers, json=data)
            response_data = response.json()

            if response.ok:
                logging.info("Received successful response from OpenAI API.")
                if function_schema:
                    responses[question] = response_data['choices'][0]['message']['function_call']['arguments']
                else:
                    responses[question] = response_data['choices'][0]['message']['content']
            else:
                logging.error(f"API request failed with status code {response.status_code}: {response.text}")
                responses[question] = f"API request failed with status code {response.status_code}: {response.text}"

        except requests.RequestException as e:
            logging.error(f"Request to OpenAI API failed: {e}")
            responses[question] = f"API request failed with error: {str(e)}"

        # Add a delay to see if the function pauses as expected
        time.sleep(0.5)

    logging.info("Completed processing all questions.")
    return responses
