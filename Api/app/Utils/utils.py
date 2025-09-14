import ast
import json
import logging
import os
import dotenv
import asyncio
import re
from app.Utils.chatUtils import set_warning_context
from app.DB import schemas, crud
from typing import AsyncGenerator, Optional, Dict, List, Any
from app.DB.crud import get_last_llm0_response, get_navigation_by_name, get_navigation_configurations, get_promptname_by_id, get_entity_search_system_prompt_by_id
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Depends
from app.Utils.constants import TimeStampFormat, BasePath
from app.extractEnvVariables import llm_deployemnt_3_5, llm_deployemnt_4_o, non_kb_llm_deployment_4_0, llm_deployment_4_o_mini
from app.Utils.constants import LLM0_promptModel, LLM1_promptModel, LLM2_promptModel


# Load environment variables from .env file
dotenv.load_dotenv()

# Azure Storage configuration
parameters_container = os.getenv('PARAMETERS_CONTAINER')
account_name = os.getenv('ACCOUNT_NAME')
container_name = os.getenv('INPUT_FILES_CONTAINER')

def extract_json_array_from_string(input_string:str):
    try:
        # Regex to match JSON arrays between the two ### titles
        json_pattern = r'```json\n(\[.*?\])\n```'
        
        # Find all JSON arrays in the text
        json_matches = re.findall(json_pattern, input_string, re.DOTALL)
        
        # Convert the matched JSON strings to Python lists (arrays)
        json_arrays = [json.loads(match) for match in json_matches]

        if len(json_matches) > 0:
            return json_arrays
        else:
            json_data = extract_json_from_string(input_string)
            if "error" in json_data:
                return {
                    "error": "Failed to parse JSON response in extract_json_from_string ",
                }
            return json_data
    except ValueError as e:
        logging.warning(f"Found JSON within string but parsing failed: {e}")
    return {
        "error": "Failed to parse JSON response in extract_json_array_from_string",
    }


def extract_json_from_string(s: str):
    start_idx = s.find('{')
    end_idx = s.rfind('}')
    if start_idx != -1 and end_idx != -1:
        try:
            return json.loads(s[start_idx:end_idx+1])
        except ValueError as e:
            logging.warning(f"Found JSON within string but parsing failed: {e}")
    return {"error": "Failed to parse JSON response"}

def parse_json(data):
    # Create a mapping from id to label using a dictionary comprehension
    id_to_label = {
    field['id'].lower(): (
        'activityId' if field['id'].lower() == "activity_0_complianceactivity_complianceactivitycounter"
        else (field['id'] if field['id'].lower() == 'primaryentitykeyid' else field['label'])
        )
    for field in data['fields']
    }
    
    # Map the result section using the id_to_label dictionary
    mapped_result = []
    for item in data['result']:
        new_item = {id_to_label.get(key.lower(), key): value for key, value in item.items() if key.lower() in id_to_label}
        mapped_result.append(new_item)
    
    # Return only the result part as JSON
    return json.dumps(mapped_result)

async def parse_json_for_id(data, db, action,entityType):
    navigation_data_records = get_navigation_configurations(db)
    navigation_data = json.loads(navigation_data_records.data)
    
    # Track both the id_to_label mapping and count of each label
    id_to_label = {}
    label_count = {}
    
    for field in data.get('fields', []):
        if 'id' in field and 'label' in field:
            label = navigation_data.get(field['label'], field['label'])
            field_id = field['id'].lower()
            
            # Check for duplicate labels
            if label in label_count:
                label_count[label] += 1
                modified_label = f"{label}[{label_count[label]}]"
                id_to_label[field_id] = modified_label
            else:
                label_count[label] = 1
                id_to_label[field_id] = label
    
    # Navigation links part remains unchanged
    navigation_links = {}
    for item in id_to_label.values():
        nav_link = await get_navigation_by_name(db, item)
        if nav_link:
            action = action[0] if isinstance(action, list) else action
            if action is not None and (action.lower() == "create" or action.lower() == "launch"):
                print("Selected EntityType:",entityType)
                if entityType is not None:
                     nav_link = await get_navigation_by_name(db, entityType)
            navigation_links[item] = nav_link.url if nav_link is not None else ""
    
    # Transform results using the updated id_to_label mapping
    mapped_result = []
    for item in data.get('result', []):
        new_item = {
            id_to_label.get(key.lower(), key): value
            for key, value in item.items()
        }
        mapped_result.append(new_item)

    return {
        "navigation_links": navigation_links,
        "result": json.loads(json.dumps(mapped_result))
    }
    
