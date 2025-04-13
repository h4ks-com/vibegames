from typing import Literal

import mistletoe
import requests
from mistletoe.block_token import CodeFence
from pydantic import BaseModel

from app.settings import settings

RoleType = Literal["user", "assistant"]


class Message(BaseModel):
    role: RoleType
    content: str


def get_completion(messages: list[Message]) -> str:
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }

    json_data = {
        "messages": [message.model_dump() for message in messages],
    }

    response = requests.post(f"{settings.GPT4F_API_URL}/api/completions", headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()["completion"]


class SourceFile(BaseModel):
    name: str
    content: str


class Context(BaseModel):
    messages: list[Message] = []


class Project(BaseModel):
    context: Context = Context()
    files: list[SourceFile] = []

    def prompt(self, content: str) -> str:
        self.context.messages.append(Message(role="user", content=content))
        ai_response = get_completion(self.context.messages)
        self.context.messages.append(Message(role="assistant", content=ai_response))
        return ai_response

    def prompt_without_tracking(self, content: str) -> str:
        context = self.context.model_copy(deep=True)
        context.messages.append(Message(role="user", content=content))
        return get_completion(context.messages)

    def add_file(self, name: str, content: str) -> None:
        self.files.append(SourceFile(name=name, content=content))


def extract_code_blocks(markdown: str) -> str:
    document = mistletoe.Document(markdown)
    code = None
    if document.children:
        for child in document.children:
            if isinstance(child, CodeFence):
                code = child.content
                break

    if code is None:
        raise ValueError("No code block found in the response.")
    return code


def create_project(prompt: str) -> Project:
    project = Project()
    response = project.prompt(
        f"{prompt}\nMake sure everything is in a single HTML file with embedded CSS and JS in a single code block to be"
        " used as a web app."
    )
    code = extract_code_blocks(response)
    project.add_file("index.html", code)
    return project


def edit_project(
    messages: list[Message],
    prompt: str,
) -> Project:
    project = Project(context=Context(messages=messages))
    response = project.prompt(
        f"{prompt}\nMake sure everything is kept in a single HTML file with embedded CSS and JS in a single code block to be"
        " used as a web app."
    )
    code = extract_code_blocks(response)
    project.add_file("index.html", code)
    return project
