# Project Explanation: ToxDB

## Overview

ToxDB is an open-source, community-driven toxicology database designed to collect, organize, and make accessible scientific data from toxicological studies. It provides a standardized format for recording toxicology experiments, with a hierarchical data structure that accommodates different animal models, dose groups, and outcome measurements.

## Problem

Toxicology research generates vast amounts of data that are often stored in disparate formats, making it difficult to compare results across studies or perform meta-analyses. Researchers, citizens, and regulatory agencies need a standardized way to record, access, and analyze toxicology data to make informed decisions about chemical safety.

## Solution: ToxDB

ToxDB addresses this problem by providing an open-source platform where toxicology data can be recorded in a standardized format. The application enables researchers, regulatory scientists, and community members to:

1. Document toxicology studies with detailed metadata
2. Record animal model characteristics for each study
3. Specify dose groups and exposure conditions
4. Track outcome measurements (e.g., cancer incidence, organ effects)

The hierarchical data structure ensures that relationships between studies, animal models, dose groups, and outcomes are preserved, allowing for nested queries and analysis.

## Technical Implementation

### Backend Architecture

ToxDB is built with Flask, a lightweight Python web framework, and uses SQLAlchemy as an ORM (Object-Relational Mapping) layer for database interactions. This combination provides:

- Flexibility for future expansion
- Maintainable codebase through model-view separation
- Efficient database operations

The data models mirror the hierarchical structure of toxicology research, with foreign key relationships maintaining data integrity.

## Features

- **Hierarchical Data Structure**: Study → Animal Model → Dose Group → Outcome
- **Flexible Metadata System**: Add custom fields to any entity in the system
- **Controlled Vocabularies**: Standardized fields for sex, dose units, route of exposure, and outcome types
- **Contributor Verification**: Requires a university or work e-mail (stored, never displayed)
- **Data Export**: Export study data in CSV format
- **Step-by-Step Workflow**: Guided data entry process

### User Interface Design

The user interface follows a step-by-step workflow that guides users through the process of adding toxicology data:

1. First, users enter basic study information
2. Then, they add details about the animal model used
3. Next, they specify dose groups
4. Finally, they record the outcomes observed, linked to the dose groups

This guided approach reduces errors and ensures complete data entry. The UI is built with Bootstrap 5, providing a responsive design that works on both desktop and mobile devices.

### Data Model

ToxDB organizes toxicology data in the following hierarchy:

1. **Toxin**: Basic information about the chemical being studied
2. **Study**: Top-level entity containing general information about the research
3. **Animal Model**: Information about the test subjects used in the study
4. **Dose Group**: Details about exposure levels and conditions
5. **Outcome**: Observed effects or results
6. **AdditionalMetadata**: Flexible system for adding custom fields to any entity

### Data Validation

ToxDB implements various validation mechanisms:

- Required fields must be completed before moving to the next step
- Numeric fields are validated to ensure they contain valid numbers
- Controlled vocabularies standardize sex, dose units, route of exposure, and outcome types
- Contributor e-mail must match a non-public, institutional domain
- Custom units can be specified when standard options don't apply

## Future Directions

Potential enhancements for future versions of ToxDB include:

1. **Advanced Search**: Implementing filters and search capabilities to find specific studies
2. **Data Export**: Adding options to export data formats other than CSV (JSON, etc.)
3. **Data Visualization**: Incorporating charts and graphs to visualize dose-response relationships
4. **API Access**: Developing an API to allow programmatic access to the database
5. **User Authentication**: Adding user accounts with different permission levels
6. **Peer Review System**: Implementing a review process for community-contributed data

## Impact and Benefits

ToxDB has the potential to significantly impact toxicology research and regulatory science by:

- **Standardizing Data Collection**: Providing a consistent format for recording toxicology studies
- **Improving Data Accessibility**: Making toxicology data more accessible to researchers
- **Enabling Meta-Analysis**: Facilitating the comparison of results across multiple studies
- **Supporting Regulatory Decisions**: Providing a comprehensive database that can inform risk assessments
- **Promoting Transparency**: Making toxicology data openly available to the scientific community and public

By creating an open repository of toxicology data, ToxDB intends to support more efficient research, better-informed regulatory decisions, and ultimately, improved protection of human health and the environment.


## Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)
- Git (optional, for cloning the repository)

### Setup Instructions

1. Clone the repository or download the source code:
   ```bash
   git clone https://github.com/yourusername/toxdb.git
   cd toxdb
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialise the database (SQLite quick-start – run once):

   ```bash
   # open the flask shell with your application context
   flask --app app.py shell
   >>> from app import db
   >>> db.create_all()
   >>> exit()

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```



## Project Structure

```
toxdb/
  ├── app.py                # Main application file with routes
  ├── models.py             # Database models
  ├── requirements.txt      # Python dependencies
  ├── Procfile              # Heroku deployment configuration
  └── templates/            # HTML templates
      ├── base.html         # Base template with navigation
      ├── home.html         # Landing page
      ├── about.html        # About page
      ├── list_studies.html # List of all studies
      ├── new_study.html    # Form to create a new study
      ├── new_animal_model.html # Form for animal model details
      ├── new_dose_group.html   # Form for dose group information
      ├── select_dose_for_outcome.html # Select dose group for outcomes
      ├── new_outcome.html      # Form for outcome data
      ├── view_study.html       # Detailed study view
      └── view_study_long.html  # Long-format view of study data
```


## Usage

### Adding a New Study

1. Click on "Add Study" in the navigation bar
2. Fill in the study information and continue
3. Add animal model details
4. Add one or more dose groups 
5. Select a dose group and enter outcome data
6. Review the completed study

### Browsing Studies

1. Click on "Studies" in the navigation bar
2. Browse the list of available studies
3. Click on a study to view its details

### Exporting Data

1. View a study's details page
2. Click on "Export to CSV" to download the study data

## Data Structure

### Study
- Study name
- Toxin studied
- Description
- Date conducted
- Author/researcher
- Contributor name 
- Contributor e-mail (required; stored privately, never shown publicly)
- Publication reference
- Custom metadata fields

### Animal Model
- Species
- Strain
- Sex (controlled vocabulary: male, female, mixed)
- Age
- Weight
- Description
- Custom metadata fields

### Dose Group
- Dose value
- Dose unit (controlled vocabulary: mg/m³, ppm, ppb, other)
- Route of exposure (oral, inhalation, dermal, intraperitoneal, other)
- Group size
- Exposure duration
- Custom metadata fields

### Outcome
- Outcome type (controlled vocabulary: cancer, organ weight, mortality, other)
- Value/result
- Observation time
- Notes
- Custom metadata fields

## Contributing

We welcome contributions from the community! Here are some ways you can help:

1. **Adding Data**: Enter toxicology studies through the web interface
2. **Code Contributions**: Help improve the functionality or fix bugs
3. **Documentation**: Help improve the documentation
4. **Reporting Issues**: Report any bugs or suggest features

## Technologies Used

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, Bootstrap 5
- **Database**: SQLite (development), PostgreSQL (production)
- **Deployment**: Heroku

## License

This project is licensed under the MIT License.
