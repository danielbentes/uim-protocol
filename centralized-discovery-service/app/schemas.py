# app/schemas.py

from pydantic import BaseModel
from typing import List, Optional

class InputParameter(BaseModel):
    name: str
    type: str
    required: bool
    description: Optional[str]

class OutputParameter(BaseModel):
    name: str
    type: str
    description: Optional[str]

class Intent(BaseModel):
    intent_uid: str
    intent_name: str
    description: str
    input_parameters: List[InputParameter]
    output_parameters: List[OutputParameter]
    endpoint: str
    tags: Optional[List[str]]

class ServiceInfo(BaseModel):
    name: str
    description: str
    service_url: str
    service_logo_url: Optional[str]
    service_terms_of_service_url: Optional[str]
    service_privacy_policy_url: Optional[str]

class AgentsJson(BaseModel):
    service_info: ServiceInfo
    intents: List[Intent]