async def change_navigation_links(data, db, conversationId, entityObject):
    llm_conversation = get_last_llm0_response(db,conversationId)
    
    if isinstance(llm_conversation.Response, str):
        parsed_response = ast.literal_eval(llm_conversation.Response)
    else:
        parsed_response = llm_conversation.Response  # Already a dictionary

    LLM0AssistanceMessage = json.dumps(parsed_response)
    LLM0AssistanceMessage = LLM0AssistanceMessage.replace("True", "true").replace("False", "false")
    LLM0AssistanceMessage = dict(parsed_response)

    json_llm_resposne = json.loads(json.dumps(LLM0AssistanceMessage))
    if json_llm_resposne.get("isSingleSelect", False):
        entity_id_value = entityObject.get("entityId",None) if type(entityObject) is dict else entityObject[0].get("entityId",None)
        if entity_id_value is not None:
            updated_links = {}
            for label, nav_link in data.get("navigation_links", {}).items():
                # replace only 'entityId' with the entityId value
                updated_link = nav_link.replace("'entityId'", f"{entity_id_value}")
                updated_links[label] = updated_link

            data["navigation_links"] = updated_links
    return data
        
async def fetch_and_map_navigation(data, db):
    # Fetch navigation data
    navigation_data_records = get_navigation_configurations(db)
    navigation_data = json.loads(navigation_data_records.data)
    # Mapping from field ID to the corresponding label (case-insensitive)
    id_to_label = {
        field['id'].lower(): (
            navigation_data.get(field['label'], field['label'])
        )
        for field in data.get('fields', []) if 'id' in field and 'label' in field
    }
    # Create a label-to-ids mapping, with prefix added to the label
    label_to_ids = {}
    for field in data.get('fields', []):
        label = field['label']
        field_id = field['id'].lower()  # case-insensitive key
        prefix = field_id.split('_')[0]  # Get the prefix before the first underscore
        modified_label = f"{prefix}_{label}"  # Combine prefix and label
        if modified_label not in label_to_ids:
            label_to_ids[modified_label] = []
        label_to_ids[modified_label].append(field_id)
    # Prepare navigation links
    navigation_links = {}
    for item in id_to_label.values():
        nav_link = await get_navigation_by_name(db, item)
        if nav_link:
            navigation_links[item] = nav_link.url
    # Map 'result' array items to their corresponding labels
    mapped_result = []
    for item in data.get('result', []):
        new_item = {}
        for key, value in item.items():
            mapped_key = key.lower()
            # If the key is 'id', apply any special handling (preserved logic)
            if 'id' in mapped_key:
                new_item[key] = value
            else:
                # Find the label for the given ID and map it
                found_label = None
                for label, ids in label_to_ids.items():
                    if mapped_key in ids:
                        found_label = label
                        break
                # Default to the original key if no match found
                new_item[found_label if found_label else key] = value
        mapped_result.append(new_item)
    # Return both the navigation links and the mapped result
    return {
        "navigation_links": navigation_links,
        "result": json.loads(json.dumps(mapped_result))
    }

async def stream_processor_text(response) -> AsyncGenerator[str, None]:
    event_id = 1
    accumulated_content = ""
    try:
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                accumulated_content += content
                yield f'event: {event_id},"content": "{content}", "accumulated_content": "{accumulated_content}", "is_last": False\n'
                event_id += 1
            await asyncio.sleep(0)  # Allow other tasks to run
        yield f'event: {event_id},"content": "{content}", "accumulated_content": "{accumulated_content}", "is_last": True'
    except Exception as e:
        logging.error(f"Error in stream_processor_text: {e}")
        yield f'event: error\ndata: {json.dumps({"error": str(e)})}\n\n'

async def stream_processor_json(response) -> AsyncGenerator[str, None]:
    event_id = 1
    accumulated_content = ""
    try:
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                accumulated_content += content
                yield json.dumps({
                    "event": event_id,
                    "data": {
                        "content": content,
                        "accumulated_content": accumulated_content,
                        "is_last": False
                    }
                }) + "\n"
                event_id += 1
            await asyncio.sleep(0)  # Allow other tasks to run
        yield json.dumps({
            "event": event_id,
            "data": {
                "content": "",
                "accumulated_content": accumulated_content,
                "is_last": True
            }
        }) + "\n"
    except Exception as e:
        logging.error(f"Error in stream_processor_json: {e}")
        yield json.dumps({"event": "error", "data": {"error": str(e)}}) + "\n"


