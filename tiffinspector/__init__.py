import json, struct, html, pkg_resources
import tifffile
from tifffile import TiffPage, TiffFrame

import xml.sax.saxutils
import xml.etree.ElementTree as ET
from typing import List, Tuple
import xmltodict
from IPython.display import JSON, HTML, Markdown

def truncate_tree(tree, levels, max_text_length):
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

def parse_image_description(image_description: str) -> str:
    root = ET.fromstring(image_description)
    return xmltodict.parse(xmltodict.parse(image_description)['root'])
        
def format_xml_as_html(xml_str: str):
    html_str = xml_str.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"<pre>{html_str}</pre>"

def truncate_text(val,max_text_length):
    return str(val) if len(str(val)) <= max_text_length else f'{val[0:max_text_length]}...'

def truncate_text_html(val,max_text_length):
    if max_text_length is None or len(val)<=max_text_length:
        return val
    return f'<span style="color: blue;">({len(val)} characters):</span> {val[0:max_text_length]} <span style="color: blue;">...</span>'
def sampleformat_to_text(sampleformat):
    format_mapping = {
        1: "Unsigned integer data",
        2: "Two's complement signed integer data",
        3: "IEEE floating-point data",
        4: "Undefined data format"
    }
    
    return format_mapping.get(sampleformat, "Unknown format")

def is_xml(string):
    try:
        ET.fromstring(string)
        return True
    except ET.ParseError:
        return False

def load_schema(schema_name):
    schema_path = pkg_resources.resource_filename('tiffinspector', f'../schemas/{schema_name}.json')
    with open(schema_path, 'r') as file:
        schema = json.load(file)
    return schema

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

