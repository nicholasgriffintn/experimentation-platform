from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Any
from pydantic import BaseModel

from ..db.session import get_db
from ..models.database import FeatureDefinition as DBFeatureDefinition

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
    """Create a new feature definition"""
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
    """List all feature definitions"""
    return db.query(DBFeatureDefinition).all()

@router.get("/{feature_name}", response_model=FeatureDefinition)
async def get_feature(feature_name: str, db: Session = Depends(get_db)):
    """Get a specific feature by name"""
    db_feature = db.query(DBFeatureDefinition).filter(DBFeatureDefinition.name == feature_name).first()
    if not db_feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_name} not found"
        )
    return db_feature

@router.delete("/{feature_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(feature_name: str, db: Session = Depends(get_db)):
    """Delete a feature"""
    db_feature = db.query(DBFeatureDefinition).filter(DBFeatureDefinition.name == feature_name).first()
    if not db_feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature {feature_name} not found"
        )
    db.delete(db_feature)
    db.commit()
    return None 