from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from pydantic import BaseModel


class LLMModel(ABC):
    @abstractmethod
    def __init__(self, api_key: str):
        raise NotImplementedError()

    @abstractmethod
    async def create(
        self,
        system_prompt: str,
        user_prompt: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        frequency_penalty: float,
        presence_penalty: float,
    ):
        raise NotImplementedError()

    @abstractmethod
    async def parse(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: BaseModel,
        model_name: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        frequency_penalty: float,
        presence_penalty: float,
    ):
        raise NotImplementedError()


class OpenAIModel(LLMModel):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def create(
        self,
        system_prompt: str,
        user_prompt: str,
        model_name: str = "gpt-4o-mini",
        temperature: float = 1,
        max_tokens: int = 3000,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> str:
        system_message = {"role": "system", "content": system_prompt}
        user_message = {"role": "user", "content": user_prompt}
        return (
            await self.client.chat.completions.create(
                model=model_name,
                messages=[system_message, user_message],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
            .choices[0]
            .message.content
        )

    async def parse(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: BaseModel,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0,
        max_tokens: int = 4000,
        top_p: float = 0.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> BaseModel:
        system_message = {"role": "system", "content": system_prompt}
        user_message = {"role": "user", "content": user_prompt}
        response = await self.client.beta.chat.completions.parse(
            model=model_name,
            messages=[system_message, user_message],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            response_format=response_format,
        )
        return response.choices[0].message.parsed
