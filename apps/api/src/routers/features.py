from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Any
from pydantic import BaseModel

from ..db.session import get_db
from ..db.base import FeatureDefinition as DBFeatureDefinition

router = APIRouter()

class FeatureDefinition(BaseModel):
    name: str
    description: str
    data_type: str
    possible_values: List[Any]

    class Config:
        from_attributes = True

@router.post("/", response_model=FeatureDefinition)
async def create_feature(feature: FeatureDefinition, db: Session = Depends(get_db)):
    """
    Create a new feature definition.

    Creates a new feature that can be used in experiments. The feature definition includes:
    - Name and description
    - Data type of the feature
    - Possible values the feature can take

    This is used to define what features can be experimented with and what values they can have.

    Args:
        feature (FeatureDefinition): The feature configuration
        db: Database session

    Returns:
        FeatureDefinition: The created feature definition

    Raises:
        HTTPException: 400 if feature with same name already exists
    """
    db_feature = db.query(DBFeatureDefinition).filter(DBFeatureDefinition.name == feature.name).first()
    if db_feature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feature {feature.name} already exists"
        )
    
    db_feature = DBFeatureDefinition(
        name=feature.name,
        description=feature.description,
        data_type=feature.data_type,
        possible_values=feature.possible_values
    )
    db.add(db_feature)
    db.commit()
    db.refresh(db_feature)
    return db_feature

@router.get("/", response_model=List[FeatureDefinition])
async def list_features(db: Session = Depends(get_db)):
    """
    List all feature definitions.

    Returns a list of all available features that can be used in experiments.
    Each feature includes its configuration and possible values.

    Returns:
        List[FeatureDefinition]: List of all feature definitions
    """
    return db.query(DBFeatureDefinition).all()

@router.get("/{feature_name}", response_model=FeatureDefinition)
async def get_feature(feature_name: str, db: Session = Depends(get_db)):
    """
    Get a specific feature definition by name.

    Retrieves detailed information about a single feature definition.

    Args:
        feature_name (str): The name of the feature to retrieve
        db: Database session

    Returns:
        FeatureDefinition: The requested feature definition

    Raises:
        HTTPException: 404 if feature not found
    """
    db_feature = db.query(DBFeatureDefinition).filter(DBFeatureDefinition.name == feature_name).first()
    if not db_feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_name} not found"
        )
    return db_feature

@router.delete("/{feature_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(feature_name: str, db: Session = Depends(get_db)):
    """
    Delete a feature definition.

    Permanently removes a feature definition. Note that this will not affect historical
    data for experiments that used this feature.

    Args:
        feature_name (str): The name of the feature to delete
        db: Database session

    Returns:
        None

    Raises:
        HTTPException: 404 if feature not found
    """
    db_feature = db.query(DBFeatureDefinition).filter(DBFeatureDefinition.name == feature_name).first()
    if not db_feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_name} not found"
        )
    db.delete(db_feature)
    db.commit()
    return None 