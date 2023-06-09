import json, html, re

import xmltodict

from IPython.display import JSON, HTML, Markdown
from .utils import is_xml, truncate_tree, truncate_text_html

def header_html(metadata,lineweight=2,width=25):
    # Create an empty HTML string
    html_str = ""

    for _property in metadata:
        # Add the the property to the HTML string
        html_str += f"<b>{_property}:</b> {metadata[_property]}<br>"
                
    # Add a horizontal line to separate the overall metadata from the page data
    if lineweight: 
        html_str += f'<hr style="border: {lineweight}px solid black; width: {width}%; padding-left: 10px; margin-left: 0;" />'
    return html_str
 
def display_report(self,expanded=False,levels=None,max_text_length=None):
        display(HTML(header_html(self.report['metadata'],lineweight=4,width=75)))
        for i, series in enumerate(self.report['series']):
            display(Markdown(f"## Series {i+1} of {self.report['series_count']}"))
            display(HTML(header_html(series['metadata'],lineweight=2,width=50)))

            for j, level in enumerate(series['levels']):
                display(Markdown(f"### Level {level['level_index']+1} of {series['level_count']}"))
                display(HTML(header_html(level['metadata'],lineweight=1,width=25)))

                for k, page in enumerate(level['pages']):
                    display(Markdown(f"#### Page {k+1} of {level['tiffpage_count']}"))
                    display(HTML(header_html(page['metadata'],lineweight=0)))

                    _tags_dict = dict([(x[0],x[4]) for x in page['tags']])
                    if 'ImageDescription' in _tags_dict and _tags_dict['ImageDescription'] is not None:
                        if is_xml(_tags_dict['ImageDescription']):
                            display(Markdown(f"**description:** (XML format)"))
                            _d = json.loads(json.dumps(xmltodict.parse(_tags_dict['ImageDescription'])))
                            display(JSON(json.loads(json.dumps(truncate_tree(_d,levels,max_text_length))),expanded=expanded))
                        else:
                            display(Markdown(f"**description:** (Plain text format)"))
                            display(HTML(truncate_text_html(html.escape(_tags_dict['ImageDescription']),max_text_length)))
                    else:
                        display(Markdown(f"**description:**\n{None}"))

                    display(HTML(_page_html(page,max_text_length)))
                    display(HTML(header_html({},lineweight=1)))
                    display(Markdown(f"#### Frames: {page['frame_count']}"))
                    display(Markdown(f"{list([x['metadata']['index'] for x in page['frames']])}"))

def _page_html(page,max_text_length=None,indent_str="&nbsp;&nbsp;&nbsp;"):
        # Add an indention for the tags table
        html_str = ""+indent_str
        # Create the table for the tags
        html_str += "<table>"
        # Iterate through the tags in the page
        html_str += "<tr><th><b>name</b></th>"
        html_str += "<th><b>dtype</b></th>"
        html_str += "<th><b>valueoffset</b></th>"
        html_str += "<th><b>count</b></th>"
        html_str += "<th style='text-align:left;'>value</b></th></tr>"
        for i, tag in enumerate(page['tags']):
            # Add the tag name and value to the HTML string
            html_str += f"<tr><td>{tag[0]}</td>"
            html_str += f"<td>{tag[1]}</td>"
            html_str += f"<td>{tag[2]}</td>"
            html_str += f"<td>{tag[3]}</td>"
            html_str += f"<td style='text-align:left;'>{truncate_text_html(html.escape(str(tag[4])),max_text_length)}</td></tr>"
        # Close the table for the tags
        html_str += "</table>"
        return html_str

