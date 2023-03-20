import json, struct, html
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
        return {f"TRUNCATED ({len(tree.keys())})":truncate_text(json.dumps(tree),max_text_length=max_text_length)} if isinstance(tree,dict) else tree
    if isinstance(tree, dict):
        pruned_dict = {}
        for key, value in tree.items():
            pruned_dict[key] = truncate_tree(value, levels - 1, max_text_length)
        return pruned_dict
    elif isinstance(tree, list):
        pruned_list = []
        for item in tree:
            pruned_list.append(truncate_tree(item, levels - 1), max_text_length)
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

class TiffInspector:
    def __init__(self, file_path: str):
        self.file_path = file_path
        #version = get_tiff_version(self.file_path)
        self.tiff = tifffile.TiffFile(file_path)
        self.report = {
            "file_path": file_path,
            "shape": list(self.tiff.asarray().shape),
            "dtype": str(self.tiff.asarray().dtype),
            "byteorder": self.tiff.byteorder,
            "bigtiff": self.tiff.is_bigtiff,
            "series_count":len([x for x in self.tiff.series]),
            "page_count":len([x for x in self.tiff.pages]),
            "series": []
        }
        for i, series in enumerate(self.tiff.series):
            series_params = ['axes', 
                             'dtype', 
                             'index', 
                             'is_multifile', 
                             'is_pyramidal', 
                             'keyframe', 
                             'kind', 
                             'name', 
                             'ndim', 
                             'offset', 
                             'shape', 
                             'size', 
                             'transform']
            series_report = dict([(x,getattr(series, x)) for x in series_params])
            #series_report['pages'] = []
            series_report['keyframe'] = series_report['keyframe'].index
            series_report['dtype'] = str(series_report['dtype'])
            series_report['level_count'] = len(series.levels)
            series_report['shape'] = list(series_report['shape'])
            series_report['levels'] = []
            for j, level in enumerate(series.levels):
                level_report = {
                    "level_index":j,
                    "series_index":level.index,
                    "shape":list(level.shape),
                    "page_count":len(level.pages),
                    "tiffpage_count":len([x for x in level.pages if isinstance(x,TiffPage)]),
                    "tiffframe_count":len([x for x in level.pages if isinstance(x,TiffFrame)]),
                    "pages":[],
                    "frames":[]
                }
                for k, page in enumerate(level.pages):
                    if isinstance(page,TiffFrame):
                        frame_report = {
                            "index":page.index
                        }
                        level_report["frames"].append(frame_report)
                    else:
                        page_params = ['axes', 
                                   'chunked', 
                                   'chunks', 
                                   'colormap', 
                                   'dtype', 
                                   'extrasamples', 
                                   'flags', 
                                   'hash', 
                                   'index', 
                                   'is_ome', 
                                   'is_qpi', 
                                   'is_scn', 
                                   'is_svs',  
                                   'is_tiled', 
                                   'jpegheader', 
                                   'nbytes', 
                                   'ndim', 
                                   'sampleformat', 
                                   'shape', 
                                   'shaped', 
                                   'size'
                                  ]
                        page_report = dict([(x,getattr(page, x)) for x in page_params])
                        page_report['shape'] = list(page.shape)
                        page_report['dtype'] = str(page.dtype)
                        page_report['hash'] = f"0x{format(page_report['hash'] & 0xFFFFFFFF, '08x')}"
                        page_report['tags'] = self._tiff_tags_to_key_type_value_tuple(page.tags) if hasattr(page,'tags') else None
                        page_report['image_description'] = TiffInspector._get_description_text(page.tags) if hasattr(page,'tags') else None
                        page_report['sampleformat'] = sampleformat_to_text(page_report['sampleformat'])
                        page_report['index'] = list(page_report['index']) if isinstance(page_report['index'],tuple) else page_report['index']
                        page_report['flags'] = list(page_report['flags']) if isinstance(page_report['flags'],set) else page_report['flags']
                        level_report["pages"].append(page_report)
                series_report['levels'].append(level_report)
            self.report["series"].append(series_report)

    def _header_html(self):
        # Create an empty HTML string
        html_str = ""

        # Add the file path to the HTML string
        html_str += f"<b>File path:</b> {self.file_path}<br>"

        # Add the shape to the HTML string
        html_str += f"<b>Shape:</b> {self.report['shape']}<br>"

        # Add the data type to the HTML string
        html_str += f"<b>Data type:</b> {self.report['dtype']}<br>"

        # Add the byte order to the HTML string
        html_str += f"<b>Byte order:</b> {self.report['byteorder']}<br>"

        # Add whether the file is a BigTIFF file to the HTML string
        html_str += f"<b>BigTIFF:</b> {self.report['bigtiff']}<br>"
        
        # Add the total count of series
        html_str += f"<b>Number of Series:</b> {self.report['series_count']}<br>"
        
        # Add the total count of pages
        html_str += f"<b>Number of Pages:</b> {self.report['page_count']}<br>"
        
        # Add a horizontal line to separate the overall metadata from the page data
        html_str += "<hr>"
        return html_str
    
    def display_report(self,expanded=False,levels=None,max_text_length=None):
        display(HTML(self._header_html()))
        for i, series in enumerate(self.report['series']):
            display(Markdown(f"## Series {i+1} of {self.report['series_count']}"))
            for k1,v1 in series.items():
                if k1=='levels': continue
                display(Markdown(f"**{k1}:** {v1}"))
            display(Markdown('## '+'-'*40))
            for j, level in enumerate(series['levels']):
                display(Markdown(f"### Level {j+1} of {series['level_count']}"))
                for k2,v2 in level.items():
                    if k2=='pages': continue
                    display(Markdown(f"**{k2}:** {v2}"))
                
                display(Markdown('### '+'-'*30))
                for k, page in enumerate(level['pages']):
                    display(Markdown(f"#### Page {k+1} of {level['page_count']}"))
                    for k3,v3 in page.items():
                        if k3=='tags': continue
                        if k3=='image_description': continue
                        display(Markdown(f"**{k3}:** {v3}"))
                    # Add the page shape to the HTML string
                    if is_xml(page['image_description']) and page['image_description'] is not None:
                        _d = json.loads(json.dumps(xmltodict.parse(page['image_description'])))
                        display(JSON(json.loads(json.dumps(truncate_tree(_d,levels,max_text_length))),expanded=expanded))
                    elif page['image_description'] is not None:
                        display(HTML(truncate_text_html(html.escape(page['image_description']),max_text_length)))
                    #display(JSON(json.dumps(xmltodict.parse(page['image_description']))))
                    #display(JSON(json.dumps(xmltodict.parse(page['image_description']))))
                    display(HTML(TiffInspector._page_html(page,max_text_length)))
                    display(Markdown('#### '+'-'*20))
        
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

