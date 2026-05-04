import logging
from openai import OpenAI

# import core
from app.core.config import get_settings

# import models
from app.models.chat import ChatResponse

settings = get_settings()

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def get_structured_response(prompt: str) -> ChatResponse:
    logging.info("Prompt: %s", prompt)
    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a mock response generator for a CAE assistant UI. "
                    "Return ONLY valid JSON, no markdown or prose. "
                    "Output must be an object with: "
                    '"parts" (array of blocks with "type" and "data") and '
                    '"suggestions" (array of blocks with "title" and "description"). '
                    'Allowed types: ["text","table","list","image","video","chart","html","wcax"]. '
                    '"table" data: {"headers":[...],"rows":[...]}; '
                    '"list" data: array of strings; '
                    '"image"/"video"/"html"/"wcax" data: a URL string; '
                    '"chart" data: {"type":"line|bar|pie","data":{"labels":[...],"datasets":[...]}}; '
                    '"text" data: a string. '
                    "Return at least 1 part; more parts are allowed. "
                    '"title" and "description" fields in "suggestions" are string.'
                    "If the request is unclear or data is unknown, return plausible mock data in the same format."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=ChatResponse,
    )
    return response.output_parsed