class TiffInspector:
    def __init__(self, file_path: str):
        self.file_path = file_path
        #version = get_tiff_version(self.file_path)
        self.tiff = tifffile.TiffFile(file_path)

        # Get metadata properties to extract programatically
        tiff_schema = load_schema('tiff_schema')
        tiff_meta_properties = list(tiff_schema['properties']['metadata']['properties'].keys())
        self.report = {
            'metadata':dict([(x,getattr(self.tiff, x)) for x in tiff_meta_properties])
        }
        # clean up the automatically read-in data to make sure list-likes are saved json-compatible lists
        for _property in self.report['metadata'].keys():
            if isinstance(getattr(self.tiff, _property),tuple): 
                self.report['metadata'][_property] = list(self.report['metadata'][_property])
            if isinstance(getattr(self.tiff, _property),set): 
                self.report['metadata'][_property] = list(self.report['metadata'][_property])

        # Get other properties that are either not primary properties of TiffFile, or are the tree-structered child properties
        self.report['shape'] = list(self.tiff.asarray().shape)
        self.report['dtype'] = str(self.tiff.asarray().dtype)
        self.report['series'] = []
        self.report['series_count'] = len([x for x in self.tiff.series])
        self.report['page_count'] = len([x for x in self.tiff.pages])

        # iterate over the series
        for i, series in enumerate(self.tiff.series):

            # Get metadata properties to extract programatically
            series_schema = load_schema('series_schema')
            series_meta_properties = list(series_schema['properties']['metadata']['properties'].keys())
            series_report = {
                'metadata':dict([(x,getattr(series, x)) for x in series_meta_properties])
            }
            # clean up the automatically read-in data to make sure list-likes are saved json-compatible lists
            for _property in series_report['metadata'].keys():
                if isinstance(getattr(series, _property),tuple): 
                    series_report['metadata'][_property] = list(series_report['metadata'][_property])
                if isinstance(getattr(series, _property),set): 
                    series_report['metadata'][_property] = list(series_report['metadata'][_property])
            
            # fix parameters to better fit the json
            series_report['metadata']['keyframe'] = series_report['metadata']['keyframe'].index
            series_report['metadata']['dtype'] = str(series_report['metadata']['dtype'])
            series_report['level_count'] = len(series.levels)
            series_report['levels'] = []

            # iterate over the levels
            for j, level in enumerate(series.levels):
                # Get metadata properties to extract programatically
                level_schema = load_schema('level_schema')
                level_meta_properties = list(level_schema['properties']['metadata']['properties'].keys())
                level_report = {
                    'metadata':dict([(x,getattr(level, x)) for x in level_meta_properties])
                }
                # clean up the automatically read-in data to make sure list-likes are saved json-compatible lists
                for _property in level_report['metadata'].keys():
                    if isinstance(getattr(level, _property),tuple): 
                        level_report['metadata'][_property] = list(level_report['metadata'][_property])
                    if isinstance(getattr(series, _property),set): 
                        level_report['metadata'][_property] = list(level_report['metadata'][_property])

                level_report['page_count'] = len(level.pages)
                level_report['level_index'] = j
                level_report['tiffpage_count'] = len([x for x in level.pages if isinstance(x,TiffPage)])
                level_report['tiffframe_count'] = len([x for x in level.pages if isinstance(x,TiffFrame)])
                level_report['pages'] = []
                level_report['frames'] = []

                # iterate over the pages
                for k, page in enumerate(level.pages):
                    if isinstance(page,TiffFrame):

                        # get the metadata properties of the TiffFrame
                        frame_schema = load_schema('frame_schema')
                        frame_meta_properties = list(frame_schema['properties']['metadata']['properties'].keys())
                        frame_report = {
                            'metadata':dict([(x,getattr(page, x)) for x in frame_meta_properties])
                        }
                        # Nothing to fix at the moment
                        level_report["frames"].append(frame_report)
                    else:
                        # get the metadata properties of the TiffPage
                        page_schema = load_schema('page_schema')
                        page_meta_properties = list(page_schema['properties']['metadata']['properties'].keys())
                        page_report = {
                            'metadata':dict([(x,getattr(page, x)) for x in page_meta_properties])
                        }

                        # Fix any list-like for json
                        for _property in page_report['metadata'].keys():
                            if isinstance(getattr(page, _property),tuple): 
                                page_report['metadata'][_property] = list(page_report['metadata'][_property])
                            if isinstance(getattr(page, _property),set): 
                                page_report['metadata'][_property] = list(page_report['metadata'][_property])

                        #page_report = dict([(x,getattr(page, x)) for x in page_params])
                        page_report['metadata']['shape'] = list(page.shape)
                        page_report['metadata']['dtype'] = str(page.dtype)
                        page_report['metadata']['hash'] = f"0x{format(page_report['metadata']['hash'] & 0xFFFFFFFF, '08x')}"
                        page_report['tags'] = self._tiff_tags_to_key_type_value_tuple(page.tags) if hasattr(page,'tags') else None
                        #page_report['image_description'] = TiffInspector._get_description_text(page.tags) if hasattr(page,'tags') else None
                        page_report['metadata']['sampleformat'] = sampleformat_to_text(page_report['metadata']['sampleformat'])
                        level_report["pages"].append(page_report)
                series_report['levels'].append(level_report)
            self.report["series"].append(series_report)

    
    def display_report(self,expanded=False,levels=None,max_text_length=None):
        display(HTML(header_html(self.report['metadata'],lineweight=4,width=75)))
        for i, series in enumerate(self.report['series']):
            display(Markdown(f"## Series {i+1} of {self.report['series_count']}"))
            display(HTML(header_html(series['metadata'],lineweight=2,width=50)))

            for j, level in enumerate(series['levels']):
                display(Markdown(f"### Level {j+1} of {series['level_count']}"))
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

                    display(HTML(TiffInspector._page_html(page,max_text_length)))
                    display(HTML(header_html({},lineweight=1)))
                display(Markdown(f"#### Frames: {len(level['frames'])}"))
                display(Markdown(f"{list([x['metadata']['index'] for x in level['frames']])}"))

        
    def __repr__(self):
        return json.dumps(self.report, indent=2)
    
    def _repr_html_(self):
        html_str = ""
        html_str += self._header_html()
        
        # Iterate through the pages in the report
        for page in self.report['pages']:
            # Add the page shape to the HTML string
            html_str += self._page_html()

        # Return the HTML string wrapped in a `pre` element
        return f"<pre>{html_str}</pre>"
    
    #<p style="color: blue;">ASCII (38085 characters)</p>
    def _tiff_tags_to_key_type_value_tuple(self, tiff_tags):
        kvt_tuples = []
        for tag in tiff_tags:
            #print(tag.dtype)
            if isinstance(tag.value, bytes):
                #print(("BYTES",tag.name))
                kvt_tuples.append([tag.name,
                                   str(tag.dtype),
                                   tag.valueoffset, 
                                   tag.count, 
                                   '0x'+tag.value.hex()
                                  ])
            else:
                kvt_tuples.append([tag.name,str(tag.dtype), tag.valueoffset, tag.count, list(tag.value) if isinstance(tag.value,tuple) else tag.value])
        return kvt_tuples


    
    
    @classmethod
    def _get_description_text(cls, tiff_tags):
        kvt_tuples = []
        for tag in tiff_tags:
            #print(tag.dtype)
            if tag.name=='ImageDescription':
                return tag.value
        return None
    @classmethod
    def _page_html(cls, page,max_text_length=None,indent_str="&nbsp;&nbsp;&nbsp;"):
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

