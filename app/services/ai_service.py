from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.analysis import ManuscriptAnalysisResult


# ==================================================
# GEMINI CLIENT
# ==================================================

client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


# ==================================================
# SYSTEM INSTRUCTION
# ==================================================

SYSTEM_INSTRUCTION = """
You are JournalPilot AI.

Analyze the supplied academic manuscript for
journal-submission readiness.

IMPORTANT:

- Use only information present in the manuscript.
- Do not invent facts.
- Do not invent citations.
- Do not invent statistics.
- Do not invent research results.
- If information is missing, mention it.
- Do not predict journal acceptance.
- Give concise, useful recommendations.

Evaluate:

1. Overall quality
2. Article type
3. Research area
4. Keywords
5. Structure
6. Abstract
7. Methodology
8. Results
9. Discussion
10. Language
11. Submission readiness
12. Critical issues
13. Improvement priorities

Scores must be integers from 0 to 100.

Keep every feedback field concise.
Keep recommendations concise.

Return ONLY valid JSON matching the
provided response schema.
"""


# ==================================================
# ANALYZE MANUSCRIPT
# ==================================================

def analyze_manuscript(
    manuscript_text: str,
) -> ManuscriptAnalysisResult:

    # ----------------------------------------------
    # Limit manuscript size for V1
    # ----------------------------------------------

    max_characters = 60000

    text = manuscript_text[:max_characters]


    # ----------------------------------------------
    # Prompt
    # ----------------------------------------------

    prompt = f"""
Analyze this academic manuscript.

Keep the analysis concise.

For each section:

- Give one score.
- Give concise feedback.
- Give 2 or 3 concise recommendations.

Keep the complete response within approximately
2500 output tokens.

MANUSCRIPT:

{text}
"""


    last_error = None


    # ----------------------------------------------
    # Retry 3 times
    # ----------------------------------------------

    for attempt in range(3):

        try:

            print(
                f"Gemini analysis attempt {attempt + 1}"
            )


            response = client.models.generate_content(

                model=settings.GEMINI_MODEL,

                contents=prompt,

                config=types.GenerateContentConfig(

                    system_instruction=(
                        SYSTEM_INSTRUCTION
                    ),

                    response_mime_type=(
                        "application/json"
                    ),

                    response_schema=(
                        ManuscriptAnalysisResult
                    ),

                    max_output_tokens=8000,
                ),
            )


            # --------------------------------------
            # Empty response
            # --------------------------------------

            if not response.text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )


            # --------------------------------------
            # Debug information
            # --------------------------------------

            print(
                "Gemini response length:",
                len(response.text),
            )


            print(
                "Gemini response:",
                response.text,
            )


            if response.candidates:

                print(
                    "Finish reason:",
                    response.candidates[0].finish_reason,
                )


            # --------------------------------------
            # Validate JSON
            # --------------------------------------

            result = (
                ManuscriptAnalysisResult
                .model_validate_json(
                    response.text
                )
            )


            print(
                "Gemini analysis completed successfully."
            )


            return result


        except Exception as error:

            last_error = error


            print(
                f"Gemini attempt {attempt + 1} failed:",
                repr(error),
            )


            if attempt < 2:

                import time

                time.sleep(2)


    # ----------------------------------------------
    # All attempts failed
    # ----------------------------------------------

    raise RuntimeError(
        f"Gemini analysis failed: {last_error}"
    )