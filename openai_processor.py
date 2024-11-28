import os
import logging
import pandas as pd
from typing import Dict, List, Optional, Union
from ai_utils import query_openai_gptX_with_schema

def process_medical_records_with_gpt(
    records_df: pd.DataFrame,
    questions: List[str],
    role_prompt: str,
    model_name: str,
    api_key: str,
    config: Dict,
    testing: bool = False
) -> pd.DataFrame:
    """
    Process medical records through GPT API for analysis and summarization
    
    Args:
        records_df: DataFrame containing medical records to process
        questions: List of questions to ask GPT about each record
        role_prompt: System prompt defining GPT's role and context
        model_name: Name of the GPT model to use
        api_key: OpenAI API key
        config: Configuration dictionary containing processing settings
        testing: Boolean flag for testing mode
    
    Returns:
        DataFrame with processed records including GPT analysis
    """
    # Ensure required columns exist
    if 'Processed' not in records_df.columns:
        records_df['Processed'] = False
    
    for index, row in records_df.iterrows():
        # Skip already processed records unless in testing mode
        if not testing and row.get('Processed', False):
            logging.info(f"Skipping record {index} - Already processed")
            continue
            
        logging.info(f"Processing record {index}")
        
        # Get the text content to process
        text = row.get('text', '')
        if not text:
            logging.warning(f"No text content for record {index}")
            continue
            
        try:
            # Handle PDF files that couldn't be processed normally
            if "Could not extract text from PDF" in text:
                file_path = row.get('file_path', '')
                if file_path and os.path.exists(file_path) and file_path.lower().endswith('.pdf'):
                    logging.info(f"Sending PDF file directly to GPT: {file_path}")
                    response = query_openai_gptX_with_schema(
                        text=None,
                        questions=questions,
                        role_prompt=role_prompt,
                        model_name=model_name,
                        api_key=api_key,
                        file_path=file_path,
                        function_schema=None,
                        max_tokens=3000,
                        temperature=0.1
                    )
                else:
                    raise ValueError(f"PDF file not found or invalid: {file_path}")
            else:
                # Process normally with extracted text
                logging.info(f"Sending to GPT: {text[:100]}...")
                response = query_openai_gptX_with_schema(
                    text=text,
                    questions=questions,
                    role_prompt=role_prompt,
                    model_name=model_name,
                    api_key=api_key,
                    file_path=None,
                    function_schema=None,
                    max_tokens=3000,
                    temperature=0.1
                )
            
            # Process the GPT response
            if isinstance(response, dict):
                # Update DataFrame with all response fields
                for key, value in response.items():
                    if isinstance(value, str):
                        records_df.at[index, key] = value.strip()
                    else:
                        records_df.at[index, key] = value
                
                logging.info(f"Successfully processed record {index}")
            else:
                logging.warning(f"Unexpected response format from GPT for record {index}")
                records_df.at[index, 'processing_error'] = "Unexpected response format"
            
            # Mark as processed
            records_df.at[index, 'Processed'] = True
            
        except Exception as e:
            error_msg = f"Error processing record {index} through GPT: {str(e)}"
            logging.error(error_msg)
            records_df.at[index, 'processing_error'] = error_msg
            continue

    return records_df

def batch_process_medical_records(
    records_df: pd.DataFrame,
    config: Dict,
    questions: Optional[List[str]] = None,
    testing: bool = False
) -> pd.DataFrame:
    """
    High-level function to process medical records in batches
    
    Args:
        records_df: DataFrame containing medical records to process
        config: Configuration dictionary containing API settings and prompts
        questions: Optional list of questions to override config questions
        testing: Boolean flag for testing mode
    
    Returns:
        DataFrame with processed records
    """
    # Get processing parameters from config
    api_key = config.get('openai_api_key')
    if not api_key:
        raise ValueError("OpenAI API key not found in config")
        
    model_name = config.get('model_name', 'gpt-4')
    role_prompt = config.get('role_prompt', 'You are a medical records analyst.')
    default_questions = config.get('analysis_questions', [
        "What is the primary medical condition discussed?",
        "What are the key findings or diagnoses?",
        "What are the recommended treatments or next steps?"
    ])
    
    # Use provided questions or fall back to config/default questions
    questions_to_use = questions if questions is not None else default_questions
    
    # Process records
    processed_df = process_medical_records_with_gpt(
        records_df=records_df,
        questions=questions_to_use,
        role_prompt=role_prompt,
        model_name=model_name,
        api_key=api_key,
        config=config,
        testing=testing
    )
    
    return processed_df
