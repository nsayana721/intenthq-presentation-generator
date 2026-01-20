"""PPTX template handling utilities."""

from pptx import Presentation
from pathlib import Path
from config import settings
import logging


class PPTXHandler:
    """Handles PPTX template operations with format preservation."""
    
    def __init__(self):
        self.logger = logging.getLogger("tools.pptx")
        self.template_path = settings.template_path
    
    def find_shape_by_name(self, slide, name):
        """Find a shape on a slide by its name."""
        for shape in slide.shapes:
            if hasattr(shape, 'name') and shape.name == name:
                return shape
        return None
    
    def replace_text_preserve_format(self, shape, new_text):
        """Replace text in a shape while preserving ALL formatting."""
        if not hasattr(shape, 'text_frame'):
            return
        
        text_frame = shape.text_frame
        
        # Save original formatting
        para_format = {}
        run_format = None
        
        if text_frame.paragraphs:
            first_para = text_frame.paragraphs[0]
            para_format = {
                'alignment': first_para.alignment,
                'level': first_para.level,
                'space_before': first_para.space_before,
                'space_after': first_para.space_after,
                'line_spacing': first_para.line_spacing,
            }
            
            if first_para.runs:
                first_run = first_para.runs[0]
                run_format = {
                    'font_name': first_run.font.name,
                    'font_size': first_run.font.size,
                    'bold': first_run.font.bold,
                    'italic': first_run.font.italic,
                    'underline': first_run.font.underline,
                    'color_rgb': first_run.font.color.rgb if first_run.font.color.type == 1 else None,
                    'color_theme': first_run.font.color.theme_color if first_run.font.color.type == 2 else None,
                }
        
        # Clear and add new text
        text_frame.clear()
        p = text_frame.paragraphs[0]
        
        # Restore paragraph formatting
        if para_format:
            p.alignment = para_format['alignment']
            p.level = para_format['level']
            if para_format['space_before'] is not None:
                p.space_before = para_format['space_before']
            if para_format['space_after'] is not None:
                p.space_after = para_format['space_after']
            if para_format['line_spacing'] is not None:
                p.line_spacing = para_format['line_spacing']
        
        # Add text with formatting
        run = p.add_run()
        run.text = new_text
        
        if run_format:
            if run_format['font_name']:
                run.font.name = run_format['font_name']
            if run_format['font_size']:
                run.font.size = run_format['font_size']
            if run_format['bold'] is not None:
                run.font.bold = run_format['bold']
            if run_format['italic'] is not None:
                run.font.italic = run_format['italic']
            if run_format['underline'] is not None:
                run.font.underline = run_format['underline']
            if run_format['color_rgb']:
                run.font.color.rgb = run_format['color_rgb']
            elif run_format['color_theme']:
                run.font.color.theme_color = run_format['color_theme']
    
    def create_presentation(self, content_json, output_path: Path) -> Path:
        """
        Create presentation from template and content.
        
        Args:
            content_json: ContentCreatorOutput object
            output_path: Where to save the PPTX
            
        Returns:
            Path to created presentation
        """
        self.logger.info(f"Creating presentation: {output_path.name}")
        
        # Load template
        prs = Presentation(str(self.template_path))
        self.logger.info(f"Loaded template from {self.template_path}")
        
        brand = content_json.brand
        slides_data = content_json.slides
        
        # Process each slide
        for slide_data in slides_data:
            slide_num = slide_data.slide
            slide_index = slide_num - 1
            
            if slide_index >= len(prs.slides):
                self.logger.warning(f"Slide {slide_num} not found in template")
                continue
            
            slide = prs.slides[slide_index]
            self.logger.info(f"Processing Slide {slide_num}: {slide_data.title}")
            
            # SLIDE 1: Brand name
            if slide_num == 1:
                shape = self.find_shape_by_name(slide, 'BRAND_NAME')
                if shape:
                    self.replace_text_preserve_format(shape, brand)
                    self.logger.info(f"  ✓ Replaced BRAND_NAME with '{brand}'")
            
            # SLIDE 2: Static
            elif slide_num == 2:
                self.logger.info("  ⊘ Skipping (static agenda)")
            
            # SLIDE 3: Industry Context
            elif slide_num == 3:
                if slide_data.content and slide_data.content != "STATIC_TEMPLATE":
                    shape = self.find_shape_by_name(slide, 'CONTENT_BOX')
                    if shape:
                        self.replace_text_preserve_format(shape, slide_data.content)
                        self.logger.info("  ✓ Replaced CONTENT_BOX")
                
                # Bullets (up to 3)
                for i in range(min(3, len(slide_data.bullets or []))):
                    shape = self.find_shape_by_name(slide, f'BULLET_{i+1}')
                    if shape:
                        self.replace_text_preserve_format(shape, slide_data.bullets[i])
                        self.logger.info(f"  ✓ Replaced BULLET_{i+1}")
            
            # SLIDES 4-6: Use Cases
            elif slide_num in [4, 5, 6]:
                usecase_num = slide_num - 3
                
                # Title
                shape = self.find_shape_by_name(slide, f'USECASE_{usecase_num}_TITLE')
                if shape:
                    self.replace_text_preserve_format(shape, slide_data.title)
                    self.logger.info(f"  ✓ Replaced USECASE_{usecase_num}_TITLE")
                
                # Bullets (up to 3)
                for i in range(min(3, len(slide_data.bullets or []))):
                    shape = self.find_shape_by_name(slide, f'BULLET_{i+1}')
                    if shape:
                        self.replace_text_preserve_format(shape, slide_data.bullets[i])
                        self.logger.info(f"  ✓ Replaced BULLET_{i+1}")
            
            # SLIDES 7-9: Static
            elif slide_num in [7, 8, 9]:
                self.logger.info("  ⊘ Skipping (static slide)")
            
            # SLIDE 10: Primary Solution
            elif slide_num == 10:
                # Find JSON slide 10 data
                json_slide_10 = next((s for s in slides_data if s.slide == 10), None)
                if json_slide_10:
                    # Title
                    shape = self.find_shape_by_name(slide, 'PRIMARY_SOLUTION_TITLE')
                    if shape:
                        self.replace_text_preserve_format(shape, json_slide_10.title or "Primary Solution")
                        self.logger.info("  ✓ Replaced PRIMARY_SOLUTION_TITLE")
                    
                    # Bullets (up to 3)
                    for i in range(min(3, len(json_slide_10.bullets or []))):
                        shape = self.find_shape_by_name(slide, f'BULLET_{i+1}')
                        if shape:
                            self.replace_text_preserve_format(shape, json_slide_10.bullets[i])
                            self.logger.info(f"  ✓ Replaced BULLET_{i+1}")
            
            # SLIDE 11: Secondary Solutions
            elif slide_num == 11:
                # Find JSON slide 11 data
                json_slide_11 = next((s for s in slides_data if s.slide == 11), None)
                if json_slide_11:
                    # Title
                    shape = self.find_shape_by_name(slide, 'SECONDARY_SOLUTION_TITLE')
                    if shape:
                        self.replace_text_preserve_format(shape, json_slide_11.title or "Complementary Solutions")
                        self.logger.info("  ✓ Replaced SECONDARY_SOLUTION_TITLE")
                    
                    # Bullets (up to 3)
                    for i in range(min(3, len(json_slide_11.bullets or []))):
                        shape = self.find_shape_by_name(slide, f'BULLET_{i+1}')
                        if shape:
                            self.replace_text_preserve_format(shape, json_slide_11.bullets[i])
                            self.logger.info(f"  ✓ Replaced BULLET_{i+1}")
            
            # SLIDE 12: Static
            elif slide_num == 12:
                self.logger.info("  ⊘ Skipping (static slide)")
        
        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(output_path))
        
        self.logger.info(f"✅ Presentation saved: {output_path}")
        return output_path