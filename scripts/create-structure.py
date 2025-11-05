import pandas as pd
import os
import sys
import glob
from pathlib import Path

def extract_course_code(csv_filename):
    """Extract course code from CSV filename"""
    # MSDS696_S71_Data Science Practicum II_GradesExport_2025-11-05-18-14.csv
    basename = os.path.basename(csv_filename)
    parts = basename.split('_')
    if len(parts) >= 2:
        return f"{parts[0].lower()}_{parts[1].lower()}"
    return "unknown_course"

def create_student_folders(csv_path):
    """Create folder structure based on CSV data"""
    
    # Read CSV file
    df = pd.read_csv(csv_path)
    
    # Extract course code from filename
    course_code = extract_course_code(csv_path)
    
    # Create base directory
    base_dir = Path(f"data/{course_code}")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Get active students - FIXED filtering logic
    print(f"📊 Total rows in CSV: {len(df)}")
    print(f"📊 Username column sample: {df['Username'].head().tolist()}")
    
    # Filter out rows with empty usernames or demo accounts
    # Remove the requirement for # prefix since your data doesn't have it
    students = df[
        df['Username'].notna() & 
        (df['Username'].str.len() > 0) &
        ~df['Username'].str.contains('demo', case=False, na=False)
    ]
    
    print(f"📊 Filtered students: {len(students)}")
    
    created_folders = []
    
    for _, student in students.iterrows():
        # Remove # if it exists, otherwise use username as-is
        username = str(student['Username']).replace('#', '').strip()
        first_name = str(student['First Name']).strip()
        last_name = str(student['Last Name']).strip()
        email = str(student['Email']).strip()
        
        # Skip if essential data is missing or is NaN
        if not username or first_name == 'nan' or last_name == 'nan' or email == 'nan':
            print(f"⚠️ Skipping student with missing data: {username} - {first_name} {last_name}")
            continue
        
        # Skip demo/test accounts
        if 'demo' in username.lower() or 'test' in username.lower():
            print(f"⚠️ Skipping demo/test account: {username}")
            continue
        
        print(f"🔄 Processing: {first_name} {last_name} ({username})")
        
        # Create student folder
        student_dir = base_dir / username
        student_dir.mkdir(exist_ok=True)
        
        # Create profile.md if it doesn't exist
        profile_path = student_dir / "profile.md"
        if not profile_path.exists():
            profile_content = f"""---
username: {username}
firstName: {first_name}
lastName: {last_name}
email: {email}
course: {course_code.upper()}
semester: Spring 2025
---

# {first_name} {last_name}

## About Me
*Edit this section to tell us about yourself, your background, and your interests in data science.*

## Skills
*List your technical skills, programming languages, tools, and frameworks you're familiar with.*

**Programming Languages:**
- Python
- R
- SQL

**Tools & Frameworks:**
- Pandas, NumPy, Scikit-learn
- Matplotlib, Seaborn
- Jupyter Notebooks

## Practicum I Project

**Title:** *Enter your project title*

**Abstract:** 
*Provide a brief overview of your project, the problem you're solving, and your approach.*

**Key Technologies:**
- Technology 1
- Technology 2
- Technology 3

**Key Achievements:**
- Achievement 1
- Achievement 2
- Achievement 3

**Links:**
- [GitHub Repository](#)
- [Project Report](project1_report.pdf)
- [Presentation Slides](project1_slides.pdf)

## Practicum II Project

**Title:** *Enter your project title*

**Abstract:** 
*Provide a brief overview of your project, the problem you're solving, and your approach.*

**Key Technologies:**
- Technology 1
- Technology 2
- Technology 3

**Key Achievements:**
- Achievement 1
- Achievement 2
- Achievement 3

**Links:**
- [GitHub Repository](#)
- [Project Report](project2_report.pdf)
- [Presentation Slides](project2_slides.pdf)

## Contact Information

**Email:** {email}
**LinkedIn:** [Your LinkedIn Profile](#)
**GitHub:** [Your GitHub Profile](#)
**Portfolio:** [Your Portfolio Website](#)

---
*This profile is part of the Regis University Data Science Practicum Program.*
"""
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(profile_content)
            print(f"  📝 Created profile.md for {username}")
        
        # Create README.md for the folder
        readme_path = student_dir / "README.md"
        if not readme_path.exists():
            readme_content = f"""# {first_name} {last_name} - Portfolio Files

This folder contains all portfolio files for **{first_name} {last_name}** ({username}).

## File Structure

- `profile.md` - Main profile information (edit this!)
- `avatar.jpg/png` - Profile photo
- `project1_report.pdf` - Practicum I project report
- `project1_slides.pdf` - Practicum I presentation slides
- `project2_report.pdf` - Practicum II project report  
- `project2_slides.pdf` - Practicum II presentation slides
- Additional project files and images

## Instructions for Students

1. **Edit `profile.md`** with your information
2. **Upload your profile photo** as `avatar.jpg` or `avatar.png`
3. **Upload project reports** as PDF files
4. **Upload presentation slides** as PDF files
5. **Add any additional images** or supplementary files

## File Guidelines

- **Images**: Use JPG or PNG format
- **Documents**: Use PDF format for reports and presentations
- **File Names**: Use clear, descriptive names
- **File Size**: Keep individual files under 25MB

Course: {course_code.upper()} | Semester: Spring 2025 | Student: {username}
"""
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"  📄 Created README.md for {username}")
        
        created_folders.append(f"{course_code}/{username}")
        print(f"✅ Created folder for {first_name} {last_name} ({username})")
    
    # Create course-level README
    course_readme = base_dir / "README.md"
    course_readme_content = f"""# {course_code.upper()} - Student Portfolios

This directory contains student portfolio folders for the {course_code.upper()} course.

## Students ({len(created_folders)})

"""
    
    for _, student in students.iterrows():
        username = str(student['Username']).replace('#', '').strip()
        first_name = str(student['First Name']).strip()
        last_name = str(student['Last Name']).strip()
        
        if (username and first_name != 'nan' and last_name != 'nan' 
            and 'demo' not in username.lower() and 'test' not in username.lower()):
            course_readme_content += f"- [{first_name} {last_name}](./{username}/) (`{username}`)\n"
    
    course_readme_content += f"""

## Structure

Each student folder contains:
- `profile.md` - Student profile and project information
- `avatar.jpg/png` - Profile photo
- Project reports and presentations (PDF)
- Supporting images and files

## Guidelines

- Students should only modify files in their own username folder
- Use clear, descriptive file names
- Keep files under 25MB each
- Use standard formats (JPG/PNG for images, PDF for documents)

Generated from: `{os.path.basename(csv_path)}`
Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(course_readme, 'w', encoding='utf-8') as f:
        f.write(course_readme_content)
    
    print(f"\n📊 Summary:")
    print(f"Course: {course_code.upper()}")
    print(f"Created {len(created_folders)} student folders")
    print(f"Students: {', '.join([folder.split('/')[-1] for folder in created_folders])}")
    print(f"CSV: {csv_path}")
    
    return created_folders

def main():
    if len(sys.argv) > 1 and sys.argv[1] != 'auto':
        csv_path = sys.argv[1]
    else:
        # Auto-detect CSV files
        csv_files = glob.glob('data/**/*.csv', recursive=True)
        if not csv_files:
            print("❌ No CSV files found in data/ directory")
            return
        csv_path = csv_files[0]  # Use the first CSV found
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    print(f"📁 Processing CSV: {csv_path}")
    created_folders = create_student_folders(csv_path)
    print(f"✅ Successfully created {len(created_folders)} student folders!")

if __name__ == "__main__":
    main()