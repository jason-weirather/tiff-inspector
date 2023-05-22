import xmltodict
from typing import Union, Optional, Any

import xml.etree.ElementTree as ET

import json, struct, html, pkg_resources

def load_schema(schema_name: str) -> dict:
    """
    Loads a JSON schema from a file.

    Args:
        schema_name (str): The name of the schema to be loaded. This is used to construct the 
                           filename by appending '.json' and it is assumed to be located in 
                           the '../schemas/' directory relative to 'tiffinspector'.

    Returns:
        dict: A dictionary representation of the JSON schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the file does not contain valid JSON.
    """
    schema_path = pkg_resources.resource_filename('tiffinspector', f'../schemas/{schema_name}.json')
    with open(schema_path, 'r') as file:
        schema = json.load(file)
    return schema

def is_xml(string: str) -> bool:
    """
    Determines if the provided string is valid XML.

    Args:
        string (str): The input string to be tested.

    Returns:
        bool: True if the string is valid XML, False otherwise.
    """
    try:
        ET.fromstring(string)
        return True
    except ET.ParseError:
        return False

def truncate_text(val: Any, max_text_length: int) -> str:
    """
    Truncates a text if its length exceeds the specified maximum length.

    Args:
        val: The input text to be truncated.
        max_text_length: The maximum allowed length for the text.

    Returns:
        The truncated text, with an ellipsis appended if truncation occurred.
    """
    val_str = str(val)
    return val_str if len(val_str) <= max_text_length else f'{val_str[0:max_text_length]}...'

def truncate_text_html(val: Any, max_text_length: Optional[int]) -> str:
    """
    Truncates a text if its length exceeds the specified maximum length and applies HTML styling.

    Args:
        val: The input text to be truncated.
        max_text_length: The maximum allowed length for the text.

    Returns:
        The truncated text, with an ellipsis and text length info in blue if truncation occurred.
    """
    val_str = str(val)
    if max_text_length is None: return val_str
    truncated_text = truncate_text(val, max_text_length)
    
    if len(val_str) > len(truncated_text):
        return f'<span style="color: blue;">({len(val_str)} characters):</span> {truncated_text} <span style="color: blue;">...</span>'
    
    return val_str

'''
def format_xml_as_html(xml_str: str):
    """
    Converts an XML string into an HTML-compatible string.

    Args:
        xml_str: XML string to be converted.

    Returns:
        HTML-compatible string, preserving XML structure and formatting.
    """
    html_str = xml_str.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"<pre>{html_str}</pre>"
'''
def parse_image_description(image_description: str) -> str:
    """
    Parses an XML image description and returns it as a dictionary.

    Args:
        image_description: A string of well-formed XML data with a root element.

    Returns:
        A dictionary representation of the XML data.

    Raises:
        xml.etree.ElementTree.ParseError: If the input string is not parseable as XML.
        KeyError: If the root element is missing in the XML data.
    """
    root = ET.fromstring(image_description)
    return xmltodict.parse(xmltodict.parse(image_description)['root'])



def truncate_tree(
    tree: Union[dict, list], 
    levels: Optional[int], 
    max_text_length: Optional[int]
) -> Union[dict, list]:
    """
    Truncates a tree-like structure (dict or list) to a specified depth. Nodes beyond the specified depth are replaced with a
    string indicating truncation. Supports both dict and list types for the tree.

    Args:
        tree: The tree-like structure to truncate. Dict keys are preserved in the output.
        levels: The maximum depth to preserve. If None, returns the original tree. If 0, truncates the entire tree.
        max_text_length: The maximum length for string representation of truncated parts. If None, includes the full string.

    Returns:
        The truncated version of the tree, matching the original tree type.
    """
    if levels is None:
        return tree
    if levels == 0:
        return {f"TRUNCATED ({len(tree.keys())})":json.dumps(tree) if max_text_length is None else truncate_text(json.dumps(tree),max_text_length=max_text_length)} if isinstance(tree,dict) else tree
    if isinstance(tree, dict):
        pruned_dict = {}
        for key, value in tree.items():
            pruned_dict[key] = truncate_tree(value, levels - 1, max_text_length)
        return pruned_dict
    elif isinstance(tree, list):
        pruned_list = []
        for item in tree:
            pruned_list.append(truncate_tree(item, levels - 1, max_text_length))
        return pruned_list
    else:
        return tree
