#
#  Copyright 2025 AI Edge Eliza
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
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
        """Generate Manim script from prompt with voiceover and validation"""
        try:
            logger.debug(f"Building enhanced prompt for script generation...")
            enhanced_prompt = self._build_prompt(prompt, duration_limit)
            logger.debug(f"Enhanced prompt length: {len(enhanced_prompt)} chars")

            logger.info(f"🤖 Calling Gemini API (model: gemini-2.5-pro) - Step 1/3: Generate base script...")
            loop = asyncio.get_event_loop()

            import time
            start_time = time.time()

            # First API call - generate base script
            try:
                script_content = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._call_gemini_api,
                        enhanced_prompt
                    ),
                    timeout=240.0
                )
            except asyncio.TimeoutError:
                logger.error("API call timed out after 2 minutes")
                raise ScriptGenerationError("API call timed out")

            api_duration = time.time() - start_time
            logger.info(f"✅ Gemini API Step 1 responded in {api_duration:.2f}s")

            # Extract and clean the script
            cleaned_script = self._clean_script(script_content)

            # Second API call - validate and fix the script
            logger.info(f"🔍 Step 2/3: Validating script with second Gemini call...")
            start_time = time.time()

            try:
                validated_script = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._validate_and_fix_script,
                        cleaned_script
                    ),
                    timeout=240.0
                )
            except asyncio.TimeoutError:
                logger.warning("Validation call timed out, using original script")
                validated_script = cleaned_script

            validation_duration = time.time() - start_time
            logger.info(f"✅ Script validation completed in {validation_duration:.2f}s")

            # Third API call - add voiceover functionality
            logger.info(f"🎙️ Step 3/3: Adding voiceover with third Gemini call...")
            start_time = time.time()

            try:
                voiceover_script = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._add_voiceover_functionality,
                        validated_script,
                        prompt
                    ),
                    timeout=240.0
                )
            except asyncio.TimeoutError:
                logger.warning("Voiceover call timed out, using validated script without voiceover")
                voiceover_script = validated_script

            voiceover_duration = time.time() - start_time
            logger.info(f"✅ Voiceover integration completed in {voiceover_duration:.2f}s")

            return voiceover_script

        except Exception as e:
            logger.error(f"❌ Script generation failed: {e}")
            logger.exception(f"Full script generation traceback:")
            raise ScriptGenerationError(
                "Failed to generate Manim script",
                details=str(e)
            )

    def _add_voiceover_functionality(self, script_content: str, original_prompt: str) -> str:
        """Third Gemini call to add voiceover functionality to the existing script"""
        voiceover_prompt = f"""
Transform this Manim script to use voiceover functionality. The original educational topic was: "{original_prompt}"

CRITICAL REQUIREMENTS FOR VOICEOVER INTEGRATION:
1. Change the class to inherit from VoiceoverScene instead of Scene
2. Import: from manim_voiceover import VoiceoverScene
3. Import: from manim_voiceover.services.azure import AzureService
4. Add speech service initialization in construct method:
   self.set_speech_service(AzureService(voice="en-US-JennyNeural", style="friendly"))
5. Wrap animation sequences with voiceover context managers
6. Use this pattern: with self.voiceover(text="Narration text here") as tracker:
7. Sync animations with voiceover duration using tracker.duration
8. Write natural, educational narration that explains what's happening
9. Keep the same visual content and animations, just add voiceover

VOICEOVER PATTERNS TO USE:
- with self.voiceover(text="Introduction text") as tracker:
    self.play(Write(title), run_time=tracker.duration)

- with self.voiceover(text="Explanation text") as tracker:
    self.play(Create(shape), run_time=tracker.duration - 0.5)
    self.wait(0.5)

NARRATION GUIDELINES:
- Write clear, educational narration
- Explain concepts as they appear visually
- Use natural, conversational language
- Match narration length to animation duration
- Include brief pauses with self.wait() when needed

EXISTING SCRIPT TO TRANSFORM:
```python
{script_content}
```

Return ONLY the complete transformed Python code with voiceover integration, no explanations or markdown.
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=voiceover_prompt
            )

            voiceover_script = response.text
            # Clean the response in case it has markdown
            voiceover_script = re.sub(r'```python\s*\n', '', voiceover_script)
            voiceover_script = re.sub(r'```\s*$', '', voiceover_script, flags=re.MULTILINE)
            voiceover_script = voiceover_script.strip()

            # Validate that voiceover imports were added
            if 'VoiceoverScene' not in voiceover_script:
                logger.warning("Voiceover integration may have failed, VoiceoverScene not found")
                # Add imports if missing
                if 'from manim_voiceover' not in voiceover_script:
                    voiceover_script = self._add_voiceover_imports(voiceover_script)
                # Convert Scene to VoiceoverScene
                voiceover_script = re.sub(r'class\s+(\w+)\s*\(\s*Scene\s*\):', r'class \1(VoiceoverScene):',
                                          voiceover_script)

            logger.info(f"✅ Voiceover integration applied successfully")
            return voiceover_script

        except Exception as e:
            logger.warning(f"Voiceover integration failed: {e}, using original script")
            # If voiceover fails, try to add basic voiceover structure manually
            return self._add_basic_voiceover_structure(script_content)

    def _add_voiceover_imports(self, script_content: str) -> str:
        """Add necessary voiceover imports to the script"""
        # Find the existing imports section
        if 'from manim import *' in script_content:
            script_content = script_content.replace(
                'from manim import *',
                'from manim import *\nfrom manim_voiceover import VoiceoverScene\nfrom manim_voiceover.services.azure import AzureService'
            )
        else:
            # Add imports at the beginning
            script_content = 'from manim import *\nfrom manim_voiceover import VoiceoverScene\nfrom manim_voiceover.services.azure import AzureService\n\n' + script_content

        return script_content

    def _add_basic_voiceover_structure(self, script_content: str) -> str:
        """Add basic voiceover structure if AI integration fails"""
        # Add imports
        script_content = self._add_voiceover_imports(script_content)

        # Convert Scene to VoiceoverScene
        script_content = re.sub(r'class\s+(\w+)\s*\(\s*Scene\s*\):', r'class \1(VoiceoverScene):', script_content)

        # Add speech service initialization after construct method definition
        speech_service_init = '''        # Initialize speech service
        self.set_speech_service(
            AzureService(
                voice="en-US-JennyNeural",
                style="friendly"
            )
        )

'''

        # Find construct method and add speech service
        script_content = re.sub(
            r'(def construct\(self\):\s*\n)',
            r'\1' + speech_service_init,
            script_content
        )

        return script_content

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
- CRITICAL: Fix animation on groups - NEVER use Create(group), Write(group), or FadeIn(group)
- For groups use: self.play(*[Create(obj) for obj in group]) or animate each member individually
- Make sure all objects are properly defined before use
- Ensure proper indentation
- IMPORTANT: Fix vector normalization - use np.linalg.norm() instead of .normalize()
- Import numpy as np if needed for vector operations
- Complete any incomplete lines of code

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
        - Import numpy as np if you need vector operations
        - Create a class that inherits from Scene (voiceover will be added later)
        - NEVER use VGroup(*self.mobjects) - this causes errors
        - Instead use Group() or create specific groups of objects
        - Use VMobject types for grouping (Text, Circle, Rectangle, etc.)
        - Avoid mixing Mobject and VMobject types
        - Keep the animation between 10-{duration_limit} seconds
        - Make sure all imports are correct
        - End with self.wait(2) for a clean finish
        - Use Text() instead of MathTex for better compatibility
        - Use simple, reliable Manim objects

        VECTOR OPERATIONS:
        - NEVER use .normalize() on numpy arrays - this method doesn't exist
        - Use np.linalg.norm() for vector normalization: vector / np.linalg.norm(vector)
        - Example: normalized = (point_a - point_b) / np.linalg.norm(point_a - point_b)
        - Always complete your lines of code - don't leave hanging expressions

        SAFE OBJECT TYPES TO USE:
        - Text() for all text
        - Circle(), Rectangle(), Square() for shapes
        - Line(), Arrow() for connections
        - Group() for grouping objects (NOT VGroup(*self.mobjects))
        - NumberPlane(), Axes() for coordinate systems

        ANIMATION RULES:
        - Use Create() ONLY on individual objects (Circle, Rectangle, Line, Text, etc.)
        - NEVER use Create(group), Write(group), or FadeIn(group) - this causes "NotImplementedError"
        - For groups, animate each object separately: self.play(*[Create(obj) for obj in group])
        - Alternative for groups: self.play(Create(obj1), Create(obj2), Create(obj3))
        - For VGroups/Groups: Use AnimationGroup or animate individual members
        - Example: self.play(*[Write(obj) for obj in my_group]) instead of Write(my_group)

        SAFE COLORS TO USE (ONLY THESE):
        - RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, PINK
        - WHITE, BLACK, GRAY, GREY, LIGHT_GRAY, DARK_GRAY
        - TEAL, MAROON, GOLD
        - For custom colors use: "#FF5733" or "#3498DB" (hex format)

        NOTE: This script will later be enhanced with voiceover functionality, so focus on clear visual storytelling.

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

        # Fix Create() on groups - this is a major source of errors
        # Pattern: self.play(Create(group_variable))
        script_content = re.sub(
            r'self\.play\(Create\(([a-zA-Z_][a-zA-Z0-9_]*(?:_group|_objects|Group|VGroup)[^)]*)\)\)',
            r'self.play(*[Create(obj) for obj in \1])',
            script_content
        )

        # Also handle Write() on groups
        script_content = re.sub(
            r'self\.play\(Write\(([a-zA-Z_][a-zA-Z0-9_]*(?:_group|_objects|Group|VGroup)[^)]*)\)\)',
            r'self.play(*[Write(obj) for obj in \1])',
            script_content
        )

        # Fix FadeIn on groups
        script_content = re.sub(
            r'self\.play\(FadeIn\(([a-zA-Z_][a-zA-Z0-9_]*(?:_group|_objects|Group|VGroup)[^)]*)\)\)',
            r'self.play(*[FadeIn(obj) for obj in \1])',
            script_content
        )

        # Fix vector normalization issues
        # Replace .normalize() with proper numpy normalization
        script_content = re.sub(
            r'([a-zA-Z_][a-zA-Z0-9_]*(?:\s*[-+]\s*[a-zA-Z_][a-zA-Z0-9_]*)?)\.normalize\(\)',
            r'(\1 / np.linalg.norm(\1))',
            script_content
        )

        # Fix incomplete .normal patterns
        script_content = re.sub(
            r'([a-zA-Z_][a-zA-Z0-9_]*(?:\s*[-+]\s*[a-zA-Z_][a-zA-Z0-9_]*)?)\.normal(?!\w)',
            r'(\1 / np.linalg.norm(\1))',
            script_content
        )

        # Ensure numpy is imported if vector operations are used
        if 'np.linalg.norm' in script_content and 'import numpy as np' not in script_content:
            script_content = 'import numpy as np\n' + script_content

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

        # Add numpy import if needed
        if 'np.' in script_content and 'import numpy as np' not in script_content:
            script_content = script_content.replace('from manim import *', 'from manim import *\nimport numpy as np')

        # Ensure class definition exists
        if not re.search(r'class \w+\(Scene\):', script_content):
            # Wrap existing code in a basic class structure
            script_content = f"""from manim import *