def parse_streaming_json(data: str) -> tuple:
    def preprocess_json(s: str) -> str:
        # Add quotes to keys
        s = re.sub(r'(\w+):', r'"\1":', s)
        # Ensure all string values are properly quoted
        s = re.sub(r': (?![\{\[\"\d])(.*?)(?=,|}|$)', r': "\1"', s)
        return s

    try:
        # Attempt to parse the current data
        parsed_json = json.loads(data)
        return parsed_json, True
    except json.JSONDecodeError:
        # Check if we have a complete object
        if data.count('{') == data.count('}') and data.strip().startswith('{') and data.strip().endswith('}'):
            try:
                # Preprocess and try to parse again
                modified_data = preprocess_json(data)
                parsed_json = json.loads(modified_data)
                return parsed_json
            except json.JSONDecodeError as e:
                logging.warning(f"Failed to parse what looks like a complete JSON object: {data}")
                logging.warning(f"Error: {str(e)}")
        
        # If parsing failed and it's not a complete object, return None
        return None


def parse_error_message(error_input):
    try:
        # If the input is already a dictionary, no need to parse it
        if isinstance(error_input, dict):
            error_dict = error_input
        else:
            # Safely parse the string into a dictionary
            error_dict = json.loads(error_input)


        # Check if the dictionary has the expected keys
        if 'errorcode' in error_dict and 'errormessage' in error_dict:
            # Construct a structured error response similar to the provided example
            error_response = {
                "statusCode": error_dict.get('errorcode', 10404),  # Use provided error code or default
                "error": {
                    "name": "NoRelevantInformationError",  # Replace with an appropriate error name
                    "message": error_dict['errormessage'],
                    "response": error_dict  # Include the original error dictionary
                },
                "data": None
            }

            return error_response
        else:
            return None
    except json.JSONDecodeError:
        # Handle JSON parsing error
        return None
    except Exception as e:
        # Catch any other exceptions
        print(f"Unexpected error: {e}")
        return None
    

def handle_error(e):
    logging.error("Error occurred ", e)
    return {
        "statusCode": 500,
        "error": {
            "name": "Internal Server Error",
            "message": "Some technical issue occurred."
        },
        "data": None
    }


def storeDebugResponse(
    db: Session, 
    userQuery: Optional[str] = None, 
    debugData: Optional[Dict[str, Any]] = None, 
    startTime: Optional[datetime] = None, 
    endTime: Optional[datetime] = None,
    sessionId: Optional[str] = None
):
    base_dir = BasePath
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)

    timestamp = datetime.now().strftime(TimeStampFormat)
    
    if userQuery:
        file_name = f"query_{timestamp}.json"
        file_path = os.path.join(base_dir, file_name)
        debug_response = {
            "userQuery": userQuery,
            "llmRequestResponse": []
        }
        with open(file_path, 'w') as file:
            json.dump(debug_response, file, indent=4)
                
    elif debugData:
        query_files = [f for f in os.listdir(base_dir) if f.startswith("query_")]
        if not query_files:
            raise ValueError("No existing query file found")
        
        if sessionId:
            matching_files = []
            for query_file in query_files:
                file_path = os.path.join(base_dir, query_file)
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    if data.get("sessionId") == sessionId:
                        matching_files.append(query_file)
            
            if matching_files:
                latest_query = max(matching_files)
            else:
                latest_query = max(query_files)
        else:
            latest_query = max(query_files)
        
        file_path = os.path.join(base_dir, latest_query)
        
        with open(file_path, 'r') as file:
            debug_response = json.load(file)
        
        llm_request_response = {
            "prompt_name": "",
            "prompt_version": "",
            "prompt_parameters": "",
            "model": "",
            "system_prompt": "",
            "response": "",
            "prompt_tokens": 0,
            "output_tokens": 0,
            "start_time": "",
            "end_time": "",
            "time_taken": "",
            "error": "",
            "is_error": "error" in debugData or debugData.get("isError", False)
        }
        
        if llm_request_response["is_error"]:
            llm_request_response["error"] = debugData.get("error", "Unknown error")
        else:
            prompt_id = debugData.get("promptId")
            if prompt_id:
                llm_request_response.update({
                    "prompt_name": get_promptname_by_id(db, prompt_id),
                    "prompt_version": debugData.get("promptVersion", ""),
                    "model": debugData.get("modelUsed", ""),
                    "system_prompt": debugData.get("systemPrompt", ""),
                    "response": debugData.get("assistantMessage", ""),
                    "prompt_tokens": debugData.get("promptTokens", 0),
                    "output_tokens": debugData.get("completionTokens", 0)
                })
                
                llm0_data_by_id = get_entity_search_system_prompt_by_id(
                    db,
                    prompt_id,
                    prompt_version=debugData.get('promptVersion')
                )
                if llm0_data_by_id and llm0_data_by_id.chatParameters:
                    llm_request_response["prompt_parameters"] = json.loads(llm0_data_by_id.chatParameters)
        
        if startTime and endTime:
            llm_request_response.update({
                "start_time": startTime.isoformat(),
                "end_time": endTime.isoformat(),
                "time_taken": str(endTime - startTime)
            })
        else:
            llm_request_response["time_taken"] = "N/A"
        debug_response["llmRequestResponse"].append(llm_request_response)     
           
        with open(file_path, 'w') as file:
            json.dump(debug_response, file, indent=4)
        print(f"Updated query file with new response: {file_path}")
    
    return debug_response

