# Regis University Student Data Processing System

This repository automates the creation of professional student portfolios for the Regis University Data Science Practicum program.

## � Quick Start

### For Faculty 👩‍🏫
Upload your CSV file → Student folders are created automatically → Professional portfolios generated

**📖 [Complete Faculty Guide](../instructor-guide.html)**

### For Students 🎓
Edit your profile → Add your photo and files → Portfolio published automatically

**📖 [Complete Student Guide](../student-guide.html)**

## 📋 How It Works

1. **Faculty uploads CSV** with student roster (format: `2025_Summer_MSDS692.csv`)
2. **System creates folders** for each student with profile templates
3. **Students customize** their `profile.md` files and add assets
4. **Automated sync** generates professional HTML portfolios
5. **Main portfolio site** is updated automatically

## 🏗️ System Architecture

```
CSV Upload → Student Folders → Profile Templates → HTML Generation → Portfolio Site
```

## 📁 Generated Structure

```
data/2025_summer_msds692/
├── student1/
│   ├── profile.md          # Student edits this
│   ├── avatar.jpg          # Profile photo
│   ├── reports/           # Project reports
│   └── presentations/     # Project slides
└── student2/
    └── ...
```

## � CSV Format

```csv
Student Name,Email,Username,Project Title,GitHub,Presentation,Report,Profile Page
"John Doe","jdoe@worldclass.regis.edu","jdoe001","Data Analysis Project","","","",""
"Jane Smith","jsmith@regis.edu","jsmith002","ML Classification","","","",""
```

## 📊 Features

- ✅ **Automated Processing**: Zero manual setup
- ✅ **Email Cleaning**: `@worldclass.regis.edu` → `@regis.edu`
- ✅ **Professional Design**: University-branded portfolios
- ✅ **Mobile Responsive**: Works on all devices
- ✅ **Course Support**: MSDS 692 and MSDS 696
- ✅ **Asset Management**: Images, reports, presentations

## � Documentation

- **[Faculty Guide](../instructor-guide.html)** - Complete management instructions
- **[Student Guide](../student-guide.html)** - Step-by-step portfolio creation
- **[Technical Documentation](../documentation.html)** - System architecture and API
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Development overview

## 🤖 Automation

GitHub Actions automatically:
- Detects CSV uploads
- Creates student folders and templates
- Generates HTML portfolios
- Syncs to main portfolio repository
- Optimizes images for web

## 🆘 Support

- **Faculty**: See [Instructor Guide](../instructor-guide.html) for management tasks
- **Students**: See [Student Guide](../student-guide.html) for portfolio creation
- **Technical Issues**: Create an issue in this repository
- **Contact**: datasciencehelp@regis.edu

---

**Regis University Data Science Program**  
*Automated Portfolio Generation System v1.0*