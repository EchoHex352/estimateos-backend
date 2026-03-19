"""
AI Blueprint Analyzer
Uses Anthropic Claude to analyze construction blueprints and detect materials
"""

import anthropic
import base64
import json
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class BlueprintAnalyzer:
    """Analyze construction blueprints using AI"""
    
    def __init__(self):
        """Initialize AI analyzer with Anthropic API"""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("WARNING: ANTHROPIC_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # CSI Division knowledge
        self.division_knowledge = self._load_division_knowledge()
    
    def _load_division_knowledge(self) -> Dict:
        """Load CSI division knowledge for better analysis"""
        return {
            '03': {
                'name': 'Concrete',
                'materials': ['concrete slab', 'footing', 'foundation', 'beam', 'column', 'wall'],
                'units': ['CY', 'SF', 'LF']
            },
            '04': {
                'name': 'Masonry',
                'materials': ['CMU block', 'brick', 'stone', 'mortar', 'grout'],
                'units': ['SF', 'EA', 'CY']
            },
            '05': {
                'name': 'Metals',
                'materials': ['structural steel', 'beam', 'column', 'joist', 'decking', 'railing'],
                'units': ['TON', 'LB', 'LF', 'SF']
            },
            '08': {
                'name': 'Openings',
                'materials': ['door', 'window', 'frame', 'hardware'],
                'units': ['EA']
            },
            '09': {
                'name': 'Finishes',
                'materials': ['drywall', 'paint', 'flooring', 'tile', 'ceiling'],
                'units': ['SF', 'SY']
            },
            '22': {
                'name': 'Plumbing',
                'materials': ['pipe', 'fixture', 'valve', 'water heater'],
                'units': ['EA', 'LF']
            },
            '23': {
                'name': 'HVAC',
                'materials': ['ductwork', 'air handler', 'diffuser', 'grille'],
                'units': ['SF', 'EA', 'LF']
            },
            '26': {
                'name': 'Electrical',
                'materials': ['panel', 'receptacle', 'switch', 'fixture', 'conduit'],
                'units': ['EA', 'LF']
            }
        }
    
    async def analyze_blueprint(
        self,
        image_path: str,
        ocr_text: str,
        selected_divisions: List[str],
        legend_info: Optional[str] = None
    ) -> Dict:
        """
        Analyze a blueprint page and detect materials
        
        Args:
            image_path: Path to blueprint image
            ocr_text: Text extracted from page via OCR
            selected_divisions: List of CSI divisions to focus on
            legend_info: Optional legend/schedule information
        
        Returns:
            Dictionary with detected materials and their properties
        """
        if not self.client:
            # Return mock data if API key not configured
            return self._generate_mock_analysis(selected_divisions)
        
        try:
            # Read and encode image
            with open(image_path, "rb") as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Build division context
            division_context = self._build_division_context(selected_divisions)
            
            # Create prompt
            user_prompt = self._build_analysis_prompt(
                selected_divisions=selected_divisions,
                division_context=division_context,
                ocr_text=ocr_text,
                legend_info=legend_info or "No legend visible on this page"
            )
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ]
            )
            
            # Parse response
            response_text = response.content[0].text
            results = self._parse_claude_response(response_text)
            
            return results
            
        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")
            return {"materials": [], "error": str(e)}
    
    def _build_division_context(self, selected_divisions: List[str]) -> str:
        """Build context about selected divisions"""
        context_parts = []
        
        for div_id in selected_divisions:
            if div_id in self.division_knowledge:
                div_info = self.division_knowledge[div_id]
                context_parts.append(
                    f"Division {div_id} - {div_info['name']}: "
                    f"Look for {', '.join(div_info['materials'])}. "
                    f"Common units: {', '.join(div_info['units'])}"
                )
        
        return "\n".join(context_parts)
    
    def _build_analysis_prompt(
        self,
        selected_divisions: List[str],
        division_context: str,
        ocr_text: str,
        legend_info: str
    ) -> str:
        """Build the analysis prompt for Claude"""
        
        prompt = f"""You are an expert construction estimator analyzing a blueprint for quantity takeoff.

SELECTED DIVISIONS TO ANALYZE:
{', '.join(selected_divisions)}

DIVISION CONTEXT:
{division_context}

OCR EXTRACTED TEXT FROM THIS PAGE:
{ocr_text[:2000]}  

LEGEND/SCHEDULE INFORMATION:
{legend_info}

YOUR TASK:
Carefully analyze this construction blueprint and identify ALL materials that belong to the selected divisions.

For EACH material you identify:
1. Division (CSI code from selected divisions)
2. Material type (specific, e.g., "Concrete Slab 6 inch" not just "Concrete")
3. Description (detailed specifications)
4. Location/bounding box (approximate x, y, width, height coordinates on the drawing)
5. Quantity (numerical estimate based on dimensions shown)
6. Unit (SF, LF, CY, EA, etc. - use appropriate unit for the material)
7. Confidence level (high/medium/low based on clarity of drawing)
8. Notes (any important details, dimensions, or specifications)

IMPORTANT GUIDELINES:
- Use dimensions shown on the drawing to calculate quantities
- If dimensions aren't clear, note "Needs verification" in notes
- For areas: calculate Length × Width in appropriate unit
- For volumes: calculate Length × Width × Depth
- For linear items: sum up all lengths
- For counted items: count each occurrence
- Cross-reference with schedules/legends if visible
- Consider typical construction conventions

Return ONLY a valid JSON object in this exact format:
{{
  "materials": [
    {{
      "division": "03",
      "material_type": "Concrete Slab",
      "description": "6 inch thick slab on grade with WWF",
      "bbox": {{"x": 100, "y": 200, "width": 300, "height": 150}},
      "quantity": 1200,
      "unit": "SF",
      "confidence": "high",
      "notes": "Based on 30' x 40' dimensions shown"
    }}
  ],
  "legend_items": [],
  "schedules": []
}}

Analyze this blueprint now and return the JSON:"""
        
        return prompt
    
    def _parse_claude_response(self, response_text: str) -> Dict:
        """Parse Claude's JSON response"""
        try:
            # Try to extract JSON from response
            # Claude might wrap it in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            # Parse JSON
            results = json.loads(json_text)
            
            # Validate structure
            if 'materials' not in results:
                results['materials'] = []
            
            return results
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {str(e)}")
            print(f"Response was: {response_text[:500]}")
            return {"materials": [], "error": "Failed to parse AI response"}
    
    def _generate_mock_analysis(self, selected_divisions: List[str]) -> Dict:
        """Generate mock analysis for testing without API key"""
        mock_materials = {
            '03': [
                {
                    "division": "03",
                    "material_type": "Concrete Slab",
                    "description": "6 inch thick slab on grade",
                    "bbox": {"x": 150, "y": 200, "width": 300, "height": 200},
                    "quantity": 1200,
                    "unit": "SF",
                    "confidence": "high",
                    "notes": "Mock data for testing"
                }
            ],
            '04': [
                {
                    "division": "04",
                    "material_type": "CMU Block Wall",
                    "description": "8 inch CMU block",
                    "bbox": {"x": 200, "y": 150, "width": 180, "height": 250},
                    "quantity": 450,
                    "unit": "SF",
                    "confidence": "medium",
                    "notes": "Mock data for testing"
                }
            ],
            '08': [
                {
                    "division": "08",
                    "material_type": "Hollow Metal Door",
                    "description": "3'-0\" x 7'-0\" hollow metal door",
                    "bbox": {"x": 250, "y": 300, "width": 50, "height": 80},
                    "quantity": 3,
                    "unit": "EA",
                    "confidence": "high",
                    "notes": "Mock data for testing"
                }
            ]
        }
        
        materials = []
        for div_id in selected_divisions:
            if div_id in mock_materials:
                materials.extend(mock_materials[div_id])
        
        return {
            "materials": materials,
            "legend_items": [],
            "schedules": [],
            "note": "MOCK DATA - Configure ANTHROPIC_API_KEY for real analysis"
        }
    
    def estimate_processing_time(self, num_pages: int) -> int:
        """
        Estimate processing time in seconds
        
        Args:
            num_pages: Number of pages to process
        
        Returns:
            Estimated seconds
        """
        # Assume ~10 seconds per page for AI analysis
        return num_pages * 10
    
    def validate_material_data(self, material: Dict) -> bool:
        """
        Validate material data structure
        
        Args:
            material: Material dictionary
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['division', 'material_type', 'quantity', 'unit']
        return all(field in material for field in required_fields)
