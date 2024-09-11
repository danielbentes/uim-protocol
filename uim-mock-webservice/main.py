import json
import os
from pydantic import BaseModel, Field
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from fastapi.security import APIKeyHeader

# Load environment variables
load_dotenv()

class SearchRequest(BaseModel):
    location: str
    min_price: int = None
    max_price: int = None
    property_type: str = None

class SearchResponse(BaseModel):
    properties: list
    total_results: int

class DetailsRequest(BaseModel):
    property_id: str

class DetailsResponse(BaseModel):
    property_details: dict

class PolicyAgreementRequest(BaseModel):
    agent_id: str = Field(..., description="The unique identifier of the agent")
    signed_policy: str = Field(..., min_length=1, description="The signed policy document")
    signature: str = Field(..., min_length=1, description="The signature of the policy document")

class ExecuteRequest(BaseModel):
    intent_uid: str = Field(..., description="The unique identifier of the intent")
    parameters: Dict[str, Any] = Field(..., description="The parameters for the intent")


app = FastAPI()

UIM_SERVICE_PUBLIC_KEY = os.getenv("UIM_SERVICE_PUBLIC_KEY")
UIM_SERVICE_PRIVATE_KEY = os.getenv("UIM_SERVICE_PRIVATE_KEY")
UIM_SERVICE_LICENSE = os.getenv("UIM_SERVICE_LICENSE")

@app.get("/agents.json")
async def get_agents_json(request: Request):
    agents_json = create_agents_json(request)
    return JSONResponse(content=agents_json)

def create_agents_json(request: Request):
    base_url = f"{request.url.scheme}://{request.client.host}:{request.url.port}"
    return {
        "service-info": {
            "name": "fakerealestate.com",
            "description": "A fictional service providing property listings and real estate data.",
            "service_url": f"{base_url}",
            "service_logo_url": f"{base_url}/logo.png",
            "service_terms_of_service_url": f"{base_url}/terms",
            "service_privacy_policy_url": f"{base_url}/privacy"
        },
        "intents": [
            {
                "intent_uid": "fakerealestate.com:searchProperty:v1",
                "intent_name": "SearchProperty",
                "description": "Searches properties based on location, price range, and property type.",
                "input_parameters": SearchRequest.model_json_schema()["properties"],
                "output_parameters": SearchResponse.model_json_schema()["properties"],
                "tags": ["real estate", "search", "property"],
                "rate_limit": "1000/hour",
                "price": "0.00 USD"
            },
            {
                "intent_uid": "fakerealestate.com:getPropertyDetails:v1",
                "intent_name": "GetPropertyDetails",
                "description": "Fetches detailed information for a specific property based on property ID.",
                "input_parameters": DetailsRequest.model_json_schema()["properties"],
                "output_parameters": DetailsResponse.model_json_schema()["properties"],
                "tags": ["real estate", "details", "property"],
                "rate_limit": "1000/hour",
                "price": "0.01 USD"
            }
        ],
        "uim-public-key": UIM_SERVICE_PUBLIC_KEY,
        "uim-policy-file": f"{base_url}/uim-policy.json",
        "uim-api-discovery": f"{base_url}/uim/intents/search",
        "uim-api-execute": f"{base_url}/uim/execute",
        "uim-compliance": {
            "standards": ["ISO27001", "GDPR"],
            "regional-compliance": {
                "EU": "GDPR",
                "US-CA": "CCPA"
            },
            "notes": "Data is encrypted in transit and at rest."
        },
        "uim-license": UIM_SERVICE_LICENSE
    }

@app.get("/uim-policy.json")
async def get_policy_json(request: Request):
    policy_json = create_policy_json(request)
    return JSONResponse(content=policy_json)

