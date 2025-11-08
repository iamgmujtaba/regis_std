#!/usr/bin/env python3
"""
Enhanced Sync Script for Regis University Data Science Practicum
Syncs student data from regis_std to main regis portfolio repository
Converts markdown profiles to HTML and organizes data by semester
"""

import os
import shutil
import json
import yaml
from pathlib import Path
import glob
from datetime import datetime
import re

def parse_markdown_profile(md_path):
    """Parse markdown profile and extract metadata and content"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract YAML front matter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            yaml_content = parts[1]
            md_content = parts[2].strip()
            try:
                metadata = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                print(f"    ⚠️  YAML parse error: {e}")
                metadata = {}
        else:
            metadata = {}
            md_content = content
    else:
        metadata = {}
        md_content = content
    
    return metadata, md_content

def clean_email(email):
    """Clean email by removing worldclass subdomain"""
    if not email:
        return email
    return email.replace('@worldclass.regis.edu', '@regis.edu')

def find_student_files(student_dir, course_code, username):
    """Find all student files and generate proper URLs"""
    files = {
        'avatar_url': None,
        'cv_url': None,
        'images': [],
        'pdfs': [],
        'reports': [],
        'presentations': []
    }
    
    # Base URL for raw GitHub content
    base_url = f"https://raw.githubusercontent.com/iamgmujtaba/regis_std/main/data/{course_code}/{username}"
    
    # Find avatar (priority: webp > jpg > png)
    for ext in ['webp', 'jpg', 'jpeg', 'png']:
        avatar_path = student_dir / f'avatar.{ext}'
        if avatar_path.exists():
            files['avatar_url'] = f"{base_url}/avatar.{ext}"
            print(f"    📸 Found avatar: avatar.{ext}")
            break
    
    # Find CV
    cv_patterns = ['cv.pdf', f'{username}_cv.pdf', 'resume.pdf', f'{username}_resume.pdf']
    for pattern in cv_patterns:
        cv_path = student_dir / pattern
        if cv_path.exists():
            files['cv_url'] = f"{base_url}/{pattern}"
            print(f"    📄 Found CV: {pattern}")
            break
    
    # Find reports
    reports_dir = student_dir / 'reports'
    if reports_dir.exists():
        for report_file in reports_dir.glob('*.pdf'):
            files['reports'].append({
                'name': report_file.name,
                'url': f"{base_url}/reports/{report_file.name}",
                'type': 'report'
            })
            print(f"    📊 Found report: {report_file.name}")
    
    # Find presentations
    presentations_dir = student_dir / 'presentations'
    if presentations_dir.exists():
        for pres_file in presentations_dir.glob('*.pdf'):
            files['presentations'].append({
                'name': pres_file.name,
                'url': f"{base_url}/presentations/{pres_file.name}",
                'type': 'presentation'
            })
            print(f"    � Found presentation: {pres_file.name}")
    
    # Find other PDFs in root directory
    for pdf_file in student_dir.glob('*.pdf'):
        files['pdfs'].append({
            'name': pdf_file.name,
            'url': f"{base_url}/{pdf_file.name}",
            'type': 'pdf'
        })
        print(f"    📄 Found PDF: {pdf_file.name}")
    
    # Find images
    for img_file in student_dir.glob('*.{jpg,jpeg,png,webp}'):
        if not img_file.name.startswith('avatar'):
            files['images'].append({
                'name': img_file.name,
                'url': f"{base_url}/{img_file.name}",
                'type': 'image'
            })
            print(f"    �️  Found image: {img_file.name}")
    
    return files

def parse_course_folder(folder_name):
    """
    Parse course folder name to extract course info
    2025_summer_msds692 -> {year: 2025, semester: summer, course: msds692}
    """
    parts = folder_name.split('_')
    
    if len(parts) >= 3:
        year = parts[0]
        semester = parts[1].lower()
        course = parts[2].lower()
        
        return {
            'year': year,
            'semester': semester,
            'course': course.upper(),
            'folder_name': folder_name,
            'display_name': f"{course.upper()} - {semester.title()} {year}",
            'is_practicum_1': 'msds692' in course.lower(),
            'is_practicum_2': 'msds696' in course.lower()
        }
    else:
        # Fallback parsing for legacy names
        return {
            'year': '2025',
            'semester': 'spring',
            'course': 'MSDS692',
            'folder_name': folder_name,
            'display_name': folder_name,
            'is_practicum_1': True,
            'is_practicum_2': False
        }

def parse_markdown_sections(content):
    """Parse markdown content into structured sections"""
    sections = {
        'about': '', 
        'skills': {}, 
        'practicum1': {}, 
        'practicum2': {}, 
        'contact': {},
        'experience': '',
        'achievements': []
    }
    
    lines = content.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.startswith('## '):
            # Save previous section
            if current_section and current_content:
                section_content = '\n'.join(current_content).strip()
                
                if current_section == 'about':
                    sections['about'] = section_content
                elif current_section == 'skills':
                    sections['skills'] = parse_skills_section(section_content)
                elif current_section in ['practicum1', 'practicum2']:
                    sections[current_section] = parse_project_section(section_content)
                elif current_section == 'contact':
                    sections['contact'] = parse_contact_section(section_content)
                elif current_section == 'experience':
                    sections['experience'] = section_content
                elif current_section == 'achievements':
                    sections['achievements'] = parse_achievements_section(section_content)
            
            # Start new section
            section_name = line_stripped[3:].strip().lower()
            current_content = []
            
            # Map section names (check more specific conditions first)
            if 'about' in section_name:
                current_section = 'about'
            elif 'skill' in section_name:
                current_section = 'skills'
            elif 'practicum ii' in section_name or 'msds 696' in section_name:
                current_section = 'practicum2'
            elif 'practicum i' in section_name or 'msds 692' in section_name:
                current_section = 'practicum1'
            elif 'contact' in section_name:
                current_section = 'contact'
            elif 'experience' in section_name:
                current_section = 'experience'
            elif 'achievement' in section_name or 'award' in section_name:
                current_section = 'achievements'
            else:
                current_section = None
        else:
            if current_section and line_stripped:
                current_content.append(line)
    
    # Save last section
    if current_section and current_content:
        section_content = '\n'.join(current_content).strip()
        if current_section == 'about':
            sections['about'] = section_content
        elif current_section == 'skills':
            sections['skills'] = parse_skills_section(section_content)
        elif current_section in ['practicum1', 'practicum2']:
            sections[current_section] = parse_project_section(section_content)
        elif current_section == 'contact':
            sections['contact'] = parse_contact_section(section_content)
    
    return sections

def parse_skills_section(skills_text):
    """Parse skills section into structured format"""
    skills = {}
    current_category = None
    
    for line in skills_text.split('\n'):
        line = line.strip()
        if line.startswith('**') and line.endswith(':**'):
            current_category = line[2:-3].strip()
            skills[current_category] = []
        elif line.startswith('- ') and current_category:
            skill = line[2:].strip()
            skills[current_category].append(skill)
    
    return skills

def parse_project_section(project_text):
    """Parse project section into structured data"""
    project = {
        'title': '',
        'tags': [],
        'abstract': '',
        'achievements': [],
        'technologies': '',
        'github': '#',
        'report': '#',
        'slides': '#',
        'demo': '#'
    }
    
    current_field = None
    
    for line in project_text.split('\n'):
        line = line.strip()
        
        if line.startswith('**Title:**'):
            project['title'] = line[10:].strip()
        elif line.startswith('**Tags:**'):
            tags = line[9:].strip()
            project['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        elif line.startswith('**Abstract:**'):
            project['abstract'] = line[13:].strip()
            current_field = 'abstract'
        elif line.startswith('**Technologies Used:**') or line.startswith('**Technologies:**'):
            project['technologies'] = line.split(':', 1)[1].strip()
        elif line.startswith('**Key Achievements:**'):
            current_field = 'achievements'
        elif line.startswith('**Links:**'):
            current_field = 'links'
        elif line.startswith('- '):
            if current_field == 'achievements':
                project['achievements'].append(line[2:].strip())
            elif current_field == 'links':
                link_text = line[2:].strip()
                # Parse various link formats
                if 'github' in link_text.lower():
                    match = re.search(r'\[(.*?)\]\((.*?)\)', link_text)
                    if match:
                        project['github'] = match.group(2)
                elif 'report' in link_text.lower():
                    match = re.search(r'\[(.*?)\]\((.*?)\)', link_text)
                    if match:
                        project['report'] = match.group(2)
                elif 'slide' in link_text.lower() or 'presentation' in link_text.lower():
                    match = re.search(r'\[(.*?)\]\((.*?)\)', link_text)
                    if match:
                        project['slides'] = match.group(2)
                elif 'demo' in link_text.lower():
                    match = re.search(r'\[(.*?)\]\((.*?)\)', link_text)
                    if match:
                        project['demo'] = match.group(2)
        elif current_field == 'abstract' and line and not line.startswith('**'):
            if project['abstract']:
                project['abstract'] += ' ' + line
            else:
                project['abstract'] = line
    
    return project

def parse_contact_section(contact_text):
    """Parse contact section with flexible format support"""
    contact = {
        'email': '',
        'linkedin': '#',
        'github': '#',
        'portfolio': '#'
    }
    
    for line in contact_text.split('\n'):
        line = line.strip()
        
        # Handle different markdown formats
        if 'email' in line.lower() and ('@' in line):
            # Extract email address
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', line)
            if email_match:
                contact['email'] = clean_email(email_match.group())
        
        elif 'linkedin' in line.lower():
            # Look for various LinkedIn patterns
            if '[' in line and ']' in line and '(' in line and ')' in line:
                # Markdown link format [text](url)
                match = re.search(r'\[.*?\]\((.*?)\)', line)
                if match and 'linkedin.com' in match.group(1):
                    contact['linkedin'] = match.group(1)
            else:
                # Look for raw LinkedIn URL
                linkedin_match = re.search(r'https?://[^\s]*linkedin\.com[^\s]*', line)
                if linkedin_match:
                    contact['linkedin'] = linkedin_match.group()
                
        elif 'github' in line.lower():
            # Look for various GitHub patterns  
            if '[' in line and ']' in line and '(' in line and ')' in line:
                # Markdown link format [text](url)
                match = re.search(r'\[.*?\]\((.*?)\)', line)
                if match and 'github.com' in match.group(1):
                    contact['github'] = match.group(1)
            else:
                # Look for raw GitHub URL
                github_match = re.search(r'https?://[^\s]*github\.com[^\s]*', line)
                if github_match:
                    contact['github'] = github_match.group()
        
        elif ('portfolio' in line.lower() or 'website' in line.lower()) and 'http' in line:
            # Look for portfolio/website URLs
            if '[' in line and ']' in line and '(' in line and ')' in line:
                # Markdown link format [text](url)  
                match = re.search(r'\[.*?\]\((.*?)\)', line)
                if match:
                    contact['portfolio'] = match.group(1)
            else:
                # Look for raw URL
                url_match = re.search(r'https?://[^\s]+', line)
                if url_match:
                    contact['portfolio'] = url_match.group()
    
    return contact

def parse_achievements_section(achievements_text):
    """Parse achievements section into list"""
    achievements = []
    for line in achievements_text.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            achievements.append(line[2:].strip())
    return achievements

def get_project_urls_from_json(username, is_practicum_1):
    """Get project URLs from the JSON data files and check for local files"""
    try:
        # First check for local PDF files in student directory
        student_dir = Path('data') / 'students' / username
        project_num = '1' if is_practicum_1 else '2'
        
        local_report = student_dir / 'reports' / f'{username}_practicum{project_num}_report.pdf'
        local_slides = student_dir / 'presentations' / f'{username}_practicum{project_num}_slides.pdf'
        local_cv = student_dir / f'{username}_cv.pdf'
        
        # Base URL for raw GitHub content
        base_url = f"https://raw.githubusercontent.com/iamgmujtaba/regis_std/main/data/students/{username}"
        
        # Check if local files exist and create URLs
        local_urls = {}
        if local_report.exists():
            local_urls['report'] = f"{base_url}/reports/{username}_practicum{project_num}_report.pdf"
            print(f"    📄 Found local report: {local_report.name}")
        
        if local_slides.exists():
            local_urls['slides'] = f"{base_url}/presentations/{username}_practicum{project_num}_slides.pdf"
            local_urls['presentation'] = local_urls['slides']  # alias
            print(f"    📄 Found local slides: {local_slides.name}")
        
        if local_cv.exists():
            local_urls['cv'] = f"{base_url}/{username}_cv.pdf"
            print(f"    📄 Found local CV: {local_cv.name}")
        
        # Now try to get URLs from JSON data
        json_filename = "2025_summer_msds692.json" if is_practicum_1 else "2025_summer_msds696.json"
        json_path = Path('data') / json_filename
        
        json_urls = {'github': '#', 'slides': '#', 'report': '#', 'demo': '#'}
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                course_data = json.load(f)
            
            # Find the student in the JSON data
            for student in course_data.get('students', []):
                if student.get('username') == username:
                    json_urls.update({
                        'github': student.get('github', '#'),
                        'slides': student.get('slides', '#'),
                        'report': student.get('report', '#'),
                        'demo': student.get('demo', '#'),
                        'presentation': student.get('slides', '#')  # alias for slides
                    })
                    break
        
        # Merge local and JSON URLs (local files take precedence for reports/slides)
        final_urls = {
            'github': json_urls.get('github', '#'),
            'demo': json_urls.get('demo', '#'),
            'slides': local_urls.get('slides', json_urls.get('slides', '#')),
            'presentation': local_urls.get('presentation', json_urls.get('presentation', '#')),
            'report': local_urls.get('report', json_urls.get('report', '#')),
            'cv': local_urls.get('cv', '#')
        }
        
        return final_urls
        
    except Exception as e:
        print(f"    ⚠️  Error reading data for {username}: {e}")
        return {'github': '#', 'slides': '#', 'report': '#', 'demo': '#', 'cv': '#'}

def auto_detect_project_files(student_files, course_info, username, project_section):
    """Get project URLs from JSON data (preferred) or fall back to file detection"""
    # First try to get URLs from JSON data
    json_urls = get_project_urls_from_json(username, course_info['is_practicum_1'])
    
    # If we got valid URLs from JSON, use them
    if any(url != '#' for url in json_urls.values()):
        print(f"    📄 Using URLs from JSON data for {username}")
        return json_urls
    
    # Fall back to original file detection logic
    print(f"    🔍 Falling back to file detection for {username}")
    project_urls = {
        'report': '#',
        'slides': '#'
    }
    
    # Determine if this is Practicum I or II
    is_practicum_1 = course_info['is_practicum_1']
    project_num = '1' if is_practicum_1 else '2'
    
    # Try to find report
    for report_file in student_files['reports']:
        filename = report_file['name'].lower()
        if (f'practicum{project_num}' in filename or 
            f'practicum_{project_num}' in filename or
            f'practicum {project_num}' in filename or
            'report' in filename):
            project_urls['report'] = report_file['url']
            break
    
    # Try to find presentation
    for pres_file in student_files['presentations']:
        filename = pres_file['name'].lower()
        if (f'practicum{project_num}' in filename or 
            f'practicum_{project_num}' in filename or
            f'practicum {project_num}' in filename or
            'slides' in filename or
            'presentation' in filename):
            project_urls['slides'] = pres_file['url']
            break
    
    # Use URLs from markdown if available, otherwise use auto-detected
    final_urls = {
        'report': project_section.get('report', '#') if project_section.get('report', '#') != '#' else project_urls['report'],
        'slides': project_section.get('slides', '#') if project_section.get('slides', '#') != '#' else project_urls['slides'],
        'github': project_section.get('github', '#'),
        'demo': project_section.get('demo', '#'),
        'presentation': project_section.get('slides', '#')  # alias for slides
    }
    
    return final_urls

def create_html_page(student_data, course_info, target_dir, markdown_content, metadata, student_files):
    """Create enhanced HTML page in the student's own directory and optionally in profiles"""
    username = student_data['username']
    name = metadata.get('name', student_data.get('name', 'Student Name'))
    email = clean_email(metadata.get('email', student_data.get('email', 'student@regis.edu')))
    
    # Parse markdown sections
    sections = parse_markdown_sections(markdown_content)
    
    # Student's directory paths
    local_student_dir = Path('data/students') / username
    target_student_dir = target_dir / 'students' / username if target_dir != Path('data') else local_student_dir
    
    # Also create in profiles directory for GitHub Pages
    profiles_dir = target_dir.parent / 'profiles' if target_dir != Path('data') else None
    
    # Generate project HTML for ALL practicum experiences
    projects_html = ""
    
    # Check for MSDS692 (Practicum I)
    if sections.get('practicum1') and sections['practicum1'].get('title'):
        practicum1_course_info = {
            'course': 'MSDS692',
            'is_practicum_1': True,
            'semester': 'Summer 2025'
        }
        practicum1_urls = auto_detect_project_files(student_files, practicum1_course_info, username, sections['practicum1'])
        practicum1_html = generate_enhanced_project_html(sections['practicum1'], "MSDS 692 - Practicum I", practicum1_course_info, practicum1_urls)
        projects_html += practicum1_html
    
    # Check for MSDS696 (Practicum II)
    if sections.get('practicum2') and sections['practicum2'].get('title'):
        practicum2_course_info = {
            'course': 'MSDS696',
            'is_practicum_1': False,
            'semester': 'Summer 2025'
        }
        practicum2_urls = auto_detect_project_files(student_files, practicum2_course_info, username, sections['practicum2'])
        practicum2_html = generate_enhanced_project_html(sections['practicum2'], "MSDS 696 - Practicum II", practicum2_course_info, practicum2_urls)
        projects_html += practicum2_html
    
    # If no projects found, show default message
    if not projects_html:
        projects_html = '''
        <div class="bg-white rounded-lg shadow-lg p-8 text-center">
            <div class="bg-gray-100 rounded-lg p-8">
                <i class="fas fa-graduation-cap text-4xl text-gray-400 mb-4"></i>
                <h3 class="text-2xl font-bold text-gray-600 mb-4">Data Science Practicum Projects</h3>
                <p class="text-gray-500">Project information will be available soon.</p>
                <small class="text-gray-400 block mt-2">Please update your profile.md with project details</small>
            </div>
        </div>
        '''
    
    # Use the combined projects HTML
    project_html = projects_html
    
    # Generate skills and other sections
    skills_html = generate_skills_html(sections['skills'])
    about_html = format_about_text(sections['about'])
    contact_html = generate_contact_html(sections['contact'], email)
    
    # Use avatar URL or create fallback
    avatar_url = student_files['avatar_url'] or f"https://via.placeholder.com/200x200/1e40af/ffffff?text={name[0] if name else 'S'}"
    
    # CV URL - try to get from local files or JSON data
    cv_url = '#'
    if sections.get('practicum1'):
        practicum1_urls = auto_detect_project_files(student_files, {'is_practicum_1': True}, username, sections['practicum1'])
        cv_url = practicum1_urls.get('cv', cv_url)
    if cv_url == '#' and sections.get('practicum2'):
        practicum2_urls = auto_detect_project_files(student_files, {'is_practicum_1': False}, username, sections['practicum2'])
        cv_url = practicum2_urls.get('cv', cv_url)
    if cv_url == '#':
        cv_url = student_files['cv_url'] or '#'
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{name} - Regis University Data Science Student Portfolio">
    <title>{name} - Regis University Data Science Portfolio</title>
    
    <!-- Favicon -->
    <link rel="icon" type="image/png" href="../assets/img/favicon.png">
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Custom Styles -->
    <link rel="stylesheet" href="../assets/css/style.css">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: '#1e40af',
                        secondary: '#7c3aed',
                        accent: '#06b6d4',
                    }}
                }}
            }}
        }}
    </script>
