from typing import Any, Dict, List
from pydantic import BaseModel, create_model
from openai import OpenAI
from texttools.base import BaseQuestionDetector

class LLMQuestionDetector(BaseQuestionDetector):
    """
    LLM-based detector using OpenAI's client.responses.parse
    for Structured Outputs (Pydantic models).
    """

    def __init__(
        self,
        client: OpenAI,
        *,
        model: str,
        temperature: float = 0.0,
        prompt_template: str = None,
        handlers: List[Any] = None,
        **client_kwargs: Any
    ):
        """
        :param client: an instantiated OpenAI client
        :param model: the model name (e.g. "gpt-4o-2024-08-06")
        :param temperature: sampling temperature
        :param prompt_template: override default prompt instructions
        :param handlers: optional list of result handlers
        :param client_kwargs: any other OpenAI kwargs (e.g. `max_tokens`, `top_p`, etc.)
        """
        super().__init__(handlers)
        self.client = client
        self.model = model
        self.temperature = temperature
        self.client_kwargs = client_kwargs

        self.prompt_template = prompt_template or (
            "You are a binary classifier. "
            "Answer only with `true` or `false` depending on the input."
        )

        self._OutputModel = create_model(
            "DetectionOutput",
            result=(bool, ...),  
        )

    def _build_messages(self, text: str) -> List[Dict[str, str]]:
        clean = self.preprocess(text)
        return [
            {"role": "system", "content": self.prompt_template},
            {"role": "user",   "content": clean},
        ]

    def detect(self, text: str) -> bool:
        msgs = self._build_messages(text)
        resp = self.client.responses.parse(
            model=self.model,
            input=msgs,
            text_format=self._OutputModel,
            temperature=self.temperature,
            **self.client_kwargs,
        )
        output: BaseModel = resp.output_parsed
        self._dispatch({"text": output.result})  
        return output.result