def create_policy_json(request: Request):
    base_url = f"{request.url.scheme}://{request.client.host}:{request.url.port}"
    
    return {
        "@context": "http://www.w3.org/ns/odrl.jsonld",
        "@type": "odrl:Set",
        "@id": f"{base_url}/uim-policy",
        "profile": "http://www.w3.org/ns/odrl/2/core",
        "permission": [
            {
            "target": f"{base_url}/uim/execute/SearchProperty",
            "action": {
                "id": "odrl:execute",
                "refinement": [
                {
                    "leftOperand": "odrl:count",
                    "operator": "odrl:lteq",
                    "rightOperand": 1000,
                    "unit": "odrl:hour"
                }
                ]
            }
            },
            {
            "target": f"{base_url}/uim/execute/GetPropertyDetails",
            "action": {
                "id": "odrl:execute",
                "refinement": [
                {
                    "leftOperand": "odrl:count",
                    "operator": "odrl:lteq",
                    "rightOperand": 1000,
                    "unit": "odrl:hour"
                }
                ]
            },
            "duty": [
                {
                "action": [
                    {
                        "rdf:value": { "@id": "odrl:compensate" },
                        "refinement": [{
                            "leftOperand": "payAmount",
                            "operator": "eq",
                            "rightOperand": { "@value": "0.01", "@type": "xsd:decimal" },
                            "unit": "http://dbpedia.org/resource/Euro"
                        }]
                    }
                ]
                }
            ]
            }
        ],
        "prohibition": [
            {
            "target": [
                f"{base_url}/uim/execute/SearchProperty",
                f"{base_url}/uim/execute/GetPropertyDetails"
            ],
            "action": {
                "id": "odrl:execute",
                "refinement": [
                {
                    "leftOperand": "odrl:count",
                    "operator": "odrl:gt",
                    "rightOperand": 1000,
                    "unit": "odrl:hour"
                }
                ]
            }
            }
        ],
        "party": [
            {
            "function": "odrl:assigner",
            "identifier": f"{base_url}/assigner"
            },
            {
            "function": "odrl:assignee",
            "identifier": f"{base_url}/assignee"
            }
        ],
        "asset": [
            {
            "id": f"{base_url}/uim/execute/SearchProperty",
            "type": "odrl:Asset"
            },
            {
            "id": f"{base_url}/uim/execute/GetPropertyDetails",
            "type": "odrl:Asset"
            }
        ]
    }

def verify_signed_policy(signed_policy: str, public_key):
    try:
        # Assuming the signed_policy is a JSON string with 'policy' and 'signature' fields
        signed_policy_data = json.loads(signed_policy)
        policy = signed_policy_data['policy']
        signature = signed_policy_data['signature']
        
        public_key.verify(
            signature.encode(),
            policy.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"Verification failed: {e}")
        return False

from fastapi import Depends

def verify_pat(request: Request):
    token = request.headers.get("uim-pat")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Decode the token without verification to extract the payload
        decoded_pat = jwt.decode(token, options={"verify_signature": False})
        
        # Verify the token's signature
        jwt.decode(
            token,
            UIM_SERVICE_PUBLIC_KEY,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        
        # Check if the PAT is expired
        if datetime.fromisoformat(decoded_pat["valid_to"]) < datetime.now(timezone.utc):
            raise HTTPException(status_code=403, detail="PAT expired.")
        
        # Additional checks can be added here, such as permissions and obligations
        
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid PAT.")
    
    return decoded_pat

@app.post("/pat/issue")
async def issue_pat(request: PolicyAgreementRequest):
    # Mock verification of agreement and signature
    if not request.signed_policy:
        raise HTTPException(status_code=400, detail="Invalid policy agreement.")
    # Verify the signed policy
    if not verify_signed_policy(request.signed_policy, UIM_SERVICE_PUBLIC_KEY):
        raise HTTPException(status_code=400, detail="Policy verification failed.")
    
    # Generate and sign a PAT (using JWT for example)
    pat = {
        "uid": "pat-12345",
        "issued_to": "ai-agent-1",
        "permissions": ["execute:intent/searchProperty"],
        "valid_from": datetime.now(timezone.utc).isoformat(),
        "valid_to": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    }
    token = jwt.encode(pat, UIM_SERVICE_PRIVATE_KEY, algorithm="HS256")
    return {"uim-pat": token}

# Define the security scheme
security_scheme = APIKeyHeader(name="uim-pat", scheme_name="Policy Adherence Token (PAT) token scheme", description="The PAT encapsulates the agreed policies, permissions, and obligations in a digitally signed token", auto_error=False)

@app.post("/api/execute", dependencies=[Depends(security_scheme)])
async def execute_intent(request: ExecuteRequest, pat: dict = Depends(verify_pat)):
    intent_uid = request.intent_uid
    parameters = request.parameters

    if intent_uid == "fakerealestate.com:searchProperty:v1":
        location = parameters.get('location')
        min_price = parameters.get('min_price')
        max_price = parameters.get('max_price')
        property_type = parameters.get('property_type')

        # Simulate a search operation
        if location == "New York" and property_type == "apartment":
            response = {
                "total_results": 1,
                "properties": [
                    {
                        "property_id": "123",
                        "name": "Luxury Apartment",
                        "price": 2000,
                        "location": "New York",
                        "property_type": "apartment"
                    }
                ]
            }
        else:
            response = {
                "total_results": 0,
                "properties": []
            }
    elif intent_uid == "fakerealestate.com:getPropertyDetails:v1":
        property_id = parameters.get('property_id')

        # Simulate fetching property details
        if property_id == "123":
            response = {
                "property_details": {
                    "property_id": "123",
                    "name": "Luxury Apartment",
                    "price": 2000,
                    "location": "New York",
                    "property_type": "apartment",
                    "description": "A luxurious apartment in the heart of New York."
                }
            }
        else:
            response = {
                "property_details": {}
            }
    else:
        raise HTTPException(status_code=400, detail="Unknown intent_uid")

    return JSONResponse(content=response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)