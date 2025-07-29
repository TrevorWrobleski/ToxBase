import os
import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from models import db, Toxin, Study, AnimalModel, DoseGroup, Outcome, AdditionalMetadata
from datetime import datetime

# Constants for controlled vocabularies
SEX_CHOICES = [('male', 'Male'), ('female', 'Female'), ('mixed', 'Mixed')]
DOSE_UNIT_CHOICES = [('mg/m3', 'mg/m3'), ('ppm', 'ppm'), ('ppb', 'ppb'), ('other', 'Other')]
OUTCOME_TYPE_CHOICES = [
    ('cancer', 'Cancer Incidence'),
    ('organ_weight', 'Organ Weight Change'),
    ('mortality', 'Mortality'),
    ('other', 'Other')
]
ROUTE_CHOICES = [
    ('oral',        'Oral'),
    ('inhalation',  'Inhalation'),
    ('dermal',      'Dermal'),
    ('intraperitoneal', 'Intraperitoneal'),
    ('other',       'Other / Mixed')
]


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///toxdb.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        studies = Study.query.order_by(Study.created_at.desc()).limit(5).all()
        return render_template('home.html', studies=studies)

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/study/new', methods=['GET', 'POST'])
    def new_study():
        """
        Step-1 page of the wizard.
        Adds:
          • required contributor_email
          • simple “work / university” e-mail check
        """
        if request.method == 'POST':
            # ── 1. Read form fields ───────────────────────────────────────────
            name = request.form['name']
            toxin_name = request.form['toxin_name']
            description = request.form.get('description', '')
            date_conducted_str = request.form.get('date_conducted', '')
            author = request.form.get('author', '')
            contributor_name = request.form.get('contributor_name', '')
            contributor_email = request.form.get('contributor_email', '')

            # ── 2. Validate e-mail (disallow gmail, yahoo, etc.) ──────────────
            import re
            WORK_EMAIL_RE = re.compile(
                r'^[\w\.\-]+@(?!(gmail|yahoo|outlook|hotmail|protonmail)\.)[\w\.\-]+\.[a-z]{2,}$',
                re.I
            )
            if not WORK_EMAIL_RE.match(contributor_email):
                flash('Please use your university or work e-mail address.', 'danger')
                return render_template('new_study.html', toxins=Toxin.query.all())

            # ── 3. Parse optional date field ─────────────────────────────────
            date_conducted = None
            if date_conducted_str:
                try:
                    date_conducted = datetime.strptime(date_conducted_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                    return render_template('new_study.html', toxins=Toxin.query.all())

            # ── 4. Ensure the toxin exists (or create it) ────────────────────
            toxin = Toxin.query.filter_by(name=toxin_name).first()
            if not toxin:
                toxin = Toxin(name=toxin_name, description='')
                db.session.add(toxin)
                db.session.commit()

            # ── 5. Create the Study record ───────────────────────────────────
            study = Study(
                name=name,
                toxin_id=toxin.id,
                description=description,
                date_conducted=date_conducted,
                author=author,
                contributor_name=contributor_name,
                contributor_email=contributor_email,  # <-- NEW
                publication_reference=request.form.get('publication_reference', '')
            )
            db.session.add(study)
            db.session.commit()

            # ── 6. Optional extra metadata pairs ─────────────────────────────
            field_names = request.form.getlist('additional_field_name[]')
            field_values = request.form.getlist('additional_field_value[]')
            for i in range(len(field_names)):
                if i < len(field_values) and field_names[i].strip():
                    db.session.add(
                        AdditionalMetadata(
                            entity_type='study',
                            entity_id=study.id,
                            field_name=field_names[i].strip(),
                            field_value=field_values[i].strip()
                        )
                    )
            db.session.commit()

            flash('Study created successfully!', 'success')
            return redirect(url_for('new_animal_model', study_id=study.id))

        # ── GET request – just show the blank form ───────────────────────────
        toxins = Toxin.query.all()
        return render_template('new_study.html', toxins=toxins)

    @app.route('/study/<int:study_id>/animal/new', methods=['GET', 'POST'])
    def new_animal_model(study_id):
        study = Study.query.get_or_404(study_id)

        if request.method == 'POST':
            species = request.form['species']
            strain = request.form.get('strain', '')
            sex = request.form['sex']
            age = request.form.get('age', '')
            weight = request.form.get('weight', '')
            description = request.form.get('description', '')

            animal_model = AnimalModel(
                study_id=study.id,
                species=species,
                strain=strain,
                sex=sex,
                age=age,
                weight=weight,
                description=description
            )
            db.session.add(animal_model)
            db.session.commit()

            # Process additional fields
            field_names = request.form.getlist('additional_field_name[]')
            field_values = request.form.getlist('additional_field_value[]')

            for i in range(len(field_names)):
                if i < len(field_values) and field_names[i].strip():
                    metadata = AdditionalMetadata(
                        entity_type='animal_model',
                        entity_id=animal_model.id,
                        field_name=field_names[i].strip(),
                        field_value=field_values[i].strip()
                    )
                    db.session.add(metadata)

            db.session.commit()

            flash('Animal model created successfully!', 'success')
            return redirect(url_for('new_dose_group', animal_id=animal_model.id))

        return render_template('new_animal_model.html', study=study, sex_choices=SEX_CHOICES)

    @app.route('/animal/<int:animal_id>/dose/new', methods=['GET', 'POST'])
    def new_dose_group(animal_id):
        animal_model = AnimalModel.query.get_or_404(animal_id)

        # make this available for the error-render that follows
        existing_dose_groups = DoseGroup.query.filter_by(
            animal_model_id=animal_id
        ).all()

        if request.method == 'POST':
            try:
                dose_value = float(request.form['dose_value'])
                if dose_value < 0:
                    raise ValueError("Dose value must be non-negative")

                group_size = int(request.form['group_size'])
                if group_size <= 0:
                    raise ValueError("Group size must be a positive integer")

            except ValueError as e:
                flash(f'Input validation error: {str(e)}', 'danger')
                return render_template(
                    'new_dose_group.html',
                    animal_model=animal_model,
                    existing_dose_groups=existing_dose_groups,
                    dose_unit_choices=DOSE_UNIT_CHOICES,
                    route_choices=ROUTE_CHOICES  # new
                )

            dose_unit = request.form['dose_unit']
            custom_dose_unit = request.form.get('custom_dose_unit', '') if dose_unit == 'other' else None
            exposure_duration = request.form.get('exposure_duration', '')

            # ── NEW: route of exposure ───────────────────────────────
            route_choice = request.form['route_of_exposure']
            custom_route = request.form.get('custom_route', '') if route_choice == 'other' else None
            route_of_exposure = custom_route if route_choice == 'other' else route_choice

            dose_group = DoseGroup(
                animal_model_id=animal_model.id,
                dose_value=dose_value,
                dose_unit=dose_unit,
                custom_dose_unit=custom_dose_unit,
                group_size=group_size,
                exposure_duration=exposure_duration,
                route_of_exposure=route_of_exposure  # <── add this line
            )
            db.session.add(dose_group)
            db.session.commit()

            # Process additional fields
            field_names = request.form.getlist('additional_field_name[]')
            field_values = request.form.getlist('additional_field_value[]')

            for i in range(len(field_names)):
                if i < len(field_values) and field_names[i].strip():
                    metadata = AdditionalMetadata(
                        entity_type='dose_group',
                        entity_id=dose_group.id,
                        field_name=field_names[i].strip(),
                        field_value=field_values[i].strip()
                    )
                    db.session.add(metadata)

            db.session.commit()

            flash('Dose group created successfully!', 'success')

            # Check if user wants to add another dose group or proceed to outcomes
            if 'add_another' in request.form:
                return redirect(url_for('new_dose_group', animal_id=animal_model.id))
            else:
                # Instead of directly redirecting to a specific dose group's outcome page,
                # redirect to outcome selection page for this animal model
                return redirect(url_for('select_dose_for_outcome', animal_id=animal_model.id))

        # Get existing dose groups for this animal model to display
        existing_dose_groups = DoseGroup.query.filter_by(animal_model_id=animal_id).all()

        return render_template('new_dose_group.html',
                               animal_model=animal_model,
                               existing_dose_groups=existing_dose_groups,
                               dose_unit_choices=DOSE_UNIT_CHOICES,
                               route_choices=ROUTE_CHOICES)

    # New route for selecting dose group before adding an outcome
    @app.route('/animal/<int:animal_id>/outcome/select-dose', methods=['GET'])
    def select_dose_for_outcome(animal_id):
        animal_model = AnimalModel.query.get_or_404(animal_id)
        dose_groups = DoseGroup.query.filter_by(animal_model_id=animal_id).all()

        if not dose_groups:
            flash('No dose groups exist for this animal model. Please add a dose group first.', 'warning')
            return redirect(url_for('new_dose_group', animal_id=animal_id))

        return render_template('select_dose_for_outcome.html',
                               animal_model=animal_model,
                               dose_groups=dose_groups)

    # Modified outcome route
    @app.route('/dose/<int:dose_id>/outcome/new', methods=['GET', 'POST'])
    def new_outcome(dose_id):
        dose_group = DoseGroup.query.get_or_404(dose_id)

        if request.method == 'POST':
            outcome_type = request.form['outcome_type']
            custom_outcome_type = request.form.get('custom_outcome_type', '') if outcome_type == 'other' else None

            # Get the value based on outcome type
            if outcome_type == 'cancer' and 'cancer_value' in request.form and request.form['cancer_value']:
                value = request.form['cancer_value']
                # Validate tumor count
                try:
                    tumor_count = int(value)
                    if tumor_count < 0:
                        raise ValueError("Tumor count must be non-negative")
                except ValueError as e:
                    flash(f'Invalid tumor count: {str(e)}', 'danger')
                    return render_template('new_outcome.html',
                                           dose_group=dose_group,
                                           outcome_type_choices=OUTCOME_TYPE_CHOICES)
            else:
                value = request.form['value']

            observation_time = request.form.get('observation_time', '')
            notes = request.form.get('notes', '')

            outcome = Outcome(
                dose_group_id=dose_group.id,
                outcome_type=outcome_type,
                custom_outcome_type=custom_outcome_type,
                value=value,
                observation_time=observation_time,
                notes=notes
            )
            db.session.add(outcome)
            db.session.commit()

            # Process additional fields
            field_names = request.form.getlist('additional_field_name[]')
            field_values = request.form.getlist('additional_field_value[]')

            for i in range(len(field_names)):
                if i < len(field_values) and field_names[i].strip():
                    metadata = AdditionalMetadata(
                        entity_type='outcome',
                        entity_id=outcome.id,
                        field_name=field_names[i].strip(),
                        field_value=field_values[i].strip()
                    )
                    db.session.add(metadata)

            db.session.commit()

            flash('Outcome added successfully!', 'success')

            # Option to add another outcome
            if 'add_another' in request.form:
                # User wants to add another outcome to the same dose group
                return redirect(url_for('new_outcome', dose_id=dose_group.id))
            elif 'add_another_dose' in request.form:
                # User wants to add an outcome to a different dose group
                return redirect(url_for('select_dose_for_outcome', animal_id=dose_group.animal_model_id))
            else:
                # User is done adding outcomes
                return redirect(url_for('view_study', study_id=dose_group.animal_model.study_id))

        return render_template('new_outcome.html',
                               dose_group=dose_group,
                               outcome_type_choices=OUTCOME_TYPE_CHOICES)

    @app.route('/study/<int:study_id>')
    def view_study(study_id):
        study = Study.query.get_or_404(study_id)

        # Get additional metadata for the study
        study_metadata = AdditionalMetadata.query.filter_by(entity_type='study', entity_id=study_id).all()

        # Get metadata for all related entities
        metadata = {}
        for animal_model in study.animal_models:
            animal_meta = AdditionalMetadata.query.filter_by(entity_type='animal_model',
                                                             entity_id=animal_model.id).all()
            if animal_meta:
                metadata[f'animal_{animal_model.id}'] = animal_meta

            for dose_group in animal_model.dose_groups:
                dose_meta = AdditionalMetadata.query.filter_by(entity_type='dose_group', entity_id=dose_group.id).all()
                if dose_meta:
                    metadata[f'dose_{dose_group.id}'] = dose_meta

                for outcome in dose_group.outcomes:
                    outcome_meta = AdditionalMetadata.query.filter_by(entity_type='outcome', entity_id=outcome.id).all()
                    if outcome_meta:
                        metadata[f'outcome_{outcome.id}'] = outcome_meta

        return render_template('view_study.html',
                               study=study,
                               study_metadata=study_metadata,
                               metadata=metadata,
                               outcome_type_choices=OUTCOME_TYPE_CHOICES)

    @app.route('/studies')
    def list_studies():
        studies = Study.query.order_by(Study.created_at.desc()).all()
        return render_template('list_studies.html', studies=studies)

    @app.route('/entity/<entity_type>/<int:entity_id>/metadata/add', methods=['POST'])
    def add_metadata(entity_type, entity_id):
        if entity_type not in ['study', 'animal_model', 'dose_group', 'outcome']:
            flash('Invalid entity type', 'danger')
            return redirect(url_for('home'))

        # Check if entity exists
        entity = None
        if entity_type == 'study':
            entity = Study.query.get_or_404(entity_id)
        elif entity_type == 'animal_model':
            entity = AnimalModel.query.get_or_404(entity_id)
        elif entity_type == 'dose_group':
            entity = DoseGroup.query.get_or_404(entity_id)
        elif entity_type == 'outcome':
            entity = Outcome.query.get_or_404(entity_id)

        field_name = request.form.get('field_name')
        field_value = request.form.get('field_value')

        if not field_name:
            flash('Field name is required', 'danger')
            return redirect(url_for('view_study', study_id=get_study_id(entity_type, entity)))

        # Check if this field already exists
        existing = AdditionalMetadata.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name
        ).first()

        if existing:
            existing.field_value = field_value
        else:
            metadata = AdditionalMetadata(
                entity_type=entity_type,
                entity_id=entity_id,
                field_name=field_name,
                field_value=field_value
            )
            db.session.add(metadata)

        db.session.commit()
        flash('Additional information saved', 'success')
        return redirect(url_for('view_study', study_id=get_study_id(entity_type, entity)))

    @app.route('/study/<int:study_id>/export')
    def export_study(study_id):
        study = Study.query.get_or_404(study_id)

        # Create a CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow([
            'Study ID', 'Study Name', 'Toxin', 'Date Conducted', 'Author', 'Contributor',
            'Animal Species', 'Strain', 'Sex', 'Age', 'Weight',
            'Dose Value', 'Dose Unit', 'Route of Exposure',  # new column
            'Group Size', 'Exposure Duration',
            'Outcome Type', 'Outcome Value', 'Observation Time', 'Notes'
        ])

        # Write data in long format
        for animal_model in study.animal_models:
            for dose_group in animal_model.dose_groups:
                dose_unit = dose_group.custom_dose_unit if dose_group.dose_unit == 'other' else dose_group.dose_unit

                for outcome in dose_group.outcomes:
                    outcome_type = outcome.custom_outcome_type if outcome.outcome_type == 'other' else outcome.outcome_type

                    writer.writerow([
                        study.id, study.name, study.toxin.name, study.date_conducted, study.author,
                        study.contributor_name,
                        animal_model.species, animal_model.strain, animal_model.sex, animal_model.age,
                        animal_model.weight,
                        dose_group.dose_value, dose_unit, dose_group.route_of_exposure,  # new
                        dose_group.group_size, dose_group.exposure_duration,
                        outcome_type, outcome.value, outcome.observation_time, outcome.notes
                    ])

        # Prepare response
        output.seek(0)
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=study_{study_id}_data.csv"}
        )

    @app.route('/study/<int:study_id>/long-format')
    def view_study_long_format(study_id):
        study = Study.query.get_or_404(study_id)

        # Prepare data in long format
        rows = []
        for animal_model in study.animal_models:
            for dose_group in animal_model.dose_groups:
                dose_unit = dose_group.custom_dose_unit if dose_group.dose_unit == 'other' else dose_group.dose_unit

                for outcome in dose_group.outcomes:
                    outcome_type = outcome.custom_outcome_type if outcome.outcome_type == 'other' else outcome.outcome_type

                    rows.append({
                        'animal_species': animal_model.species,
                        'animal_strain': animal_model.strain,
                        'animal_sex': animal_model.sex,
                        'dose_value': dose_group.dose_value,
                        'dose_unit': dose_unit,
                        'group_size': dose_group.group_size,
                        'outcome_type': outcome_type,
                        'outcome_value': outcome.value,
                        'observation_time': outcome.observation_time
                    })

        return render_template('view_study_long.html', study=study, rows=rows)

    def get_study_id(entity_type, entity):
        """Helper to get the study ID from any entity type"""
        if entity_type == 'study':
            return entity.id
        elif entity_type == 'animal_model':
            return entity.study_id
        elif entity_type == 'dose_group':
            return entity.animal_model.study_id
        elif entity_type == 'outcome':
            return entity.dose_group.animal_model.study_id

    return app

# Context processor
@app.context_processor
def inject_label_maps():
    return dict(
        OUTCOME_LABELS=dict(OUTCOME_TYPE_CHOICES),
        DOSE_UNIT_LABELS=dict(DOSE_UNIT_CHOICES),
        ROUTE_LABELS=dict(ROUTE_CHOICES),
        SEX_LABELS=dict(SEX_CHOICES)
    )

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)