def get_layout_text(self):
    text = ''
    for i, series in enumerate(self.report["series"]):
        series_name = series["metadata"].get("name", "Unnamed Series")
        text += f"Series index:{series['metadata']['index']} name:({series_name}) shape:{series['metadata']['shape']} axes:{series['metadata']['axes']}\n"
        for j, level in enumerate(series["levels"]):
            level_name = level['metadata'].get("name", "Unnamed Level")
            text += f"    Level index:{level['level_index']} name:({level_name}) shape:{level['metadata']['shape']} axes:{level['metadata']['axes']}\n"
            for k, page in enumerate(level["pages"]):
                text += f"        Page index:{page['metadata']['index']} shape:{page['metadata']['shape']} axes:{page['metadata']['axes']}\n"
                for k, frame in enumerate(page["frames"]):
                    # Although frames are a subset from a page, they are on the same level.
                    text += f"        Frame index:{frame['metadata']['index']} shape:{frame['metadata']['shape']} axes:{frame['metadata']['axes']}\n"
    return text.rstrip('\n')

def get_layout_html(self):
    html = '<div style="font-family: Arial, sans-serif; line-height: 1.25;">'
    for i, series in enumerate(self.report["series"]):
        series_name = series["metadata"].get("name", "Unnamed Series")
        html += f'<div><span style="color: navy;">Series</span> index:<span style="font-size: 110%; font-family: monospace;"><b>{series["metadata"]["index"]}</b></span> name:(<span style="font-size: 110%; font-family: monospace;"><b><u>{series_name}</u></b></span>) shape:<span style="font-size: 100%; font-family: monospace;">{_bold_integers_in_list(series["metadata"]["shape"])}</span> axes:<span style="font-size: 110%; font-family: monospace;"><b>{series["metadata"]["axes"]}</b></span></div>'
        for j, level in enumerate(series["levels"]):
            level_name = level["metadata"].get("name", "Unnamed Level")
            html += f'<div style="margin-left: 20px;"><span style="color: darkgreen;">Level</span> index:<span style="font-size: 110%; font-family: monospace;"><b>{level["level_index"]}</b></span> name:(<span style="font-size: 110%; font-family: monospace;"><b><u>{level_name}</u></b></span>) shape:<span style="font-size: 100%; font-family: monospace;">{_bold_integers_in_list(level["metadata"]["shape"])}</span> axes:<span style="font-size: 110%; font-family: monospace;"><b>{level["metadata"]["axes"]}</b></span></div>'
            for k, page in enumerate(level["pages"]):
                html += f'<div style="margin-left: 40px;"><span style="color: darkred;">Page</span> index:<span style="font-size: 100%; font-family: monospace;">{"<b>"+str(page["metadata"]["index"])+"</b>" if isinstance(page["metadata"]["index"],int) else _bold_integers_in_list(page["metadata"]["index"])}</span> shape:<span style="font-size: 100%; font-family: monospace;">{_bold_integers_in_list(page["metadata"]["shape"])}</span> axes:<span style="font-size: 100%; font-family: monospace;"><b>{page["metadata"]["axes"]}</b></span></div>'
                for l, frame in enumerate(page["frames"]):
                    html += f'<div style="margin-left: 40px;"><span style="color: darkorange;">Frame</span> index:<span style="font-size: 100%; font-family: monospace;"><b>{frame["metadata"]["index"]}</b></span> shape:<span style="font-size: 100%; font-family: monospace;">{_bold_integers_in_list(frame["metadata"]["shape"])}</span> axes:<span style="font-size: 110%; font-family: monospace;"><b>{frame["metadata"]["axes"]}</b></span></div>'
    html += '</div>'
    return html

def _bold_integers_in_list(input_list):
    """
    Function to bold integers in a list.
    It returns a HTML string with bolded integers.
    """
    # Convert the list to a string representation
    input_string = str(input_list)

    # This regular expression matches integers
    int_regex = re.compile(r'\b\d+\b')

    # This function will be used to replace matches with HTML bold tags
    def replace_with_bold(match):
        return f'<b>{match.group()}</b>'

    # Use the re.sub function to replace matches in the string
    html_string = int_regex.sub(replace_with_bold, input_string)
    return html_string