def get_debug_info(chat: schemas.ChatCreate, db: Session):
    debug_request_body = chat.dict().get("debugRequestBody", {})
    if debug_request_body:
        final_debug_response = crud.process_all_prompts_and_screens(debug_request_body, db)
        debug_request_body.update(final_debug_response)
    return {
        "debugMode": True,
        "versionDetails": debug_request_body
    }

def storeApiDebugResponse(
    db: Session, 
    userQuery: Optional[str] = None, 
    debugData: Optional[Dict[str, Any]] = None, 
    sessionId: Optional[str] = None
)  -> Dict[str, Any]:
    llm_request_response = {
        "prompt_name": "",
        "prompt_version": "",
        "prompt_parameters": "",
        "model": "",
        "system_prompt": "",
        "response": "",
        "prompt_tokens": 0,
        "output_tokens": 0,
        "start_time": "",
        "end_time": "",
        "time_taken": "",
        "error": "",
        "is_error": "error" in debugData or debugData.get("isError", False)
    }

    # Handle error case
    if llm_request_response["is_error"]:
        llm_request_response["error"] = debugData.get("error", "Unknown error")
    else:
        prompt_id = debugData.get("promptId")
        if prompt_id:
            llm_request_response.update({
                "prompt_name": get_promptname_by_id(db, prompt_id),
                "prompt_version": debugData.get("promptVersion", ""),
                "model": debugData.get("modelUsed", ""),
                "system_prompt": debugData.get("systemPrompt", ""),
                "response": debugData.get("assistantMessage", ""),
                "prompt_tokens": debugData.get("promptTokens", 0),
                "output_tokens": debugData.get("completionTokens", 0),
                "start_time": debugData.get("start_time", ""),
                "end_time": debugData.get("end_time", ""),
                "time_taken": debugData.get("time_taken", "")
            })
            
            llm0_data_by_id = get_entity_search_system_prompt_by_id(
                db,
                prompt_id,
                prompt_version=debugData.get('promptVersion')
            )
            if llm0_data_by_id and llm0_data_by_id.chatParameters:
                llm_request_response["prompt_parameters"] = json.loads(llm0_data_by_id.chatParameters)

    debug_response = llm_request_response    
    return debug_response

def get_prompt_config(debugInfo, prompt_name, key_to_fetch, default=None): # :: Debug utility function :: 
    prompt_list = debugInfo.get("versionDetails", {}).get("prompt", [])
    if not prompt_list:
        return default
    for prompt in prompt_list:
        if prompt.get("name") == prompt_name:
            return prompt.get(key_to_fetch, default)


def get_DocLLM_ModelName(debugInfo): 
    debugmode = debugInfo.get("debugMode", False) 
    if debugmode:
        use_model = get_prompt_config(debugInfo, "DOC_LLM" , "model_deployment")  
    else:
        use_model = llm_deployemnt_3_5

    return use_model


def get_LLM0_ModelName(debugInfo,kb=False):
    debugmode = debugInfo.get("debugMode", False) 
    if debugmode:
        use_model = get_prompt_config(debugInfo, LLM0_promptModel, "model_deployment")  
    else:
        use_model = llm_deployment_4_o_mini if kb else non_kb_llm_deployment_4_0

    return use_model

