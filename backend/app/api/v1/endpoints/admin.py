"""Admin Endpoints for API Key Management (Redis Backed)."""
import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import generate_api_key, save_key_to_store, get_all_keys_from_store

router = APIRouter()


class CreateKeyRequest(BaseModel):
    name: str = Field(..., description="Key description / owner name")


class CreateKeyResponse(BaseModel):
    key_id: str
    name: str
    api_key: str
    message: str = "Save this API Key securely! It will NOT be shown again."


class KeyInfo(BaseModel):
    key_id: str
    name: str
    is_active: bool


@router.post("/keys", response_model=CreateKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_api_key(request: CreateKeyRequest):
    """Admin endpoint to issue a new API key."""
    raw_key, hashed_key = generate_api_key()
    key_id = str(uuid.uuid4())

    key_data = {
        "key_id": key_id,
        "name": request.name,
        "is_active": True,
    }
    save_key_to_store(hashed_key, key_data)

    return CreateKeyResponse(
        key_id=key_id,
        name=request.name,
        api_key=raw_key
    )


@router.get("/keys", response_model=List[KeyInfo])
async def list_api_keys():
    """Admin endpoint to list all registered keys."""
    keys_db = get_all_keys_from_store()
    keys = []
    for hashed, data in keys_db.items():
        keys.append(KeyInfo(key_id=data["key_id"], name=data["name"], is_active=data["is_active"]))
    return keys


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(key_id: str):
    """Admin endpoint to revoke an API key."""
    keys_db = get_all_keys_from_store()
    found = False
    for hashed, data in keys_db.items():
        if data["key_id"] == key_id:
            data["is_active"] = False
            save_key_to_store(hashed, data)
            found = True
            break

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key with ID '{key_id}' not found."
        )
    return None
