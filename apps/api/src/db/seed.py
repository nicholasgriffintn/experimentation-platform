from sqlalchemy.orm import Session
from .base import FeatureDefinition

def seed_default_feature_values(db: Session):
    """Seed default feature values for boolean feature flags."""
    
    boolean_feature = FeatureDefinition(
        name="enabled",
        description="Standard boolean feature flag for enabling/disabling features",
        data_type="boolean",
        possible_values=[True, False]
    )

    existing = db.query(FeatureDefinition).filter(FeatureDefinition.name == boolean_feature.name).first()
    if not existing:
        db.add(boolean_feature)
        db.commit()

def seed_all(db: Session):
    """Run all seed functions."""
    seed_default_feature_values(db) 