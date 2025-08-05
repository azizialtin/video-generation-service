import os
from google import genai
from app.core.config import settings
from app.core.exceptions import ScriptGenerationError
import re
import logging
import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)


class ScriptGenerator:
    def __init__(self):
        # Initialize Gemini client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    async def generate_script(self, prompt: str, duration_limit: int = 30) -> str:
        """Generate Manim script from prompt with validation"""
        try:
            logger.debug(f"Building enhanced prompt for script generation...")
            enhanced_prompt = self._build_prompt(prompt, duration_limit)
            logger.debug(f"Enhanced prompt length: {len(enhanced_prompt)} chars")

            logger.info(f"🤖 Calling Gemini API (model: gemini-2.5-pro)...")
            loop = asyncio.get_event_loop()

            import time
            start_time = time.time()

            # First API call - generate script
            try:
                script_content = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._call_gemini_api,
                        enhanced_prompt
                    ),
                    timeout=120.0
                )
            except asyncio.TimeoutError:
                logger.error("API call timed out after 2 minutes")
                raise ScriptGenerationError("API call timed out")

            api_duration = time.time() - start_time
            logger.info(f"✅ Gemini API responded in {api_duration:.2f}s")

            # Extract and clean the script
            cleaned_script = self._clean_script(script_content)

            # Second API call - validate and fix the script
            logger.info(f"🔍 Validating script with second Gemini call...")
            start_time = time.time()

            try:
                validated_script = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._validate_and_fix_script,
                        cleaned_script
                    ),
                    timeout=120.0
                )
            except asyncio.TimeoutError:
                logger.warning("Validation call timed out, using original script")
                validated_script = cleaned_script

            validation_duration = time.time() - start_time
            logger.info(f"✅ Script validation completed in {validation_duration:.2f}s")

            return validated_script

        except Exception as e:
            logger.error(f"❌ Script generation failed: {e}")
            logger.exception(f"Full script generation traceback:")
            raise ScriptGenerationError(
                "Failed to generate Manim script",
                details=str(e)
            )

    def _validate_and_fix_script(self, script_content: str) -> str:
        """Second Gemini call to validate and fix the script"""
        validation_prompt = f"""
Review this Manim script and fix any issues to make it executable. Return ONLY the corrected Python code.

CRITICAL FIXES NEEDED:
- Ensure all imports are correct (from manim import *)
- Fix any syntax errors
- Make sure the class inherits from Scene properly
- Fix any undefined variables or functions
- Ensure all colors used are valid Manim colors
- Fix any animation issues (no Create() or Write() on groups)
- Make sure all objects are properly defined before use
- Ensure proper indentation

SCRIPT TO FIX:
```python
{script_content}
```

Return ONLY the fixed Python code, no explanations or markdown.
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=validation_prompt
            )

            fixed_script = response.text
            # Clean the response in case it has markdown
            fixed_script = re.sub(r'```python\s*\n', '', fixed_script)
            fixed_script = re.sub(r'```\s*$', '', fixed_script, flags=re.MULTILINE)
            fixed_script = fixed_script.strip()

            logger.info(f"✅ Script validation and fixes applied")
            return fixed_script

        except Exception as e:
            logger.warning(f"Script validation failed: {e}, using original script")
            return script_content

    def _call_gemini_api(self, enhanced_prompt: str):
        """Synchronous method to call Gemini API - runs in thread executor"""
        logger.debug(f"[Thread] Making synchronous API call to Gemini...")
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=enhanced_prompt
            )
            logger.debug(f"[Thread] API call successful, response received")
            return response.text
        except Exception as e:
            logger.error(f"[Thread] API call failed: {e}")
            raise

    def _build_prompt(self, prompt: str, duration_limit: int) -> str:
        """Build enhanced prompt for script generation"""
        return f"""
        Create a complete Manim script that explains: {prompt}

        CRITICAL REQUIREMENTS:
        - Use the latest Manim syntax (from manim import *)
        - Create a class that inherits from Scene
        - NEVER use VGroup(*self.mobjects) - this causes errors
        - Instead use Group() or create specific groups of objects
        - Use VMobject types for grouping (Text, Circle, Rectangle, etc.)
        - Avoid mixing Mobject and VMobject types
        - Keep the animation between 10-{duration_limit} seconds
        - Make sure all imports are correct
        - End with self.wait(2) for a clean finish
        - Use Text() instead of MathTex for better compatibility
        - Use simple, reliable Manim objects

        SAFE OBJECT TYPES TO USE:
        - Text() for all text
        - Circle(), Rectangle(), Square() for shapes
        - Line(), Arrow() for connections
        - Group() for grouping objects (NOT VGroup(*self.mobjects))
        - NumberPlane(), Axes() for coordinate systems

        ANIMATION RULES:
        - Use Create() ONLY on individual objects (Circle, Rectangle, Line, Text, etc.)
        - For groups, animate each object separately: Write(obj1), Write(obj2), etc.
        - NEVER use Create(group) or Write(group) - animate group members individually
        - Use FadeIn() or Write() for multiple objects: Write(text1), Write(text2)
        - For groups: self.play(Write(obj1), Write(obj2), Write(obj3))

        SAFE COLORS TO USE (ONLY THESE):
        - RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, PINK
        - WHITE, BLACK, GRAY, GREY, LIGHT_GRAY, DARK_GRAY
        - TEAL, MAROON, GOLD
        - For custom colors use: "#FF5733" or "#3498DB" (hex format)

        Return ONLY the Python code without explanations or markdown formatting.
        """

    def _clean_script(self, script_content: str) -> str:
        """Clean and validate the generated script"""
        logger.debug(f"Input script content (first 500 chars): {script_content[:500]}")

        # Remove markdown code blocks
        script_content = re.sub(r'```python\s*\n', '', script_content)
        script_content = re.sub(r'```\s*$', '', script_content, flags=re.MULTILINE)

        # Remove any leading/trailing whitespace
        script_content = script_content.strip()

        # Fix common issues
        script_content = self._fix_common_issues(script_content)

        # Validate basic structure
        if not self._validate_script_structure(script_content):
            logger.warning("Script structure validation failed, applying additional fixes")
            script_content = self._apply_structure_fixes(script_content)

        logger.debug(f"Cleaned script content (first 500 chars): {script_content[:500]}")
        return script_content

    def _fix_common_issues(self, script_content: str) -> str:
        """Fix common issues that cause Manim errors"""
        # Replace problematic VGroup(*self.mobjects) pattern
        script_content = re.sub(
            r'VGroup\(\*self\.mobjects\)',
            'Group(*[mob for mob in self.mobjects if hasattr(mob, "animate")])',
            script_content
        )

        # Replace any other self.mobjects usage in VGroup
        script_content = re.sub(
            r'VGroup\([^)]*self\.mobjects[^)]*\)',
            'Group()',
            script_content
        )

        # Fix undefined color names
        color_replacements = {
            'BROWN': '"#8B4513"',
            'CYAN': 'TEAL',
            'LIME': 'GREEN',
            'NAVY': 'BLUE',
            'SILVER': 'LIGHT_GRAY',
            'OLIVE': 'YELLOW',
            'AQUA': 'TEAL',
            'FUCHSIA': 'PINK',
        }

        for invalid_color, replacement in color_replacements.items():
            script_content = re.sub(
                f'color={invalid_color}\\b',
                f'color={replacement}',
                script_content
            )

        return script_content

    def _validate_script_structure(self, script_content: str) -> bool:
        """Validate basic script structure"""
        required_patterns = [
            r'from manim import \*',
            r'class \w+\(Scene\):',
            r'def construct\(self\):',
        ]

        for pattern in required_patterns:
            if not re.search(pattern, script_content):
                logger.warning(f"Missing required pattern: {pattern}")
                return False

        return True

    def _apply_structure_fixes(self, script_content: str) -> str:
        """Apply fixes for basic script structure issues"""
        # Ensure proper imports
        if not re.search(r'from manim import \*', script_content):
            script_content = 'from manim import *\n\n' + script_content

        # Ensure class definition exists
        if not re.search(r'class \w+\(Scene\):', script_content):
            # Wrap existing code in a basic class structure
            script_content = f"""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Generated content
{chr(10).join('        ' + line for line in script_content.split(chr(10)))}

        self.wait(2)
"""

        return script_content

    def get_fallback_script(self, prompt: str) -> str:
        """Generate a simple fallback script if AI generation fails"""
        class_name = "FallbackScene"

        return f'''from manim import *

class {class_name}(Scene):
    def construct(self):
        # Title
        title = Text("Educational Video", font_size=48, color=BLUE)
        self.play(Write(title))
        self.wait(1)

        # Topic
        topic = Text("{prompt[:50]}...", font_size=32, color=WHITE)
        topic.next_to(title, DOWN, buff=1)
        self.play(Write(topic))
        self.wait(1)

        # Simple animation
        circle = Circle(radius=1, color=YELLOW)
        circle.next_to(topic, DOWN, buff=1)
        self.play(Create(circle))
        self.play(circle.animate.scale(1.5))
        self.play(circle.animate.scale(0.8))

        # Create a group for cleanup
        all_objects = Group(title, topic, circle)

        # Conclusion
        conclusion = Text("Thank you for watching!", font_size=24, color=GREEN)
        conclusion.next_to(circle, DOWN, buff=1)
        self.play(Write(conclusion))

        # Add conclusion to group
        all_objects.add(conclusion)

        # Safe cleanup
        self.play(FadeOut(all_objects))
        self.wait(2)
'''