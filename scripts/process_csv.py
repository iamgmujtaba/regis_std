#!/usr/bin/env python3
"""
Enhanced CSV Processing Script for Regis University Data Science Practicum
Processes CSV files to generate student folders and markdown profiles
"""

import os
import csv
import re
import json
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

def create_markdown_profile(student_data, course_info):
    """
    Create initial markdown profile from CSV data
    Students will enhance this later
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
    
    markdown_content = f'''---
name: "{name}"
firstName: "{first_name}"
lastName: "{last_name}"
email: "{email}"
username: "{username}"
github: "{username}"
linkedin: "{username}"
course: "{course_number}"
semester: "{course_info['semester'].title()} {course_info['year']}"
graduation: "May {int(course_info['year']) + 1}"
major: "Data Science"
degree: "Master of Science in Data Science"
university: "Regis University"
---

## About Me

I am a dedicated Data Science graduate student at Regis University, currently completing my {practicum_number} practicum experience. My focus is on applying data science techniques to solve real-world problems and gain practical experience in the field.

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

## {course_number} - Practicum {practicum_number}

**Title:** {project_title}

**Tags:** {', '.join(tags)}

**Abstract:** This project focuses on {project_title.lower()}. Please update this section with a detailed description of your project, methodology, and key findings.

**Key Achievements:**
- Please add your key project achievements
- Include quantifiable results where possible
- Highlight technical innovations or challenges overcome

**Technologies Used:** Please list the main technologies and tools used in your project

**Links:**
- GitHub Repository: [{github if github else 'Add your GitHub link'}]({github if github else '#'})
- Project Report: [Download Report](../reports/{username}_practicum{practicum_number.lower()}_report.pdf)
- Presentation Slides: [View Slides](../presentations/{username}_practicum{practicum_number.lower()}_slides.pdf)

*Please update the links above with your actual project URLs and ensure your PDF files are uploaded to the correct folders.*

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

def create_student_folder_structure(base_path, student_data, course_info):
    """
    Create folder structure for student:
    data/2025_summer_msds692/username/
    ├── profile.md
    ├── avatar.jpg (placeholder)
    ├── reports/
    ├── presentations/
    ├── assets/
    └── README.md
    """
    username = student_data['Username']
    folder_name = course_info['folder_name']
    
    # Create main student directory
    student_dir = base_path / 'data' / folder_name / username
    student_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    subdirs = ['reports', 'presentations', 'assets']
    for subdir in subdirs:
        (student_dir / subdir).mkdir(exist_ok=True)
    
    # Create profile.md
    profile_content = create_markdown_profile(student_data, course_info)
    profile_path = student_dir / 'profile.md'
    
    # Only create if doesn't exist (don't overwrite student edits)
    if not profile_path.exists():
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(profile_content)
        print(f"    📝 Created profile.md for {username}")
    else:
        print(f"    ⚠️  profile.md already exists for {username}, skipping...")
    
    # Create README.md for student instructions
    readme_content = create_student_readme(student_data, course_info)
    readme_path = student_dir / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    return student_dir

def create_student_readme(student_data, course_info):
    """Create README with instructions for students"""
    username = student_data['Username']
    course_number = "MSDS 692" if 'msds692' in course_info['course'].lower() else "MSDS 696"
    practicum_number = "I" if 'msds692' in course_info['course'].lower() else "II"
    
    return f'''# {student_data['Student Name']} - {course_number} Portfolio

## 📁 Folder Structure

```
{username}/
├── profile.md          # Your profile page content (edit this!)
├── avatar.jpg          # Your profile photo
├── reports/
│   └── {username}_practicum{practicum_number.lower()}_report.pdf
├── presentations/
│   └── {username}_practicum{practicum_number.lower()}_slides.pdf
└── assets/
    └── (additional files)
```

## 🚀 Getting Started

1. **Edit your profile.md** - Update with your actual information
2. **Upload your avatar** - Add `avatar.jpg` (or `avatar.png`, `avatar.webp`)
3. **Upload your report** - Add PDF to `reports/` folder
4. **Upload your presentation** - Add PDF to `presentations/` folder
5. **Add any additional assets** - Use `assets/` folder for extra files

## 📋 Required Files

### Profile Photo
- **File name:** `avatar.jpg`, `avatar.png`, or `avatar.webp`
- **Size:** Recommended 400x400px or larger, square format
- **Format:** JPG, PNG, or WebP

### Project Report  
- **File name:** `{username}_practicum{practicum_number.lower()}_report.pdf`
- **Location:** `reports/` folder
- **Format:** PDF only

### Presentation Slides
- **File name:** `{username}_practicum{practicum_number.lower()}_slides.pdf`  
- **Location:** `presentations/` folder
- **Format:** PDF only

## ✏️ Editing Your Profile

Your `profile.md` file contains:
- Personal information (name, email, etc.)
- About Me section
- Skills and technologies
- Project details and abstract
- Contact information

**Important:** Update all placeholder text with your actual information!

## 🔗 Links to Update

Make sure to update these in your `profile.md`:
- GitHub repository URLs
- LinkedIn profile
- Personal website/portfolio
- Any demo/project links

## 📤 File Upload Tips

1. **Keep file names consistent** with the naming convention above
2. **Use descriptive names** for files in the `assets/` folder
3. **Optimize file sizes** - compress large PDFs and images
4. **Test all links** in your profile.md file

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

def process_csv_file(csv_path, base_path):
    """
    Process CSV file and create student folder structures
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
                    
                    # Create student folder structure
                    student_dir = create_student_folder_structure(base_path, row, course_info)
                    
                    students_processed += 1
                    if student_dir:
                        students_created += 1
                        print(f"✅ Created: {row['Student Name']} ({username})")
                    
                except Exception as e:
                    error_msg = f"Row {row_num}: Error processing {row.get('Student Name', 'Unknown')}: {str(e)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    continue
    
    except Exception as e:
        print(f"❌ Error reading CSV file: {str(e)}")
        return False
    
    # Create summary
    summary = {
        'course_info': course_info,
        'processed_at': datetime.now().isoformat(),
        'students_processed': students_processed,
        'students_created': students_created,
        'errors': errors,
        'csv_file': str(csv_file)
    }
    
    # Save processing summary
    summary_path = base_path / 'data' / course_info['folder_name'] / '_processing_summary.json'
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n📊 Processing Summary:")
    print(f"   📁 Course: {course_info['display_name']}")
    print(f"   👥 Students processed: {students_processed}")
    print(f"   ✅ Folders created: {students_created}")
    print(f"   ❌ Errors: {len(errors)}")
    print(f"   📄 Summary saved: {summary_path}")
    
    if errors:
        print(f"\n⚠️  Errors encountered:")
        for error in errors:
            print(f"   • {error}")
    
    return True

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Process CSV files for Regis University Data Science Practicum')
    parser.add_argument('csv_file', help='Path to the CSV file to process')
    parser.add_argument('--base-path', '-b', default='.', help='Base path for the repository (default: current directory)')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Show what would be created without actually creating files')
    
    args = parser.parse_args()
    
    base_path = Path(args.base_path)
    
    print("🎓 Regis University Data Science Practicum - CSV Processor")
    print("=" * 60)
    print(f"📁 Base path: {base_path.absolute()}")
    print(f"📄 CSV file: {args.csv_file}")
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be created")
    
    print("=" * 60)
    
    if args.dry_run:
        print("🔍 This would process the CSV and show planned actions")
        return
    
    success = process_csv_file(args.csv_file, base_path)
    
    if success:
        print(f"\n🎉 Processing completed successfully!")
        print(f"📂 Student folders created in: data/")
        print(f"🔄 Run sync script next to generate HTML profiles")
    else:
        print(f"\n❌ Processing failed!")
        return 1

if __name__ == "__main__":
    main()