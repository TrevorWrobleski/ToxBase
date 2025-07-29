from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Toxin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    studies = db.relationship('Study', backref='toxin', lazy=True)

    def __repr__(self):
        return f"<Toxin {self.name}>"


class Study(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    toxin_id = db.Column(db.Integer, db.ForeignKey('toxin.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_conducted = db.Column(db.Date, nullable=True)
    author = db.Column(db.String(255), nullable=True)
    contributor_name = db.Column(db.String(255), nullable=True)
    contributor_email = db.Column(db.String(255), nullable=False)  # hidden from templates
    publication_reference = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    animal_models = db.relationship('AnimalModel', backref='study', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Study {self.name}>"


class AnimalModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'), nullable=False)
    species = db.Column(db.String(255), nullable=False)
    strain = db.Column(db.String(255), nullable=True)
    sex = db.Column(db.String(10), nullable=False)  # Controlled: 'male', 'female', 'mixed'
    age = db.Column(db.String(255), nullable=True)
    weight = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)

    dose_groups = db.relationship('DoseGroup', backref='animal_model', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<AnimalModel {self.species} ({self.sex})>"


class DoseGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_model_id = db.Column(db.Integer, db.ForeignKey('animal_model.id'), nullable=False)
    dose_value = db.Column(db.Float, nullable=False)
    dose_unit = db.Column(db.String(10), nullable=False)  # Controlled: 'mg/m3', 'ppm', 'ppb', 'other'
    custom_dose_unit = db.Column(db.String(255), nullable=True)  # Used when dose_unit is 'other'
    group_size = db.Column(db.Integer, nullable=False)
    exposure_duration = db.Column(db.String(255), nullable=True)
    route_of_exposure = db.Column(
        db.String(30),  # 'oral', 'inhalation', 'dermal', …
        nullable=False,
        default='unknown'
    )

    outcomes = db.relationship('Outcome', backref='dose_group', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        unit = self.custom_dose_unit if self.dose_unit == 'other' else self.dose_unit
        return f"<DoseGroup {self.dose_value} {unit}>"


class Outcome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dose_group_id = db.Column(db.Integer, db.ForeignKey('dose_group.id'), nullable=False)
    outcome_type = db.Column(db.String(20),
                             nullable=False)  # Controlled: 'cancer', 'organ_weight', 'mortality', 'other'
    custom_outcome_type = db.Column(db.String(255), nullable=True)  # Used when outcome_type is 'other'
    value = db.Column(db.Text, nullable=False)
    observation_time = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        outcome = self.custom_outcome_type if self.outcome_type == 'other' else self.outcome_type
        return f"<Outcome {outcome}>"


class AdditionalMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)  # study, animal_model, dose_group, outcome
    entity_id = db.Column(db.Integer, nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_value = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'field_name', name='unique_metadata_field'),
    )

    def __repr__(self):
        return f"<Metadata {self.entity_type}:{self.entity_id} {self.field_name}={self.field_value}>"