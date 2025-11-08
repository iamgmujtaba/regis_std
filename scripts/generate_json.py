#!/usr/bin/env python3
"""
GitHub Actions wrapper script for JSON generation
This ensures the correct parameters are used in automated workflows
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Generate JSON files for all CSV files in data directory"""
    
    # Find the script directory
    script_dir = Path(__file__).parent
    process_script = script_dir / "process_csv.py"
    
    # Find CSV files in data directory
    data_dir = script_dir.parent / "data"
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print("❌ No CSV files found in data directory")
        return 1
    
    print("🎓 GitHub Actions JSON Generator")
    print("=" * 50)
    print(f"📂 Looking for CSV files in: {data_dir}")
    print(f"📄 Found {len(csv_files)} CSV file(s)")
    
    success_count = 0
    
    for csv_file in csv_files:
        print(f"\n🔄 Processing: {csv_file.name}")
        
        try:
            # Run the process_csv.py script with --json-only flag
            cmd = [
                sys.executable,
                str(process_script),
                "--json-only",
                str(csv_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir.parent)
            
            if result.returncode == 0:
                print(f"✅ Successfully processed {csv_file.name}")
                success_count += 1
            else:
                print(f"❌ Failed to process {csv_file.name}")
                print(f"Error: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Exception processing {csv_file.name}: {str(e)}")
    
    print(f"\n📊 Final Summary:")
    print(f"   📄 CSV files processed: {len(csv_files)}")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {len(csv_files) - success_count}")
    
    if success_count == len(csv_files):
        print(f"🎉 All JSON files generated successfully!")
        
        # List generated JSON files in data directory
        json_files = list((script_dir.parent / "data").glob("*.json"))
        if json_files:
            print(f"\n📄 Generated JSON files in data/ folder:")
            for json_file in json_files:
                print(f"   • {json_file.name}")
        
        return 0
    else:
        print(f"⚠️  Some files failed to process")
        return 1

if __name__ == "__main__":
    sys.exit(main())