def get_LLM1_ModelName(debugInfo,kb=False):
    use_model = llm_deployemnt_4_o if kb else non_kb_llm_deployment_4_0
    if debugInfo is not None:
        debugmode = debugInfo.get("debugMode", False)
        if debugmode:
            use_model = get_prompt_config(debugInfo, LLM1_promptModel, "model_deployment")              
    return use_model

def get_LLM2_ModelName(debugInfo,kb=False):  
    if debugInfo.get("debugMode", False) : 
        use_model = get_prompt_config(debugInfo, LLM2_promptModel, "model_deployment")  
    else:
        use_model = llm_deployemnt_4_o if kb else non_kb_llm_deployment_4_0
    return use_model

def get_SummaryLLM_ModelName(debugInfo):
    debugmode = debugInfo.get("debugMode", False) 
    if debugmode:
        use_model = get_prompt_config(debugInfo, "Summary_LLM", "model_deployment")  
    else:
        use_model = llm_deployemnt_4_o
    
    if not use_model or not str(use_model).strip():
        use_model = llm_deployemnt_4_o

    return use_model


def add_debug_response(debugInfo, response):
    if debugInfo and debugInfo.get("debugMode", False): 
        if "debugResponses" not in debugInfo:
            debugInfo["debugResponses"] = []
        debugInfo["debugResponses"].append(response)
    

def construct_debug_responses(debugInfo, db):
    constructedDebugResponses = {}
    debugResponses = debugInfo.get("debugResponses", [])

    for index, debug_data in enumerate(debugResponses):
        if isinstance(debug_data, dict):  
            constructedDebugResponses[f"llmresponses{index}"] = storeApiDebugResponse(db, debugData=debug_data)

    return constructedDebugResponses


async def time_async_function(func, *args, **kwargs):
    start_time = datetime.now()
    result = await func(*args, **kwargs)
    end_time = datetime.now()

    if isinstance(result, dict):
        result["start_time"] = start_time.isoformat()
        result["end_time"] = end_time.isoformat()
        result["time_taken"] = str(end_time - start_time)
    
    return result

async def process_nav_results_entity_specific(db, navigation_key, data):
    """ 
        Process navigation results for entity-specific navigation
    """
    nav_link = await crud.get_navigation_by_name(db, navigation_key)
    warning_message = None
    heading = None
    
    if nav_link.EntityTypeSupported:
        supported_types = {s.strip() for s in nav_link.EntityTypeSupported.split(",")}

        def get_entity_type(obj):
            return obj.get("entityType") or obj.get("Entity Type")

        filtered_entities = []
        removed_entities = []

        for obj in data:
            entity_type = get_entity_type(obj)
            if entity_type in supported_types:
                filtered_entities.append(obj)
            else:
                removed_entities.append(entity_type)

        if removed_entities:
            removed_types = set(filter(None, removed_entities))
            # Replace "Others" with "Non-Affiliate"
            replaced_types = [("Non-Affiliate" if t == "Other" else t) for t in removed_types]
            removed_types_str = " and ".join(replaced_types)
            warning_message = (
                f"{nav_link.name} for "
                f"{removed_types_str} are not possible and have been removed from the query."
            )
            
            if filtered_entities:
                warning_message += f"\nClick the entity name to launch the {nav_link.name}"
                
            set_warning_context({'warning':str(warning_message)})

    else:
        filtered_entities = data
    # Heading addition:
    if filtered_entities:
        entity_names = [e.get("entityName", "") for e in filtered_entities]
        entity_names_str = ", ".join(f"'{name}'" for name in entity_names)
        heading = f"{navigation_key} for {entity_names_str}"

    return filtered_entities, heading
    
def process_entities(data):
    if isinstance(data, list):
        mapped_result = [
            {
                ('primaryentitykeyid' if key.lower() == "entityid" else key): value 
                for key, value in item.items()
            }
            for item in data
        ]
        return {"result": mapped_result}
    
def process_nav_result(data):
    transformed_data = [
    {
        "primaryentitykeyid": item["primaryentitykeyid"],
        "Name": item["entityName"],
        "Entity Type": item["entityType"]
    }
    for item in data
    ]
    return transformed_data

def safe_parse_response(response):
    """ 
        Safely parses a string or object into a dictionary.
        Tries ast.literal_eval first, then json.loads. Returns an empty
        dictionary if parsing fails or if the result isn't a dict.
    """
    if isinstance(response, dict):
        return response
    if isinstance(response, str):
        try:
            parsed = ast.literal_eval(response)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return {}