</head>
<body class="bg-gray-50">
    <!-- Navigation Bar -->
    <nav class="bg-white shadow-lg sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="flex items-center">
                    <i class="fas fa-user-graduate text-primary text-2xl mr-3"></i>
                    <span class="font-bold text-xl text-gray-800">Regis University Portfolio</span>
                </div>
                <div class="hidden md:flex space-x-6">
                    <a href="../index.html" class="text-gray-700 hover:text-primary transition duration-300">
                        <i class="fas fa-home mr-1"></i> Home
                    </a>
                    <a href="#about" class="text-gray-700 hover:text-primary transition duration-300">About</a>
                    <a href="#projects" class="text-gray-700 hover:text-primary transition duration-300">Projects</a>
                    <a href="#contact" class="text-gray-700 hover:text-primary transition duration-300">Contact</a>
                </div>
                <div class="md:hidden">
                    <button id="mobile-menu-button" class="text-gray-700 hover:text-primary">
                        <i class="fas fa-bars text-2xl"></i>
                    </button>
                </div>
            </div>
        </div>
        <!-- Mobile Menu -->
        <div id="mobile-menu" class="hidden md:hidden bg-white border-t">
            <div class="px-2 pt-2 pb-3 space-y-1">
                <a href="../index.html" class="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">
                    <i class="fas fa-home mr-1"></i> Home
                </a>
                <a href="#about" class="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">About</a>
                <a href="#projects" class="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">Projects</a>
                <a href="#contact" class="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">Contact</a>
            </div>
        </div>
    </nav>

    <!-- Hero/Profile Section -->
    <section class="bg-gradient-to-r from-primary to-secondary py-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex flex-col md:flex-row items-center justify-center gap-8">
                <!-- Profile Photo -->
                <div class="flex-shrink-0">
                    <div class="w-48 h-48 rounded-full overflow-hidden border-4 border-white shadow-2xl bg-white">
                        <img src="{avatar_url}" 
                             alt="{name}" 
                             class="w-full h-full object-cover"
                             onerror="this.src='https://via.placeholder.com/200x200/1e40af/ffffff?text={name[0] if name else 'S'}'">
                    </div>
                </div>
                
                <!-- Profile Info -->
                <div class="text-center md:text-left text-white">
                    <h1 class="text-4xl md:text-5xl font-bold mb-2">{name}</h1>
                    <p class="text-xl text-blue-100 mb-2">Data Science Graduate Student</p>
                    <p class="text-lg text-blue-200 mb-4">Regis University | {course_info['course']}</p>
                    
                    <!-- Social Links -->
                    <div class="flex justify-center md:justify-start space-x-4 mb-4">
                        <a href="{sections['contact'].get('github', '#')}" 
                           target="_blank"
                           class="w-10 h-10 bg-white text-primary rounded-full flex items-center justify-center hover:bg-blue-50 transition duration-300">
                            <i class="fab fa-github text-xl"></i>
                        </a>
                        <a href="{sections['contact'].get('linkedin', '#')}" 
                           target="_blank"
                           class="w-10 h-10 bg-white text-primary rounded-full flex items-center justify-center hover:bg-blue-50 transition duration-300">
                            <i class="fab fa-linkedin text-xl"></i>
                        </a>
                        <a href="mailto:{email}" 
                           class="w-10 h-10 bg-white text-primary rounded-full flex items-center justify-center hover:bg-blue-50 transition duration-300">
                            <i class="fas fa-envelope text-xl"></i>
                        </a>
                        <a href="{cv_url}" 
                           target="_blank"
                           class="w-10 h-10 bg-white text-primary rounded-full flex items-center justify-center hover:bg-blue-50 transition duration-300 {'opacity-50 cursor-not-allowed' if cv_url == '#' else ''}">
                            <i class="fas fa-file-pdf text-xl"></i>
                        </a>
                    </div>
                    
                    <!-- Quick Links -->
                    <div class="flex flex-wrap justify-center md:justify-start gap-3">
                        <a href="{cv_url}" 
                           target="_blank"
                           class="{'bg-white text-primary' if cv_url != '#' else 'bg-gray-300 text-gray-600 cursor-not-allowed'} px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition duration-300 inline-flex items-center">
                            <i class="fas fa-download mr-2"></i> Download CV
                        </a>
                        <a href="#contact" 
                           class="bg-transparent border-2 border-white text-white px-4 py-2 rounded-lg font-semibold hover:bg-white hover:text-primary transition duration-300 inline-flex items-center">
                            <i class="fas fa-paper-plane mr-2"></i> Contact Me
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="py-16 bg-white">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-4 text-center">About Me</h2>
            <div class="w-20 h-1 bg-primary mx-auto mb-8"></div>
            
            <div class="prose prose-lg max-w-none text-gray-700">
                {about_html}
            </div>

            <!-- Skills Section -->
            <div class="mt-12">
                <h3 class="text-2xl font-bold text-gray-900 mb-6 text-center">Technical Skills</h3>
                {skills_html}
            </div>
        </div>
    </section>

    <!-- Projects Section -->
    <section id="projects" class="py-16 bg-gray-50">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-4 text-center">Data Science Practicum Projects</h2>
            <div class="w-20 h-1 bg-primary mx-auto mb-12"></div>

            {project_html}
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="py-16 bg-white">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-4 text-center">Get In Touch</h2>
            <div class="w-20 h-1 bg-primary mx-auto mb-12"></div>
            {contact_html}
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p class="mb-2">&copy; 2025 {name}. All rights reserved.</p>
            <p class="text-gray-400 text-sm">Regis University Data Science Practicum Portfolio | Powered by GitHub Pages</p>
            <div class="mt-4">
                <a href="../index.html" class="text-gray-400 hover:text-white transition mx-2">
                    <i class="fas fa-home mr-1"></i> Back to Main Page
                </a>
            </div>
        </div>
    </footer>

    <!-- Mobile Menu Script -->
    <script>
        document.getElementById('mobile-menu-button').addEventListener('click', function() {{
            const menu = document.getElementById('mobile-menu');
            menu.classList.toggle('hidden');
        }});

        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    // Close mobile menu if open
                    document.getElementById('mobile-menu').classList.add('hidden');
                }}
            }});
        }});
    </script>
