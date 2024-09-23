from enum import Enum
from pydantic import BaseModel, Field
from typing import Union
import torch
import outlines
from outlines import samplers
from outlines import generate
from outlines.integrations.utils import convert_json_schema_to_str
from outlines.fsm.json_schema import build_regex_from_schema


class Action(str, Enum):
    verify = "verify"


class Reason_and_Act(BaseModel):
    Scratchpad: str = Field(
        ...,
        description="Information from the Observation useful to answer the question",
    )
    Thought: str = Field(
        ...,
        description="It describes your thoughts about the question you have been asked",
    )
    Action: Action
    Action_Input: str = Field(..., description="The arguments of the Action.")


class Final_Answer(BaseModel):
    Final_Thought: str = Field(
        ...,
        description="It describes your final thoughts about the question you have been asked",
    )
    Final_Answer: str = Field(
        ..., description="Answer to the question grounded on the Observation"
    )


class Decision(BaseModel):
    Decision: Union[Reason_and_Act, Final_Answer]


class ReactChatBot:
    def __init__(self, dialect: str, db_schema: str, attempts: int = 5):
        self.attempts = attempts
        self.schema = Decision.model_json_schema()
        schema_str = convert_json_schema_to_str(json_schema=self.schema)
        self.react_regex_str = build_regex_from_schema(schema_str)
        # print(self.react_regex_str)

        self.react_prompt = generate_react_prompt(self.schema, dialect, db_schema)

        self.model = outlines.models.transformers(
            "mistralai/Mistral-7B-Instruct-v0.3",
            model_kwargs={"device_map": "auto", "torch_dtype": torch.bfloat16},
        )

    def __call__(self, user_prompt: str):
        return self.think(user_prompt)

    def think(self, user_prompt: str):
        full_prompt = generate_full_prompt(self.react_prompt, user_prompt)

        generator = generate.regex(self.model, self.react_regex_str, samplers.greedy())
        # generator = generate.regex(
        #     self.model, self.react_regex_str, samplers.multinomial()
        # )
        result = generator(full_prompt, max_tokens=4096)
        return result


@outlines.prompt
def generate_react_prompt(schema: str, dialect: str, db_schema: str):
    """
    <s>system
    You are a world class AI agent designed to interact with a SQL database to find a correct SQL query for the given question.
    Given an input question, generate a syntactically correct {{ dialect }} query.
    Here's the datbase schema you must interact with:
    <db_schema>
        {{ db_schema }}
    </db_schema></s>
    
    You always output a JSON with correct Pydantic schema. 
    Here's the json schema you must adhere to:
    <schema>
        {{ schema }}
    </schema>
    
    You run in a loop of Scratchpad, Thought, Action, Action Input, PAUSE, Observation. 
    At the end of the loop you output a Final Answer. It MUST be a valid {{ dialect }} query!
    Don't provide a final answer until you are sure you have a valid query.
    Use Scratchpad to store the information from the Observation useful to answer the question
    Use Thought to describe your thoughts about the question you have been asked \
        and reflect carefully about the Observation if it exists.
    Use Action to run one of the actions available to you.
    Use Action Input to input the arguments of the selected action - then return PAUSE.
    Observation will be the result of running those actions.
    Your available actions are:
        verify:
            e.g. Verify a SQL query: "SELECT * FROM table;"
            Verify a {{ dialect }} query for and returns a boolean and a string
                - If the query is valid -> True, ""
                - If the quer is invalid -> False, "error message"            
    The SQL query MUST have in-line comments to explain what each clause does.
    Some tips to always keep in mind:
    tip1) If the SQL query resulted in errors or not correct results, rewrite the SQL query and try again.
    tip2) You should always execute the SQL query by calling the verify action to make sure the results are correct.
    DO NOT TRY TO GUESS THE ANSWER.
    """


@outlines.prompt
def generate_user_prompt(question: str):
    """
    <s>user
    {{ question }}</s>

    <s>assistant
    """


@outlines.prompt
def extend_user_prompt(
    prev_user_prompt: str,
    scratchpad: str,
    thought: str,
    action: str,
    action_input: str,
    observation: str,
):
    """
    {{ prev_user_prompt }}

    Scratchpad:
        {{ scratchpad }}
    Thought:
        {{ thought }}
    Action:
        {{ action }}
    Action Input:
        {{ action_input }}
    Observation:
        {{ observation }}
    """


@outlines.prompt
def generate_full_prompt(react_prompt: str, user_prompt: str):
    """
    {{ react_prompt }}

    {{ user_prompt }}
    """
