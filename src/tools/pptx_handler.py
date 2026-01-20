"""
PPTX Handler for Final_Template_V2_0.pptx
Works with pre-made slides - updates text in existing shapes.
"""

from pptx import Presentation
from pptx.util import Pt
from pathlib import Path
from config import settings
import logging


class PPTXHandler:
    """
    Handles PPTX operations for Final_Template_V2_0 template.
    Template has 12 pre-made slides - we update text in existing shapes.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("tools.pptx")
        self.template_path = settings.template_path
    
    def create_presentation(self, slides_content: list, output_path: Path) -> Path:
        """
        Create presentation from template by updating slide content.
        
        Args:
            slides_content: List of SlideContent objects from Agent 7
            output_path: Where to save the PPTX
            
        Returns:
            Path to created presentation
        """
        self.logger.info(f"Creating presentation: {output_path.name}")
        
        # Load template (has 12 pre-made slides)
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        
        prs = Presentation(str(self.template_path))
        self.logger.info(f"Loaded template with {len(prs.slides)} slides")
        
        # Update each slide with Agent 7's content
        for slide_data in slides_content:
            slide_num = slide_data.slide
            
            # Validate slide number
            if slide_num < 1 or slide_num > len(prs.slides):
                self.logger.warning(f"Slide {slide_num} out of range, skipping")
                continue
            
            # Get the template slide (0-indexed)
            slide = prs.slides[slide_num - 1]
            
            # Update slide content
            self._update_slide(slide, slide_data, slide_num)
        
        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(output_path))
        
        self.logger.info(f"Presentation saved: {output_path}")
        return output_path
    
    def _update_slide(self, slide, slide_data, slide_num: int):
        """
        Update a single slide with new content.
        
        Strategy:
        - Slides 7, 8, 9, 12: STATIC - skip (keep template as-is)
        - Other slides: Update text in shapes
        """
        # STATIC slides - don't modify
        if slide_num in [7, 8, 9, 12]:
            self.logger.info(f"Slide {slide_num}: STATIC - keeping template content")
            return
        
        # Check if this is a STATIC marker from Agent 7
        if slide_data.content == "STATIC_TEMPLATE":
            self.logger.info(f"Slide {slide_num}: STATIC marker - keeping template")
            return
        
        self.logger.info(f"Slide {slide_num}: Updating content - {slide_data.title}")
        
        # Update title (find first shape with title text)
        self._update_title(slide, slide_data.title)
        
        # Update content based on slide type
        if slide_num == 1:
            # Title slide - update subtitle
            self._update_title_slide(slide, slide_data)
        
        elif slide_num == 2:
            # Agenda - update bullets
            self._update_bulleted_slide(slide, slide_data)
        
        elif slide_num == 3:
            # Industry context - content + bullets
            self._update_content_slide(slide, slide_data)
        
        elif slide_num in [4, 5, 6]:
            # Pain slides - bullets
            self._update_bulleted_slide(slide, slide_data)
        
        elif slide_num in [10, 11]:
            # Solution slides - bullets
            self._update_bulleted_slide(slide, slide_data)
    
    def _update_title(self, slide, title: str):
        """Update slide title (first text shape or shapes.title)."""
        if not title:
            return
        
        # Try standard title shape first
        if slide.shapes.title:
            slide.shapes.title.text = title
            self.logger.debug(f"  Updated title: {title[:50]}...")
            return
        
        # Otherwise find first large text box (likely title)
        for shape in slide.shapes:
            if shape.has_text_frame:
                shape.text_frame.text = title
                self.logger.debug(f"  Updated title in text box: {title[:50]}...")
                return
    
    def _update_title_slide(self, slide, slide_data):
        """Update title slide (slide 1) with brand name."""
        # Title already updated in _update_title
        # Update subtitle if present
        for shape in slide.shapes:
            if shape.has_text_frame and shape != slide.shapes.title:
                # This is likely the subtitle
                if slide_data.content:
                    shape.text_frame.text = slide_data.content
                break
    
    def _update_bulleted_slide(self, slide, slide_data):
        """Update a slide with bullet points."""
        if not slide_data.bullets:
            return
        
        # Find the main content text box (usually largest text frame after title)
        content_shapes = [
            s for s in slide.shapes 
            if s.has_text_frame and s != slide.shapes.title
        ]
        
        if not content_shapes:
            self.logger.warning("  No content shapes found for bullets")
            return
        
        # Use the first/largest content shape
        content_shape = content_shapes[0]
        tf = content_shape.text_frame
        tf.clear()
        
        # Add bullets
        for i, bullet in enumerate(slide_data.bullets):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            
            p.text = self._clean_text(bullet)
            p.level = 0
            
            # Try to preserve font size
            if p.runs:
                p.runs[0].font.size = Pt(18)
        
        self.logger.debug(f"  Added {len(slide_data.bullets)} bullets")
    
    def _update_content_slide(self, slide, slide_data):
        """Update a slide with content paragraph + bullets."""
        # Find content shapes (exclude title)
        content_shapes = [
            s for s in slide.shapes 
            if s.has_text_frame and s != slide.shapes.title
        ]
        
        if not content_shapes:
            return
        
        content_shape = content_shapes[0]
        tf = content_shape.text_frame
        tf.clear()
        
        # Add content paragraph
        if slide_data.content:
            p = tf.paragraphs[0]
            p.text = self._clean_text(slide_data.content)
            p.level = 0
            if p.runs:
                p.runs[0].font.size = Pt(16)
        
        # Add bullets
        if slide_data.bullets:
            for bullet in slide_data.bullets:
                p = tf.add_paragraph()
                p.text = self._clean_text(bullet)
                p.level = 0
                if p.runs:
                    p.runs[0].font.size = Pt(18)
        
        self.logger.debug(f"  Added content + {len(slide_data.bullets or [])} bullets")
    
    def _clean_text(self, text: str) -> str:
        """Clean text for presentation."""
        if not text:
            return ""
        
        # Remove meta words
        remove_words = ["optional", "(optional)", "TBD", "if applicable"]
        for word in remove_words:
            text = text.replace(word, "")
            text = text.replace(word.capitalize(), "")
        
        return text.strip()