</body>
</html>'''
    
    # Write the HTML file in the student's local directory
    local_html_file = local_student_dir / f'{username}.html'
    with open(local_html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"    🌐 Created local HTML: students/{username}/{username}.html")
    
    # Also copy to profiles directory for GitHub Pages (if target is different)
    if profiles_dir:
        profiles_dir.mkdir(exist_ok=True)
        profiles_html_file = profiles_dir / f'{username}.html'
        with open(profiles_html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"    🌐 Created profile HTML: profiles/{username}.html")
        return f'profiles/{username}.html'
    
    return f'students/{username}/{username}.html'
    """Generate project HTML with proper PDF links"""
    if not project_data or not project_data.get('title'):
        # Default project template
        return f'''
        <div class="bg-white rounded-lg shadow-lg overflow-hidden mb-8 border border-gray-200 hover:shadow-xl transition duration-300">
            <div class="bg-gradient-to-r from-{gradient_color} to-blue-600 px-6 py-4">
                <h3 class="text-2xl font-bold text-white flex items-center">
                    <i class="fas fa-project-diagram mr-3"></i>
                    {title} Project
                </h3>
            </div>
            <div class="p-6">
                <h4 class="text-xl font-bold text-gray-900 mb-3">
                    [Edit your profile.md to add {title.lower()} project details]
                </h4>
                
                <div class="mb-4">
                    <span class="inline-block bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full mr-2">
                        <i class="fas fa-tag mr-1"></i> Add Tags
                    </span>
                </div>

                <p class="text-gray-700 mb-4 leading-relaxed">
                    <strong>Abstract:</strong> Please edit your profile.md file to add your project abstract and details.
                </p>

                <div class="flex flex-wrap gap-3 mt-6">
                    <a href="#" class="inline-flex items-center px-4 py-2 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed">
                        <i class="fab fa-github mr-2"></i> View Code
                    </a>
                    <a href="#" class="inline-flex items-center px-4 py-2 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed">
                        <i class="fas fa-file-pdf mr-2"></i> Read Report
                    </a>
                    <a href="#" class="inline-flex items-center px-4 py-2 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed">
                        <i class="fas fa-presentation mr-2"></i> View Slides
                    </a>
                </div>
            </div>
        </div>'''
    
    # Generate tags HTML
    tags_html = ''
    for tag in project_data.get('tags', []):
        color = 'blue' if 'Python' in tag else 'green' if 'Data' in tag else 'purple'
        tags_html += f'''
        <span class="inline-block bg-{color}-100 text-{color}-800 text-xs font-semibold px-3 py-1 rounded-full mr-2">
            <i class="fas fa-tag mr-1"></i> {tag}
        </span>'''
    
    # Generate achievements HTML
    achievements_html = ''
    for achievement in project_data.get('achievements', []):
        achievements_html += f'<li>{achievement}</li>'
    
    # Auto-detect PDF files if not specified in markdown
    report_url = project_data.get('report', '#')
    slides_url = project_data.get('slides', '#')
    
    # Try to find project-specific PDFs
    project_num = '1' if 'practicum i' in title.lower() else '2'
    base_url = f"https://raw.githubusercontent.com/iamgmujtaba/regis_std/main/data/{course_code}/{username}"
    
    # Look for common report naming patterns
    if report_url == '#':
        report_patterns = [
            f'practicum{project_num}_report.pdf',
            f'project{project_num}_report.pdf',
            f'practicum_{project_num}_report.pdf',
            'report.pdf'
        ]
        for pattern in report_patterns:
            for pdf in student_files['pdfs']:
                if pattern in pdf['name'].lower():
                    report_url = pdf['url']
                    break
            if report_url != '#':
                break
    
    # Look for common slides naming patterns
    if slides_url == '#':
        slides_patterns = [
            f'practicum{project_num}_slides.pdf',
            f'practicum{project_num}_presentation.pdf',
            f'project{project_num}_slides.pdf',
            'slides.pdf',
            'presentation.pdf'
        ]
        for pattern in slides_patterns:
            for pdf in student_files['pdfs']:
                if pattern in pdf['name'].lower():
                    slides_url = pdf['url']
                    break
            if slides_url != '#':
                break
    
    # Generate button classes based on availability
    github_class = "bg-gray-900 text-white hover:bg-gray-800" if project_data.get('github', '#') != '#' else "bg-gray-300 text-gray-600 cursor-not-allowed"
    report_class = "bg-primary text-white hover:bg-blue-800" if report_url != '#' else "bg-gray-300 text-gray-600 cursor-not-allowed"
    slides_class = "bg-secondary text-white hover:bg-purple-800" if slides_url != '#' else "bg-gray-300 text-gray-600 cursor-not-allowed"
    demo_class = "bg-accent text-white hover:bg-cyan-700" if project_data.get('demo', '#') != '#' else "bg-gray-300 text-gray-600 cursor-not-allowed"
    
    return f'''
    <div class="bg-white rounded-lg shadow-lg overflow-hidden mb-8 border border-gray-200 hover:shadow-xl transition duration-300">
        <div class="bg-gradient-to-r from-{gradient_color} to-blue-600 px-6 py-4">
            <h3 class="text-2xl font-bold text-white flex items-center">
                <i class="fas fa-project-diagram mr-3"></i>
                {title} Project
            </h3>
        </div>
        <div class="p-6">
            <h4 class="text-xl font-bold text-gray-900 mb-3">
                {project_data.get('title', f'{title} Project')}
            </h4>
            
            <div class="mb-4">
                {tags_html}
            </div>

            <p class="text-gray-700 mb-4 leading-relaxed">
                <strong>Abstract:</strong> {project_data.get('abstract', 'Please add project abstract in your profile.md file.')}
            </p>

            {"<div class='border-t border-gray-200 pt-4 mt-4'><h5 class='font-semibold text-gray-900 mb-3'>Key Achievements:</h5><ul class='list-disc list-inside space-y-2 text-gray-700 mb-4'>" + achievements_html + "</ul></div>" if achievements_html else ""}

            <div class="flex flex-wrap gap-3 mt-6">
                <a href="{project_data.get('github', '#')}" 
                   {"target='_blank'" if project_data.get('github', '#') != '#' else ""}
                   class="inline-flex items-center px-4 py-2 {github_class} rounded-lg transition duration-300">
                    <i class="fab fa-github mr-2"></i> View Code
                </a>
                <a href="{report_url}" 
                   {"target='_blank'" if report_url != '#' else ""}
                   class="inline-flex items-center px-4 py-2 {report_class} rounded-lg transition duration-300">
                    <i class="fas fa-file-pdf mr-2"></i> Read Report
                </a>
                <a href="{slides_url}" 
                   {"target='_blank'" if slides_url != '#' else ""}
                   class="inline-flex items-center px-4 py-2 {slides_class} rounded-lg transition duration-300">
                    <i class="fas fa-presentation mr-2"></i> View Slides
                </a>
                {"<a href='" + project_data.get('demo', '#') + "' target='_blank' class='inline-flex items-center px-4 py-2 " + demo_class + " rounded-lg transition duration-300'><i class='fas fa-external-link-alt mr-2'></i> Live Demo</a>" if project_data.get('demo', '#') != '#' else ""}
            </div>
        </div>
    </div>'''

def format_about_text(about_text):
    """Format about text as HTML paragraphs"""
    if not about_text:
        return '''<p class="text-lg leading-relaxed mb-4">
            I am a dedicated Data Science student at Regis University, currently completing my practicum 
            experience. Please edit your profile.md file to add information about yourself.
        </p>'''
    
    paragraphs = about_text.split('\n\n')
    html = ''
    for paragraph in paragraphs:
        if paragraph.strip():
            html += f'<p class="text-lg leading-relaxed mb-4">{paragraph.strip()}</p>\n'
    
    return html

def generate_skills_html(skills_dict):
    """Generate skills HTML from parsed skills"""
    if not skills_dict:
        return '''<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg text-center border border-blue-200">
                <i class="fas fa-code text-primary text-3xl mb-2"></i>
                <p class="font-semibold">Programming</p>
                <p class="text-sm text-gray-600">Python, R, SQL</p>
            </div>
            <div class="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg text-center border border-green-200">
                <i class="fas fa-laptop-code text-green-600 text-3xl mb-2"></i>
                <p class="font-semibold">Data Analysis</p>
                <p class="text-sm text-gray-600">Pandas, NumPy</p>
            </div>
            <div class="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg text-center border border-purple-200">
                <i class="fas fa-chart-bar text-purple-600 text-3xl mb-2"></i>
                <p class="font-semibold">Visualization</p>
                <p class="text-sm text-gray-600">Matplotlib, Seaborn</p>
            </div>
            <div class="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg text-center border border-orange-200">
                <i class="fas fa-brain text-orange-600 text-3xl mb-2"></i>
                <p class="font-semibold">Machine Learning</p>
                <p class="text-sm text-gray-600">Scikit-learn</p>
            </div>
        </div>'''
    
    # Map skill categories to icons and colors
    skill_icons = {
        'Programming Languages': ('fas fa-code', 'blue'),
        'Tools & Frameworks': ('fas fa-tools', 'green'),
        'Databases': ('fas fa-database', 'purple'),
        'Machine Learning': ('fas fa-brain', 'orange'),
        'Web Development': ('fas fa-laptop-code', 'indigo'),
        'Data Science': ('fas fa-chart-bar', 'red')
    }
    
    html = '<div class="grid grid-cols-2 md:grid-cols-4 gap-4">'
    
    for category, skills_list in skills_dict.items():
        icon, color = skill_icons.get(category, ('fas fa-star', 'gray'))
        skills_text = ', '.join(skills_list[:3])  # Show first 3 skills
        
        html += f'''
        <div class="bg-gradient-to-br from-{color}-50 to-{color}-100 p-4 rounded-lg text-center border border-{color}-200">
            <i class="{icon} text-{color}-600 text-3xl mb-2"></i>
            <p class="font-semibold">{category}</p>
            <p class="text-sm text-gray-600">{skills_text}</p>
        </div>'''
    
    html += '</div>'
    return html

def generate_contact_html(contact_data, email):
    """Generate contact HTML from parsed contact data"""
    return f'''
    <div class="grid md:grid-cols-2 gap-8">
        <!-- Contact Info -->
        <div>
            <h3 class="text-xl font-semibold mb-4">Contact Information</h3>
            <div class="space-y-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                            <i class="fas fa-envelope text-white"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="font-semibold">Email</p>
                        <a href="mailto:{email}" class="text-primary hover:underline">
                            {email}
                        </a>
                    </div>
                </div>

                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="w-10 h-10 bg-secondary rounded-lg flex items-center justify-center">
                            <i class="fab fa-linkedin text-white"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="font-semibold">LinkedIn</p>
                        <a href="{contact_data.get('linkedin', '#')}" 
                           target="_blank"
                           class="text-primary hover:underline">
                            {"LinkedIn Profile" if contact_data.get('linkedin', '#') != '#' else "Add LinkedIn in profile.md"}
                        </a>
                    </div>
                </div>

                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center">
                            <i class="fab fa-github text-white"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="font-semibold">GitHub</p>
                        <a href="{contact_data.get('github', '#')}" 
                           target="_blank"
                           class="text-primary hover:underline">
                            {"GitHub Profile" if contact_data.get('github', '#') != '#' else "Add GitHub in profile.md"}
                        </a>
                    </div>
                </div>

                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="w-10 h-10 bg-accent rounded-lg flex items-center justify-center">
                            <i class="fas fa-globe text-white"></i>
                        </div>
                    </div>
                    <div class="ml-4">
                        <p class="font-semibold">Portfolio</p>
                        <a href="{contact_data.get('portfolio', '#')}" 
                           target="_blank"
                           class="text-primary hover:underline">
                            {"Personal Website" if contact_data.get('portfolio', '#') != '#' else "Add portfolio in profile.md"}
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Quick Message Card -->
        <div class="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-lg border border-blue-200">
            <h3 class="text-xl font-semibold mb-4">Send a Message</h3>
            <p class="text-gray-700 mb-4">
                Feel free to reach out for collaboration opportunities, questions about my projects, 
                or just to connect!
            </p>
            <a href="mailto:{email}?subject=Hello%20from%20your%20portfolio" 
               class="block w-full bg-primary text-white text-center py-3 rounded-lg font-semibold hover:bg-blue-800 transition duration-300">
                <i class="fas fa-paper-plane mr-2"></i> Send Email
            </a>
            
            <div class="mt-6 pt-6 border-t border-blue-200">
                <p class="text-sm text-gray-600 text-center mb-3">Connect on social media:</p>
                <div class="flex justify-center space-x-4">
                    <a href="{contact_data.get('github', '#')}" 
                       target="_blank"
                       class="w-10 h-10 bg-gray-900 text-white rounded-full flex items-center justify-center hover:bg-gray-800 transition">
                        <i class="fab fa-github"></i>
                    </a>
                    <a href="{contact_data.get('linkedin', '#')}" 
                       target="_blank"
                       class="w-10 h-10 bg-blue-700 text-white rounded-full flex items-center justify-center hover:bg-blue-800 transition">
                        <i class="fab fa-linkedin"></i>
                    </a>
                    <a href="mailto:{email}" 
                       class="w-10 h-10 bg-red-600 text-white rounded-full flex items-center justify-center hover:bg-red-700 transition">
                        <i class="fas fa-envelope"></i>
                    </a>
                </div>
            </div>
        </div>
    </div>'''

def sync_student_data():
    """Sync student data and create HTML profiles from unified student directory"""
    
    # Paths - check if we're running in GitHub Actions or locally
    source_dir = Path('data')
    target_dir = Path('regis/data') if Path('regis').exists() else Path('data')
    
    if not source_dir.exists():
        print("❌ Source data directory not found")
        return
    
    print(f"📁 Processing unified student data from: {source_dir}")
    print(f"📁 Syncing to: {target_dir}")
    
    # Ensure target directories exist
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir.parent / 'profiles').mkdir(exist_ok=True)
    
    # Process unified student directory structure
    students_dir = source_dir / 'students'
    if not students_dir.exists():
        print(f"❌ Students directory not found: {students_dir}")
        return
    
    print(f"🔄 Processing unified student directory: {students_dir}")
    
    # Create separate collections for each course
    msds692_students = []
    msds696_students = []
    
    # Process each student in the unified directory
    for student_dir in students_dir.glob('*/'):
        if not student_dir.is_dir():
            continue
            
        username = student_dir.name
        profile_path = student_dir / 'profile.md'
        
        print(f"  👤 Processing student: {username}")
        
        if profile_path.exists():
            metadata, content = parse_markdown_profile(profile_path)
            
            # Parse the content to see which courses this student is in
            parsed_sections = parse_markdown_sections(content)
            
            # Find all student files (images, PDFs) in unified directory
            student_files = find_student_files(student_dir, 'students', username)
            
            # Create base student data entry
            base_student_data = {
                'username': username,
                'name': f"{metadata.get('firstName', '')} {metadata.get('lastName', '')}".strip() or username,
                'email': metadata.get('email', ''),
                'semester': metadata.get('semester', 'Spring 2025'),
                'profilePath': f'regis_std/data/students/{username}/profile.md',
                'avatarPath': student_files['avatar_url'],  # Direct URL
                'files': student_files['pdfs'] + student_files['images']
            }
            
            # Check if student has MSDS692 content
            if parsed_sections.get('practicum1'):
                practicum1_data = base_student_data.copy()
                practicum1_data.update({
                    'course': '2025_summer_msds692',
                    'projects': []
                })
                
                # Create HTML page for MSDS692
                course_info_692 = {
                    'course': 'MSDS692', 
                    'is_practicum_1': True, 
                    'semester': 'Summer 2025'
                }
                html_path = create_html_page(practicum1_data, course_info_692, target_dir, content, metadata, student_files)
                practicum1_data['profilePage'] = html_path
                
                msds692_students.append(practicum1_data)
                print(f"    ✅ Added to MSDS692: {base_student_data['name']} ({username})")
            
            # Check if student has MSDS696 content  
            if parsed_sections.get('practicum2'):
                practicum2_data = base_student_data.copy()
                practicum2_data.update({
                    'course': '2025_summer_msds696',
                    'projects': []
                })
                
                # Create HTML page for MSDS696
                course_info_696 = {
                    'course': 'MSDS696', 
                    'is_practicum_1': False, 
                    'semester': 'Summer 2025'
                }
                html_path = create_html_page(practicum2_data, course_info_696, target_dir, content, metadata, student_files)
                practicum2_data['profilePage'] = html_path
                
                msds696_students.append(practicum2_data)
                print(f"    ✅ Added to MSDS696: {base_student_data['name']} ({username})")
                
        else:
            print(f"    ⚠️  No profile.md found for {username}")
    
    # Create separate JSON files for each course
    courses_data = [
        ('2025_summer_msds692', msds692_students, 'MSDS692'),
        ('2025_summer_msds696', msds696_students, 'MSDS696')
    ]
    
    for course_code, course_students, course_display in courses_data:
        if course_students:  # Only create JSON if there are students
            # Create JSON in local data directory
            local_json_path = Path('data') / f'{course_code}.json'
            
            # Also create in target directory if different
            target_json_path = target_dir / f'{course_code}.json'
            
            semester_data = {
                'course': {
                    'code': course_code.upper(),
                    'name': f'Data Science Practicum - {course_display}',
                    'semester': 'Spring 2025',
                    'year': '2025',
                    'description': f'Student portfolios for {course_display} - Data Science Practicum course at Regis University.'
                },
                'university': {
                    'name': 'Regis University',
                    'phone': '(800) 388-2366',
                    'address': '3333 Regis Blvd, Denver, CO 80221',
                    'website': 'https://www.regis.edu'
                },
                'students': course_students,
                'spotlight': [],
                'statistics': {
                    'totalStudents': len(course_students),
                    'totalProjects': len(course_students),
                    'lastUpdated': datetime.now().isoformat()
                },
                'metadata': {
                    'dataSource': 'regis_std repository',
                    'syncedAt': datetime.now().isoformat(),
                    'version': '1.0'
                }
            }
            
            # Write JSON files
            with open(local_json_path, 'w', encoding='utf-8') as f:
                json.dump(semester_data, f, indent=2, ensure_ascii=False)
            
            # Copy to target directory if different
            if target_json_path != local_json_path:
                with open(target_json_path, 'w', encoding='utf-8') as f:
                    json.dump(semester_data, f, indent=2, ensure_ascii=False)
                print(f"📁 Synced: {target_json_path}")
            
            print(f"📊 Created {course_display} data file with {len(course_students)} students")
            print(f"📁 Saved: {local_json_path}")
        else:
            print(f"⏭️  No students found for {course_display}, skipping JSON creation")
    
    print(f"✅ Sync completed successfully!")

def generate_enhanced_project_html(project_content, project_title, course_info, project_urls):
    """Generate enhanced project HTML with proper course context"""
    if not project_content:
        return f'''
        <div class="bg-white rounded-lg shadow-lg p-8 text-center">
            <div class="bg-gray-100 rounded-lg p-8">
                <i class="fas fa-graduation-cap text-4xl text-gray-400 mb-4"></i>
                <h3 class="text-2xl font-bold text-gray-600 mb-4">{project_title}</h3>
                <p class="text-gray-500">Project information will be available soon.</p>
                <small class="text-gray-400 block mt-2">{course_info['course']}</small>
            </div>
        </div>
        '''
    
    # Handle both dictionary (parsed) and string (raw) input
    if isinstance(project_content, dict):
        # Extract information from parsed project dictionary
        project_data = project_content
        content_title = project_data.get('title', project_title)
        description = project_data.get('abstract', project_data.get('description', 'Project description coming soon.'))
        technologies = project_data.get('technologies', [])
        achievements = project_data.get('achievements', [])
        links = project_data.get('links', {})
        
        # Convert technologies list to string if needed
        if isinstance(technologies, list):
            tech_text = ', '.join(technologies) if technologies else 'Technologies will be listed here'
        else:
            tech_text = str(technologies) if technologies else 'Technologies will be listed here'
            
    else:
        # Handle raw string content (legacy support)
        lines = project_content.strip().split('\n')
        content_title = project_title
        description_start = 0
        
        # Look for a title in the first few lines
        for i, line in enumerate(lines[:3]):
            if line.startswith('#'):
                content_title = line.strip('#').strip() or project_title
                description_start = i + 1
                break
            elif line.strip() and not line.startswith('-') and not line.startswith('*'):
                content_title = line.strip() or project_title
                description_start = i + 1
                break
        
        # Get description
        description_lines = lines[description_start:] if description_start < len(lines) else []
        description = '\n'.join(description_lines).strip() if description_lines else 'Project description coming soon.'
        tech_text = 'Technologies will be listed here'
        achievements = []
        links = {}
    
    # Convert markdown to HTML for description
    description_html = description
    if description:
        # Simple markdown conversion
        description_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', description)
        description_html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', description)
        description_html = re.sub(r'`(.*?)`', r'<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">\1</code>', description_html)
        description_html = description_html.replace('\n\n', '</p><p class="mb-4">').replace('\n', '<br>')
        description_html = f'<p class="mb-4">{description_html}</p>'
    else:
        description_html = '<p class="text-gray-600">Project details will be added soon.</p>'
    
    # Generate achievements HTML
    achievements_html = ''
    if achievements:
        achievements_html = '<div class="mb-6"><h4 class="font-semibold mb-3">Key Achievements:</h4><ul class="list-disc list-inside space-y-1">'
        for achievement in achievements[:5]:  # Limit to 5 achievements
            achievements_html += f'<li class="text-gray-700">{achievement}</li>'
        achievements_html += '</ul></div>'
    
    # Generate project links
    links_html = ''
    if any(project_urls.values()):
        links_html = '<div class="flex flex-wrap gap-3 mt-6">'
        
        if project_urls.get('github'):
            links_html += f'''
            <a href="{project_urls['github']}" target="_blank" 
               class="inline-flex items-center px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition duration-300">
                <i class="fab fa-github mr-2"></i> GitHub Repository
            </a>
            '''
        
        if project_urls.get('presentation'):
            links_html += f'''
            <a href="{project_urls['presentation']}" target="_blank"
               class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition duration-300">
                <i class="fas fa-presentation-screen mr-2"></i> Presentation
            </a>
            '''
        
        if project_urls.get('report'):
            links_html += f'''
            <a href="{project_urls['report']}" target="_blank"
               class="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition duration-300">
                <i class="fas fa-file-pdf mr-2"></i> Project Report
            </a>
            '''
        
        links_html += '</div>'
    
    # Generate course badge
    course_badge = ''
    if course_info['is_practicum_1']:
        course_badge = '<span class="inline-block bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">MSDS 692</span>'
    else:
        course_badge = '<span class="inline-block bg-purple-100 text-purple-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">MSDS 696</span>'
    
    return f'''
    <div class="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition duration-300">
        <div class="mb-4">
            {course_badge}
        </div>
        <h3 class="text-2xl font-bold text-gray-900 mb-4">{content_title}</h3>
        <div class="text-gray-700 leading-relaxed mb-4">
            {description_html}
        </div>
        {links_html}
        <div class="mt-6 pt-4 border-t border-gray-200">
            <small class="text-gray-500">
                <i class="fas fa-university mr-1"></i>
                Regis University | {course_info['course']} | {course_info['semester']}
            </small>
        </div>
    </div>
    '''

def generate_project_html(project_data, title, gradient_color, student_files, course_code, username):
    """Generate project HTML with course context (legacy function for compatibility)"""
    # Convert to new format
    course_info = {
        'course': course_code,
        'is_practicum_1': 'msds692' in course_code.lower(),
        'semester': 'Current Semester'
    }
    
    # Create project URLs
    project_urls = {
        'github': student_files.get('github_url'),
        'presentation': student_files.get('presentation_url'),
        'report': student_files.get('report_url')
    }
    
    return generate_enhanced_project_html(project_data, title, course_info, project_urls)

def format_about_text(about_content):
    """Format about text as HTML"""
    if not about_content:
        return '''
        <div class="text-center text-gray-500 py-8">
            <i class="fas fa-user text-4xl mb-4"></i>
            <p>About information will be available soon.</p>
        </div>
        '''
    
    # Simple markdown to HTML conversion
    html_content = about_content
    
    # Convert markdown formatting
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
    html_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_content)
    html_content = re.sub(r'`(.*?)`', r'<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">\1</code>', html_content)
    
    # Handle paragraphs
    paragraphs = html_content.split('\n\n')
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph:
            # Replace single newlines with line breaks
            paragraph = paragraph.replace('\n', '<br>')
            formatted_paragraphs.append(f'<p class="mb-4">{paragraph}</p>')
    
    return '\n'.join(formatted_paragraphs) if formatted_paragraphs else '<p class="text-gray-600">About information will be available soon.</p>'

if __name__ == "__main__":
    print("🔄 Starting enhanced sync process...")
    sync_student_data()
    print("✅ Enhanced sync completed!")