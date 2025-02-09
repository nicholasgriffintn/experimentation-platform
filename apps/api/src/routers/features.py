from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import FeatureDefinition as DBFeatureDefinition
from ..db.session import get_db
from ..middleware.error_handler import ResourceNotFoundError, ValidationError

router = APIRouter()

class FeatureDefinition(BaseModel):
    name: str
    description: str
    data_type: str
    possible_values: List[Any]
    default_value: Any

    class Config:
        from_attributes = True

@router.post("/", response_model=FeatureDefinition)
async def create_feature(feature: FeatureDefinition, db: Session = Depends(get_db)):
    """
    Create a new feature definition.

    Creates a new feature that can be used in feature flag experiments.
    The feature definition includes possible values and default value.

    Args:
        feature (FeatureDefinition): The feature configuration
        db: Database session

    Returns:
        FeatureDefinition: The created feature definition

    Raises:
        ValidationError: If feature with same name already exists
    """
    db_feature = db.query(DBFeatureDefinition).filter(DBFeatureDefinition.name == feature.name).first()
    if db_feature:
        raise ValidationError(
            f"Feature {feature.name} already exists",
            details={"feature_name": feature.name}
        )
    
    db_feature = DBFeatureDefinition(
        name=feature.name,
        description=feature.description,
        data_type=feature.data_type,
        possible_values=feature.possible_values,
        default_value=feature.default_value
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
    Get a feature definition by name.

    Args:
        feature_name (str): The name of the feature
        db: Database session

    Returns:
        FeatureDefinition: The feature definition

    Raises:
        ResourceNotFoundError: If feature not found
    """
    feature = db.query(DBFeatureDefinition).filter(DBFeatureDefinition.name == feature_name).first()
    if not feature:
        raise ResourceNotFoundError("Feature", feature_name)
    return feature

@router.put("/{feature_name}", response_model=FeatureDefinition)
async def update_feature(
    feature_name: str,
    feature_update: FeatureDefinition,
    db: Session = Depends(get_db)
):
    """
    Update a feature definition.

    Args:
        feature_name (str): The name of the feature to update
        feature_update (FeatureDefinition): The update data
        db: Database session

    Returns:
        FeatureDefinition: The updated feature definition

    Raises:
        ResourceNotFoundError: If feature not found
    """
    feature = db.query(DBFeatureDefinition).filter(DBFeatureDefinition.name == feature_name).first()
    if not feature:
        raise ResourceNotFoundError("Feature", feature_name)
    
    for field, value in feature_update.dict(exclude_unset=True).items():
        setattr(feature, field, value)
    
    db.commit()
    db.refresh(feature)
    return feature

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