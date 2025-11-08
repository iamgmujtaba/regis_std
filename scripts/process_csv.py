#!/usr/bin/env python3
"""
Enhanced CSV Processing Script for Regis University Data Science Practicum
Processes CSV files to generate student folders and markdown profiles
"""

import os
import csv
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
import argparse

def clean_email(email):
    """
    Clean email address by removing worldclass subdomain
    ajensen008@worldclass.regis.edu -> ajensen008@regis.edu
    """
    if not email:
        return email
    
    # Remove worldclass subdomain if present
    email = email.replace('@worldclass.regis.edu', '@regis.edu')
    
    # Ensure it ends with @regis.edu if it doesn't already
    if '@regis.edu' not in email and '@' in email:
        username = email.split('@')[0]
        email = f"{username}@regis.edu"
    
    return email

def parse_course_code(csv_filename):
    """
    Parse course information from CSV filename
    2025_Summer_MSDS692.csv -> {year: 2025, semester: summer, course: msds692}
    """
    # Remove .csv extension and split by underscore
    base_name = os.path.splitext(csv_filename)[0]
    parts = base_name.split('_')
    
    if len(parts) >= 3:
        year = parts[0]
        semester = parts[1].lower()
        course = parts[2].lower()
        
        # Create folder name: 2025_summer_msds692
        folder_name = f"{year}_{semester}_{course}"
        
        return {
            'year': year,
            'semester': semester,
            'course': course,
            'folder_name': folder_name,
            'display_name': f"{course.upper()} - {semester.title()} {year}"
        }
    else:
        # Fallback for non-standard names
        return {
            'year': '2025',
            'semester': 'spring',
            'course': 'msds692',
            'folder_name': base_name,
            'display_name': base_name
        }

def validate_csv_row(row, required_fields):
    """Validate CSV row has all required fields"""
    missing_fields = []
    for field in required_fields:
        if field not in row or not row[field].strip():
            missing_fields.append(field)
    
    return missing_fields

def generate_fallback_url(base_url, field_name):
    """Generate fallback URL that redirects to profile"""
    return f"{base_url}#"  # Will redirect to profile page

