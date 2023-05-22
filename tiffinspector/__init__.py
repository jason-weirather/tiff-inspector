from ._version import __version__


import tifffile, json
from tifffile import TiffPage, TiffFrame

#import xml.sax.saxutils

from typing import List, Tuple

from .report_generator import display_report as report_generator_display_report
from .utils import load_schema, truncate_text_html


def sampleformat_to_text(sampleformat):
    format_mapping = {
        1: "Unsigned integer data",
        2: "Two's complement signed integer data",
        3: "IEEE floating-point data",
        4: "Undefined data format"
    }    
    return format_mapping.get(sampleformat, "Unknown format")



class TiffInspector:
    def __init__(self, file_path: str, report: dict = None):
        self.file_path = file_path
        #version = get_tiff_version(self.file_path)
        self.tiff = tifffile.TiffFile(file_path)

        if report is not None:
            # In the case of a report being passed in we are basically copying another object
            # we force a deep copy on report
            self.report = json.loads(json.dumps(report))
            return

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

                page_report = None
                #level_report['frames'] = []

                # iterate over the pages
                for k, page in enumerate(level.pages):
                    if isinstance(page,TiffFrame):
                        if page_report is None:
                            raise ValueError("Expected to see a page before TiffFrame")
                        # get the metadata properties of the TiffFrame
                        frame_schema = load_schema('frame_schema')
                        frame_meta_properties = list(frame_schema['properties']['metadata']['properties'].keys())
                        frame_report = {
                            'metadata':dict([(x,getattr(page, x)) for x in frame_meta_properties])
                        }
                        # Nothing to fix at the moment
                        page_report['frames'].append(frame_report)
                        page_report['frame_count'] = len(page_report['frames'])
                    else:
                        # If theres a current page we need to store this one in the level
                        if page_report is not None:
                            level_report['pages'].append(page_report)

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
                        page_report['frames'] = []
                        page_report['frame_count'] = 0
                if page_report is not None:
                    level_report["pages"].append(page_report)
                series_report['levels'].append(level_report)
            self.report["series"].append(series_report)

    def series(self, series_slice):
        if isinstance(series_slice, slice):
            start, stop, step = series_slice.indices(len(self.report['series']))
            selected_series = [series for series in self.report['series'][start:stop:step]]
        elif isinstance(series_slice, int):
            selected_series = [self.report['series'][series_slice]]
        else:
            raise TypeError(f"Unsupported argument type {type(series_slice)}. Use int or slice.")
        new_report = json.loads(json.dumps(self.report))
        new_report['series'] = selected_series
        new_report['series_count'] = len(selected_series)
        return TiffInspector(file_path = self.file_path, report = new_report)

    def levels(self, levels_slice):
        if isinstance(levels_slice, slice):
            new_report = json.loads(json.dumps(self.report))
            new_report['series'] = []
            for series in self.report['series']:
                start, stop, step = levels_slice.indices(len(series['levels']))
                selected_levels = [level for level in series['levels'][start:stop:step]]
                if selected_levels:  # Only add the series if it contains at least one level
                    series_copy = series.copy()
                    series_copy['levels'] = selected_levels
                    new_report['series'].append(series_copy)
        elif isinstance(levels_slice, int):
            new_report = json.loads(json.dumps(self.report))
            new_report['series'] = []
            for series in self.report['series']:
                selected_levels = [series['levels'][levels_slice]]
                if selected_levels:  # Only add the series if it contains at least one level
                    series_copy = series.copy()
                    series_copy['levels'] = selected_levels
                    new_report['series'].append(series_copy)
        else:
            raise TypeError(f"Unsupported argument type {type(levels_slice)}. Use int or slice.")
        new_report = json.loads(json.dumps(new_report))
        for i, series in enumerate(new_report['series']):
            new_report['series'][i]['level_count'] = len(series['levels'])
        return TiffInspector(file_path = self.file_path, report = new_report)

    def display_structure(self):
        for i, series in enumerate(self.report["series"]):
            series_name = series["metadata"].get("name", "Unnamed Series")
            print(f"Series index:{series['metadata']['index']} name:({series_name}) shape:{series['metadata']['shape']}")
            for j, level in enumerate(series["levels"]):
                level_name = level['metadata'].get("name", "Unnamed Level")
                print(f"    Level index:{level['level_index']} name:({level_name}) shape:{level['metadata']['shape']}")
                for k, page in enumerate(level["pages"]):
                    #print(page['metadata'])
                    print(f"        Page index:{page['metadata']['index']} shape:{page['metadata']['shape']}")
                    for k, frame in enumerate(page["frames"]):
                        print(f"        Frame index:{frame['metadata']['index']}")

    
    def display_report(self,*args,**kwargs):
        return report_generator_display_report(self,*args,**kwargs)
        
    #def __repr__(self):
    #    return json.dumps(self.report, indent=2)
    
    #def _repr_html_(self):
    #    html_str = ""
    #    html_str += self._header_html()
    #    
    #    # Iterate through the pages in the report
    #    for page in self.report['pages']:
    #        # Add the page shape to the HTML string
    #        html_str += self._page_html()

    #    # Return the HTML string wrapped in a `pre` element
    #    return f"<pre>{html_str}</pre>"
    
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
            elif str(tag.dtype) in ['DATATYPES.RATIONAL','DATATYPES.SRATIONAL']:
                kvt_tuples.append([tag.name, str(tag.dtype), tag.valueoffset, tag.count, tag.value[0]/tag.value[1]])
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