import numpy as np

class GeneratedScene(Scene):
    def construct(self):
        # Generated content
{chr(10).join('        ' + line for line in script_content.split(chr(10)))}

        self.wait(2)
"""

        return script_content

    def get_fallback_script(self, prompt: str) -> str:
        """Generate a simple fallback script with voiceover if AI generation fails"""
        class_name = "FallbackScene"

        return f'''from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.azure import AzureService
import numpy as np

class {class_name}(VoiceoverScene):
    def construct(self):
        # Initialize speech service
        self.set_speech_service(
            AzureService(
                voice="en-US-JennyNeural",
                style="friendly"
            )
        )

        # Title with voiceover
        title = Text("Educational Video", font_size=48, color=BLUE)
        with self.voiceover(text="Welcome to this educational video presentation.") as tracker:
            self.play(Write(title), run_time=tracker.duration)

        # Topic with voiceover
        topic = Text("{prompt[:50]}...", font_size=32, color=WHITE)
        topic.next_to(title, DOWN, buff=1)
        with self.voiceover(text="Today we will explore: {prompt[:100]}") as tracker:
            self.play(Write(topic), run_time=tracker.duration)

        # Simple animation with voiceover
        circle = Circle(radius=1, color=YELLOW)
        circle.next_to(topic, DOWN, buff=1)
        with self.voiceover(text="Let me demonstrate this concept with a simple visual example.") as tracker:
            self.play(Create(circle), run_time=tracker.duration - 1)
            self.wait(1)

        with self.voiceover(text="Notice how the shape transforms to emphasize key points.") as tracker:
            self.play(circle.animate.scale(1.5), run_time=tracker.duration / 2)
            self.play(circle.animate.scale(0.8), run_time=tracker.duration / 2)

        # Conclusion with voiceover
        conclusion = Text("Thank you for watching!", font_size=24, color=GREEN)
        conclusion.next_to(circle, DOWN, buff=1)
        with self.voiceover(text="Thank you for watching this educational presentation!") as tracker:
            self.play(Write(conclusion), run_time=tracker.duration)

        # Final cleanup
        all_objects = Group(title, topic, circle, conclusion)
        self.play(FadeOut(all_objects))
        self.wait(2)
'''