def load_existing_profile(profile_path):
    """Load existing profile and extract practicum data"""
    if not profile_path.exists():
        return None, []
    
    with open(profile_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract existing practicum sections
    import re
    practicum_pattern = r'## (MSDS \d+) - Practicum ([IV]+)\n\n(.*?)(?=\n## |$)'
    existing_practica = re.findall(practicum_pattern, content, re.DOTALL)
    
    return content, existing_practica

def create_markdown_profile(student_data, course_info, existing_content=None, existing_practica=None):
    """
    Create or update markdown profile from CSV data
    Handles multiple practicum experiences in one profile
    """
    name = student_data['Student Name']
    email = clean_email(student_data['Email'])
    username = student_data['Username']
    project_title = student_data['Project Title']
    github = student_data.get('GitHub', '')
    
    # Determine course type
    is_msds692 = 'msds692' in course_info['course'].lower()
    course_number = "MSDS 692" if is_msds692 else "MSDS 696"
    practicum_number = "I" if is_msds692 else "II"
    
    # Split name into first and last
    name_parts = name.split(' ')
    first_name = name_parts[0] if name_parts else username
    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
    
    # Generate tags based on project title
    tags = extract_project_tags(project_title)
    
    # If updating existing profile, parse and merge
    if existing_content and existing_practica:
        return update_existing_profile(existing_content, existing_practica, student_data, course_info, practicum_number, project_title, tags)
    
    # Create new profile with current practicum
    current_practicum_section = f'''## {course_number} - Practicum {practicum_number}

**Title:** {project_title}

**Semester:** {course_info['semester'].title()} {course_info['year']}

**Tags:** {', '.join(tags)}

**Abstract:** This project focuses on {project_title.lower()}. Please update this section with a detailed description of your project, methodology, and key findings.

**Key Achievements:**
- Please add your key project achievements
- Include quantifiable results where possible
- Highlight technical innovations or challenges overcome

**Technologies Used:** Please list the main technologies and tools used in your project

**Links:**
- GitHub Repository: [{github if github else 'Add your GitHub link'}]({github if github else '#'})
- Project Report: [Download Report](reports/{username}_practicum{practicum_number.lower()}_report.pdf)
- Presentation Slides: [View Slides](presentations/{username}_practicum{practicum_number.lower()}_slides.pdf)

*Please update the links above with your actual project URLs and ensure your PDF files are uploaded to the correct folders.*
'''

    markdown_content = f'''---
name: "{name}"
firstName: "{first_name}"
lastName: "{last_name}"
email: "{email}"
username: "{username}"
github: "{username}"
linkedin: "{username}"
graduation: "May {int(course_info['year']) + 1}"
major: "Data Science"
degree: "Master of Science in Data Science"
university: "Regis University"
current_course: "{course_number}"
current_semester: "{course_info['semester'].title()} {course_info['year']}"
---

## About Me

I am a dedicated Data Science graduate student at Regis University. My focus is on applying data science techniques to solve real-world problems and gain practical experience in the field.

*Please update this section with your personal background, interests, and career goals.*

## Skills

**Programming Languages:**
- Python - Intermediate
- R - Intermediate  
- SQL - Intermediate

**Data Science Tools:**
- Pandas, NumPy
- Matplotlib, Seaborn
- Scikit-learn

**Technologies:**
- Jupyter Notebooks
- Git/GitHub
- Excel

*Please update this section with your actual skills and proficiency levels.*

{current_practicum_section}

## Contact

**Email:** {email}

**LinkedIn:** [Connect with me](https://linkedin.com/in/{username})

**GitHub:** [View my repositories](https://github.com/{username})

**Portfolio:** [Visit my portfolio](https://your-portfolio-site.com)

*Please update the links above with your actual social media and portfolio URLs.*

---

*This profile was auto-generated from CSV data. Please update all sections with your actual information, projects, and experiences.*
'''
    
    return markdown_content

def update_existing_profile(existing_content, existing_practica, student_data, course_info, practicum_number, project_title, tags):
    """Update existing profile with new practicum information"""
    import re
    
    username = student_data['Username']
    github = student_data.get('GitHub', '')
    course_number = "MSDS 692" if 'msds692' in course_info['course'].lower() else "MSDS 696"
    
    # Check if this practicum already exists
    practicum_exists = any(p[0] == course_number for p in existing_practica)
    
    if practicum_exists:
        # Update existing practicum section
        pattern = rf'(## {course_number} - Practicum {practicum_number}\n\n)(.*?)(?=\n## |$)'
        
        new_section = f'''## {course_number} - Practicum {practicum_number}

**Title:** {project_title}

**Semester:** {course_info['semester'].title()} {course_info['year']}

**Tags:** {', '.join(tags)}

**Abstract:** This project focuses on {project_title.lower()}. Please update this section with a detailed description of your project, methodology, and key findings.

**Key Achievements:**
- Please add your key project achievements
- Include quantifiable results where possible
- Highlight technical innovations or challenges overcome

**Technologies Used:** Please list the main technologies and tools used in your project

**Links:**
- GitHub Repository: [{github if github else 'Add your GitHub link'}]({github if github else '#'})
- Project Report: [Download Report](reports/{username}_practicum{practicum_number.lower()}_report.pdf)
- Presentation Slides: [View Slides](presentations/{username}_practicum{practicum_number.lower()}_slides.pdf)

*Please update the links above with your actual project URLs and ensure your PDF files are uploaded to the correct folders.*

'''
        
        updated_content = re.sub(pattern, new_section, existing_content, flags=re.DOTALL)
    else:
        # Add new practicum section before Contact section
        new_section = f'''## {course_number} - Practicum {practicum_number}

**Title:** {project_title}

**Semester:** {course_info['semester'].title()} {course_info['year']}

**Tags:** {', '.join(tags)}

**Abstract:** This project focuses on {project_title.lower()}. Please update this section with a detailed description of your project, methodology, and key findings.

**Key Achievements:**
- Please add your key project achievements
- Include quantifiable results where possible
- Highlight technical innovations or challenges overcome

**Technologies Used:** Please list the main technologies and tools used in your project

**Links:**
- GitHub Repository: [{github if github else 'Add your GitHub link'}]({github if github else '#'})
- Project Report: [Download Report](reports/{username}_practicum{practicum_number.lower()}_report.pdf)
- Presentation Slides: [View Slides](presentations/{username}_practicum{practicum_number.lower()}_slides.pdf)

*Please update the links above with your actual project URLs and ensure your PDF files are uploaded to the correct folders.*

'''
        
        # Insert before Contact section
        contact_pattern = r'(\n## Contact\n)'
        if re.search(contact_pattern, existing_content):
            updated_content = re.sub(contact_pattern, f'\n{new_section}\n## Contact\n', existing_content)
        else:
            # If no Contact section found, append at end
            updated_content = existing_content.rstrip() + '\n\n' + new_section
    
    # Update frontmatter with current course info
    frontmatter_pattern = r'(current_course: ".*?")'
    updated_content = re.sub(frontmatter_pattern, f'current_course: "{course_number}"', updated_content)
    
    frontmatter_pattern = r'(current_semester: ".*?")'
    updated_content = re.sub(frontmatter_pattern, f'current_semester: "{course_info["semester"].title()} {course_info["year"]}"', updated_content)
    
    return updated_content

def extract_project_tags(project_title):
    """
    Extract relevant tags from project title
    """
    tags = []
    title_lower = project_title.lower()
    
    # Common technology/methodology keywords
    tag_keywords = {
        'machine learning': 'Machine Learning',
        'deep learning': 'Deep Learning',
        'neural network': 'Neural Networks',
        'classification': 'Classification',
        'regression': 'Regression',
        'clustering': 'Clustering',
        'nlp': 'Natural Language Processing',
        'natural language': 'Natural Language Processing',
        'computer vision': 'Computer Vision',
        'image processing': 'Image Processing',
        'data visualization': 'Data Visualization',
        'predictive': 'Predictive Analytics',
        'analysis': 'Data Analysis',
        'python': 'Python',
        'r programming': 'R',
        'sql': 'SQL',
        'web scraping': 'Web Scraping',
        'api': 'API Integration',
        'dashboard': 'Dashboard',
        'time series': 'Time Series Analysis',
        'forecasting': 'Forecasting',
        'recommendation': 'Recommendation Systems',
        'sentiment': 'Sentiment Analysis',
        'text mining': 'Text Mining',
        'big data': 'Big Data',
        'spark': 'Apache Spark',
        'hadoop': 'Hadoop',
        'tensorflow': 'TensorFlow',
        'pytorch': 'PyTorch',
        'scikit': 'Scikit-learn',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'matplotlib': 'Matplotlib',
        'seaborn': 'Seaborn',
        'plotly': 'Plotly',
        'tableau': 'Tableau',
        'power bi': 'Power BI',
        'excel': 'Excel',
        'statistics': 'Statistics',
        'statistical': 'Statistics'
    }
    
    for keyword, tag in tag_keywords.items():
        if keyword in title_lower:
            if tag not in tags:
                tags.append(tag)
    
    # If no specific tags found, add generic ones
    if not tags:
        tags = ['Data Science', 'Python', 'Analytics']
    
    return tags[:5]  # Limit to 5 tags

def generate_course_json(students_data, course_info, csv_file):
    """
    Generate JSON structure for GitHub Actions processing
    This JSON will be used to create the unified student profiles
    """
    # Map course code for JSON
    course_code = "MSDS692" if 'msds692' in course_info['course'].lower() else "MSDS696"
    practicum_name = "Data Science Practicum I" if 'msds692' in course_info['course'].lower() else "Data Science Practicum II"
    
    # Determine term code (this might need adjustment based on your term system)
    term_suffix = "8W1" if 'msds692' in course_info['course'].lower() else "8W2"
    term_code = f"{course_info['year'][2:]}SU{term_suffix}"  # e.g., "25SU8W1"
    
    course_json = {
        "course": {
            "code": course_code,
            "name": practicum_name,
            "semester": course_info['semester'].title(),
            "year": course_info['year'],
            "term": term_code,
            "description": f"{'Foundational' if 'msds692' in course_info['course'].lower() else 'Advanced'} practicum experience focusing on real-world data science applications {'and methodology' if 'msds692' in course_info['course'].lower() else 'and industry partnerships'}."
        },
        "students": []
    }
    
    # Add students
    for student_data in students_data:
        username = student_data['Username']
        
        # Build student JSON structure
        student_json = {
            "username": username,
            "name": student_data['Student Name'],
            "email": clean_email(student_data['Email']),
            "projectTitle": student_data['Project Title'],
            "avatarPath": f"https://raw.githubusercontent.com/iamgmujtaba/regis_std/main/data/students/{username}/avatar.webp",  # Standard avatar path
            "github": student_data.get('GitHub', '#') if (student_data.get('GitHub', '').strip() and not student_data.get('GitHub', '').startswith('https://your-portfolio-site.com')) else '#',
            "slides": student_data.get('Presentation', '#') if (student_data.get('Presentation', '').strip() and not student_data.get('Presentation', '').startswith('https://your-portfolio-site.com')) else '#',
            "report": student_data.get('Report', '#') if (student_data.get('Report', '').strip() and not student_data.get('Report', '').startswith('https://your-portfolio-site.com')) else '#',
            "profilePage": f"profiles/{username}.html"
        }
        
        # Add optional fields if they exist
        optional_fields = ['Blog', 'Demo', 'Other']
        for field in optional_fields:
            if (field in student_data and 
                student_data[field] and 
                student_data[field].strip() and 
                student_data[field] != '#' and 
                not student_data[field].startswith('https://your-portfolio-site.com')):
                student_json[field.lower()] = student_data[field]
        
        course_json["students"].append(student_json)
    
    return course_json

def create_student_folder_structure(base_path, student_data, course_info):
    """
    Create unified folder structure for student (works across multiple courses):
    data/students/username/
    ├── profile.md (unified profile with all practica)
    ├── avatar.jpg
    ├── reports/
    │   ├── username_practicum1_report.pdf
    │   └── username_practicum2_report.pdf
    ├── presentations/
    │   ├── username_practicum1_slides.pdf
    │   └── username_practicum2_slides.pdf
    ├── assets/
    └── README.md
    """
    username = student_data['Username']
    
    # Create unified student directory (not course-specific)
    student_dir = base_path / 'data' / 'students' / username
    student_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    subdirs = ['reports', 'presentations', 'assets']
    for subdir in subdirs:
        (student_dir / subdir).mkdir(exist_ok=True)
    
    # Copy default avatar image to student directory if it doesn't exist
    avatar_source = base_path / 'data' / 'avatar.jpg'
    avatar_dest = student_dir / 'avatar.jpg'
    
    if avatar_source.exists() and not avatar_dest.exists():
        try:
            shutil.copy2(avatar_source, avatar_dest)
            print(f"    🖼️  Copied default avatar to {username}/")
        except Exception as e:
            print(f"    ⚠️  Warning: Could not copy avatar for {username}: {e}")
    elif avatar_dest.exists():
        print(f"    ✅ Avatar already exists for {username}")
    else:
        print(f"    ⚠️  Warning: Default avatar not found at {avatar_source}")
    
    # Copy example PDF files for students to replace
    example_pdf_source = base_path / 'data' / 'example_pdf.pdf'
    if example_pdf_source.exists():
        # Create example files with proper naming for students to replace
        example_files = [
            # CV file
            (student_dir / f'{username}_cv.pdf', 'CV'),
            # Practicum I files
            (student_dir / 'reports' / f'{username}_practicum1_report.pdf', 'Practicum I Report'),
            (student_dir / 'presentations' / f'{username}_practicum1_slides.pdf', 'Practicum I Presentation'),
            # Practicum II files  
            (student_dir / 'reports' / f'{username}_practicum2_report.pdf', 'Practicum II Report'),
            (student_dir / 'presentations' / f'{username}_practicum2_slides.pdf', 'Practicum II Presentation')
        ]
        
        for dest_file, file_type in example_files:
            if not dest_file.exists():
                try:
                    shutil.copy2(example_pdf_source, dest_file)
                    print(f"    📄 Copied example PDF as {file_type}: {dest_file.name}")
                except Exception as e:
                    print(f"    ⚠️  Warning: Could not copy example PDF for {file_type}: {e}")
    else:
        print(f"    ⚠️  Warning: Example PDF not found at {example_pdf_source}")
    
    # Handle profile.md creation/update
    profile_path = student_dir / 'profile.md'
    
    # Load existing profile if it exists
    existing_content, existing_practica = load_existing_profile(profile_path)
    
    # Create or update profile content
    if existing_content:
        profile_content = create_markdown_profile(student_data, course_info, existing_content, existing_practica)
        print(f"    📝 Updated profile.md for {username} with {course_info['course'].upper()}")
    else:
        profile_content = create_markdown_profile(student_data, course_info)
        print(f"    📝 Created profile.md for {username}")
    
    # Write profile content
    with open(profile_path, 'w', encoding='utf-8') as f:
        f.write(profile_content)
    
    # Create/update README.md
    readme_content = create_student_readme(student_data, course_info)
    readme_path = student_dir / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    return student_dir

def create_student_readme(student_data, course_info):
    """Create README with instructions for students - updated for unified profile"""
    username = student_data['Username']
    
    return f'''# {student_data['Student Name']} - Data Science Portfolio

## 📁 Unified Portfolio Structure

```
{username}/
├── profile.md          # Your unified profile (contains all practica)
├── avatar.jpg          # Your profile photo
├── reports/
│   ├── {username}_practicum1_report.pdf  # MSDS 692 report
│   └── {username}_practicum2_report.pdf  # MSDS 696 report
├── presentations/
│   ├── {username}_practicum1_slides.pdf  # MSDS 692 slides
│   └── {username}_practicum2_slides.pdf  # MSDS 696 slides
└── assets/
    └── (additional files)
```

## 🚀 Getting Started

1. **Edit your profile.md** - Contains ALL your practicum experiences
2. **Upload your avatar** - Add `avatar.jpg` (or `avatar.png`, `avatar.webp`)
3. **Upload reports** - Use consistent naming: `practicum1` for MSDS 692, `practicum2` for MSDS 696
4. **Upload presentations** - Use consistent naming convention
5. **Add any additional assets** - Use `assets/` folder for extra files

## 📋 Required Files

### Profile Photo
- **File name:** `avatar.jpg`, `avatar.png`, or `avatar.webp`
- **Size:** Recommended 400x400px or larger, square format
- **Format:** JPG, PNG, or WebP

### 📄 CV/Resume
- **Current file:** `{username}_cv.pdf` ⚠️ **REPLACE THIS**
- **Format:** PDF only
- **Note:** This is an example file - replace with your actual CV

### 📊 Practicum I Files (MSDS 692)
- **Report:** `reports/{username}_practicum1_report.pdf` ⚠️ **REPLACE THIS**
- **Slides:** `presentations/{username}_practicum1_slides.pdf` ⚠️ **REPLACE THIS**
- **Format:** PDF only
- **Note:** These are example files - replace with your actual project files

### 📊 Practicum II Files (MSDS 696)
- **Report:** `reports/{username}_practicum2_report.pdf` ⚠️ **REPLACE THIS**
- **Slides:** `presentations/{username}_practicum2_slides.pdf` ⚠️ **REPLACE THIS**
- **Format:** PDF only
- **Note:** These are example files - replace with your actual project files

### 📸 Profile Photo
- **File name:** `avatar.jpg`, `avatar.png`, or `avatar.webp`
- **Size:** Recommended 400x400px or larger, square format
- **Format:** JPG, PNG, or WebP
- **Note:** Replace the default avatar with your professional photo

## ✏️ Unified Profile Structure

Your `profile.md` file contains:
- Personal information (name, email, etc.)
- About Me section
- Skills and technologies
- **MSDS 692 - Practicum I** section
- **MSDS 696 - Practicum II** section (added automatically when you take the second course)
- Contact information

**Benefits of Unified Profile:**
- ✅ One profile to maintain
- ✅ Shows progression from Practicum I to II
- ✅ Employers see complete journey
- ✅ No duplicate information

## 🔗 Links to Update

Make sure to update these in your `profile.md`:
- GitHub repository URLs for both practica
- LinkedIn profile
- Personal website/portfolio
- Any demo/project links

## 📤 File Upload Tips

1. **Use consistent naming** - `practicum1` for MSDS 692, `practicum2` for MSDS 696
2. **One profile file** - All practicum info goes in `profile.md`
3. **Optimize file sizes** - compress large PDFs and images
4. **Test all links** in your profile.md file

## 🔄 Course Progression

**First time (MSDS 692):** Profile created with Practicum I section
**Second time (MSDS 696):** Profile updated to include Practicum II section

Your profile automatically evolves as you progress through the program!

## 🆘 Need Help?

- Check the main repository documentation
- Ask your instructor for guidance
- Review other students' profiles for examples

## 🔄 Auto-sync

Your profile will automatically sync to the main portfolio site when you:
1. Upload/update files in this folder
2. Edit your profile.md file
3. Push changes to the repository

---
*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''


def process_csv_file(csv_path, base_path, json_only=False):
    """
    Process CSV file and either:
    1. Generate JSON files for GitHub Actions (json_only=True)
    2. Create student folder structures (json_only=False, original behavior)
    """
    csv_file = Path(csv_path)
    
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return False
    
    # Parse course information from filename
    course_info = parse_course_code(csv_file.name)
    print(f"📊 Processing: {course_info['display_name']}")
    print(f"📁 Folder: {course_info['folder_name']}")
    
    # Required fields in CSV
    required_fields = ['Student Name', 'Email', 'Username', 'Project Title']
    optional_fields = ['GitHub', 'Presentation', 'Report', 'Blog', 'Other', 'Demo', 'Profile Page']
    
    students_processed = 0
    students_created = 0
    errors = []
    students_data = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate CSV headers
            if not all(field in reader.fieldnames for field in required_fields):
                missing = [field for field in required_fields if field not in reader.fieldnames]
                print(f"❌ Missing required columns: {missing}")
                return False
            
            print(f"✅ CSV validation passed")
            print(f"📋 Required fields: {required_fields}")
            print(f"📋 Optional fields: {[f for f in optional_fields if f in reader.fieldnames]}")
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Validate required fields
                    missing_fields = validate_csv_row(row, required_fields)
                    if missing_fields:
                        error_msg = f"Row {row_num}: Missing required fields: {missing_fields}"
                        print(f"⚠️  {error_msg}")
                        errors.append(error_msg)
                        continue
                    
                    # Clean email
                    row['Email'] = clean_email(row['Email'])
                    
                    # Generate fallback URLs for missing optional fields
                    username = row['Username']
                    profile_base = f"https://your-portfolio-site.com/profiles/{username}"
                    
                    for field in optional_fields:
                        if field not in row or not row[field].strip():
                            row[field] = generate_fallback_url(profile_base, field)
                    
                    # Store student data for JSON generation
                    students_data.append(row)
                    
                    if not json_only:
                        # Create student folder structure (original behavior)
                        student_dir = create_student_folder_structure(base_path, row, course_info)
                        
                        if student_dir:
                            students_created += 1
                            print(f"✅ Created: {row['Student Name']} ({username})")
                    else:
                        students_created += 1
                        print(f"✅ Processed: {row['Student Name']} ({username})")
                    
                    students_processed += 1
                    
                except Exception as e:
                    error_msg = f"Row {row_num}: Error processing {row.get('Student Name', 'Unknown')}: {str(e)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    continue
    
    except Exception as e:
        print(f"❌ Error reading CSV file: {str(e)}")
        return False
    
    # Generate JSON file (always generate unless explicitly disabled)
    json_filename = None
    should_generate_json = True  # Always generate JSON by default
    
    print(f"🔍 Generating JSON file: Found {len(students_data)} students")
    
    if should_generate_json and students_data:
        course_json = generate_course_json(students_data, course_info, csv_file)
        
        # Save JSON file in data directory (not root)
        json_filename = f"{course_info['year']}_{course_info['semester']}_{course_info['course']}.json"
        json_path = base_path / 'data' / json_filename
        
        # Ensure data directory exists
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(course_json, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Generated JSON: {json_path}")
        print(f"📊 JSON contains {len(course_json['students'])} students")
    elif not students_data:
        print(f"⚠️  No students data found for JSON generation")
        print(f"🔍 Debug info:")
        print(f"   - Students processed: {students_processed}")
        print(f"   - Errors: {len(errors)}")
        if errors:
            for error in errors:
                print(f"   - Error: {error}")
    
    # Create summary
    summary = {
        'course_info': course_info,
        'processed_at': datetime.now().isoformat(),
        'students_processed': students_processed,
        'students_created': students_created,
        'errors': errors,
        'csv_file': str(csv_file),
        'json_generated': json_only and json_filename is not None
    }
    
    # Save processing summary only if not json_only mode
    # if not json_only:
        # Save processing summary (keep course-specific summaries for tracking)
        # summary_path = base_path / 'data' / course_info['folder_name'] / '_processing_summary.json'
        # summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        # with open(summary_path, 'w', encoding='utf-8') as f:
            # json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Also save a unified summary
        # unified_summary_path = base_path / 'data' / 'students' / '_processing_summary.json'
        # unified_summary = {
        #     'last_processed': datetime.now().isoformat(),
        #     'note': 'Students are stored in unified folders under data/students/',
        #     'course_summaries': {
        #         course_info['folder_name']: summary
        #     }
        # }
        
        # Load existing unified summary if it exists
        # if unified_summary_path.exists():
        #     with open(unified_summary_path, 'r', encoding='utf-8') as f:
        #         existing_unified = json.load(f)
        #         if 'course_summaries' not in existing_unified:
        #             existing_unified['course_summaries'] = {}
        #         existing_unified['course_summaries'][course_info['folder_name']] = summary
        #         existing_unified['last_processed'] = datetime.now().isoformat()
        #         unified_summary = existing_unified
        
        # unified_summary_path.parent.mkdir(parents=True, exist_ok=True)
        # with open(unified_summary_path, 'w', encoding='utf-8') as f:
        #     json.dump(unified_summary, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n📊 Processing Summary:")
    print(f"   📁 Course: {course_info['display_name']}")
    print(f"   👥 Students processed: {students_processed}")
    
    if json_only:
        # GitHub Actions mode - JSON only
        print(f"   🔧 Mode: GitHub Actions (JSON only)")
        if json_filename:
            print(f"   📄 JSON generated: {json_filename}")
            print(f"   ✅ Students in JSON: {students_created}")
        else:
            print(f"   ❌ JSON generation failed - no student data found")
    else:
        # Terminal mode - Both folders and JSON
        print(f"   🔧 Mode: Terminal (Folders + JSON)")
        print(f"   ✅ Student folders created: {students_created}")
        print(f"   📂 Student profiles location: data/students/")
        if json_filename:
            print(f"   📄 JSON generated: {json_filename}")
            print(f"   🎯 Ready for HTML generation with sync script")
        else:
            print(f"   ❌ JSON generation failed")
    
    print(f"   ❌ Errors: {len(errors)}")
    
    if errors:
        print(f"\n⚠️  Errors encountered:")
        for error in errors:
            print(f"   • {error}")
    
    return True

def migrate_existing_folders(base_path):
    """
    Migrate existing course-specific folders to unified student structure
    Call this function to migrate from old structure to new unified structure
    """
    data_path = base_path / 'data'
    students_path = data_path / 'students'
    
    # Find existing course folders
    course_folders = []
    for item in data_path.iterdir():
        if item.is_dir() and item.name != 'students' and not item.name.startswith('_'):
            course_folders.append(item)
    
    if not course_folders:
        print("No existing course folders found to migrate.")
        return
    
    print(f"🔄 Found {len(course_folders)} course folders to migrate:")
    for folder in course_folders:
        print(f"   📁 {folder.name}")
    
    students_migrated = 0
    
    for course_folder in course_folders:
        print(f"\n📂 Processing {course_folder.name}...")
        
        for student_folder in course_folder.iterdir():
            if student_folder.is_dir() and not student_folder.name.startswith('_'):
                username = student_folder.name
                
                # Create unified student folder
                unified_student_path = students_path / username
                unified_student_path.mkdir(parents=True, exist_ok=True)
                
                # Copy files from old structure to new
                import shutil
                
                # Copy all files and subdirectories
                for item in student_folder.iterdir():
                    dest = unified_student_path / item.name
                    
                    if item.is_file():
                        if not dest.exists():
                            shutil.copy2(item, dest)
                            print(f"    📄 Copied {item.name}")
                        else:
                            print(f"    ⚠️  File {item.name} already exists in unified folder")
                    elif item.is_dir():
                        if not dest.exists():
                            shutil.copytree(item, dest)
                            print(f"    📁 Copied directory {item.name}")
                        else:
                            # Merge directory contents
                            for subitem in item.iterdir():
                                subdest = dest / subitem.name
                                if not subdest.exists():
                                    if subitem.is_file():
                                        shutil.copy2(subitem, subdest)
                                    else:
                                        shutil.copytree(subitem, subdest)
                
                students_migrated += 1
                print(f"    ✅ Migrated {username}")
    
    print(f"\n📊 Migration Summary:")
    print(f"   👥 Students migrated: {students_migrated}")
    print(f"   📂 New unified location: {students_path}")
    print(f"   📝 Old course folders preserved for backup")
    
    return True

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Process CSV files for Regis University Data Science Practicum')
    parser.add_argument('csv_file', nargs='?', help='Path to the CSV file to process')
    parser.add_argument('--base-path', '-b', default='.', help='Base path for the repository (default: current directory)')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Show what would be created without actually creating files')
    parser.add_argument('--migrate', '-m', action='store_true', help='Migrate existing course-specific folders to unified structure')
    parser.add_argument('--json-only', '-j', action='store_true', help='Generate JSON files for GitHub Actions instead of creating folders')
    
    args = parser.parse_args()
    
    base_path = Path(args.base_path)
    
    print("🎓 Regis University Data Science Practicum - CSV Processor")
    print("=" * 60)
    print(f"📁 Base path: {base_path.absolute()}")
    
    if args.migrate:
        print("🔄 Migration Mode - Converting to unified student structure")
        print("=" * 60)
        return 0 if migrate_existing_folders(base_path) else 1
    
    if not args.csv_file:
        print("❌ CSV file path is required unless using --migrate option")
        parser.print_help()
        return 1
    
    print(f"📄 CSV file: {args.csv_file}")
    
    if args.json_only:
        print("🤖 GitHub Actions Mode - Generating JSON files only")
        print("   📄 Creates JSON data files for automated workflows")
        print("   📂 No student folders created")
    elif args.dry_run:
        print("🔍 DRY RUN MODE - No files will be created")
    else:
        print("� Terminal Mode - Creating student folders + JSON files")
        print("   📂 Creates student folders with example files")
        print("   📄 Creates JSON data files")
        print("   🎯 Ready for HTML generation")
    
    print("=" * 60)
    
    if args.dry_run:
        print("🔍 This would process the CSV and show planned actions")
        return
    
    success = process_csv_file(args.csv_file, base_path, json_only=args.json_only)
    
    if success:
        print(f"\n🎉 Processing completed successfully!")
        if args.json_only:
            print(f"🤖 GitHub Actions: JSON files generated for automated workflows")
            print(f"🚀 Ready for automated portfolio generation")
        else:
            print(f"� Terminal: Student folders + JSON files created")
            print(f"📂 Student folders: data/students/")
            print(f"� JSON files: data/")
            print(f"🔄 Next step: Run sync script to generate HTML portfolios")
    else:
        print(f"\n❌ Processing failed!")
        return 1

if __name__ == "__main__":
    main()