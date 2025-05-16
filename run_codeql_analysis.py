import os
import subprocess
import shutil
from pathlib import Path

# Root directories
base_dir = os.path.abspath('.')
source_dir = os.path.join(base_dir, 'us.anthropic.claude-3-7-sonnet-20250219-v1_0', 'us.anthropic.claude-3-7-sonnet-20250219-v1_0')
output_dir = os.path.join(base_dir, 'codeql_analysis')

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# 在脚本开头定义你的自定义查询套件路径
MY_CWE_QLS = os.path.abspath('my-cwe.qls')

QUERY_PACKS = {
    'python': MY_CWE_QLS,
    'javascript': 'codeql/javascript-queries:security-and-quality',
    'java': 'codeql/java-queries:security-and-quality',
    'cpp': 'codeql/cpp-queries:security-and-quality',
    'csharp': 'codeql/csharp-queries:security-and-quality',
    'go': 'codeql/go-queries:security-and-quality',
    'ruby': 'codeql/ruby-queries:security-and-quality'
}

# Function to determine the language based on file extensions
def detect_language(code_dir):
    extensions = set()
    for root, _, files in os.walk(code_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            extensions.add(ext)
    
    if '.py' in extensions:
        return 'python'
    elif '.js' in extensions or '.ts' in extensions:
        return 'javascript'
    elif '.java' in extensions:
        return 'java'
    elif '.cpp' in extensions or '.cc' in extensions or '.h' in extensions:
        return 'cpp'
    elif '.cs' in extensions:
        return 'csharp'
    elif '.go' in extensions:
        return 'go'
    elif '.rb' in extensions:
        return 'ruby'
    else:
        return None

# CodeQL analysis function
def run_codeql_analysis(code_dir, output_path, language):
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create a CodeQL database
    db_path = os.path.join(base_dir, 'temp_codeql_db')
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    
    try:
        # Create CodeQL database
        subprocess.run([
            'codeql', 'database', 'create', db_path,
            '--language=' + language,
            '--source-root=' + code_dir
        ], check=True)
        
        # Run analysis
        subprocess.run([
            'codeql', 'database', 'analyze', db_path,
            '--format=sarif-latest',
            '--output=' + output_path,
            QUERY_PACKS[language]
        ], check=True)
        
        print(f"Analysis completed for {code_dir}, results saved to {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error analyzing {code_dir}: {e}")
    finally:
        # Clean up
        if os.path.exists(db_path):
            shutil.rmtree(db_path)

# Traverse directory structure
for scenario in os.listdir(source_dir):
    scenario_path = os.path.join(source_dir, scenario)
    
    # Skip non-directories and hidden files
    if not os.path.isdir(scenario_path) or scenario.startswith('.'):
        continue
    
    for framework in os.listdir(scenario_path):
        framework_path = os.path.join(scenario_path, framework)
        
        # Skip non-directories and hidden files
        if not os.path.isdir(framework_path) or framework.startswith('.'):
            continue
        
        for temp_dir in os.listdir(framework_path):
            temp_dir_path = os.path.join(framework_path, temp_dir)
            
            # Skip non-directories and hidden files
            if not os.path.isdir(temp_dir_path) or temp_dir.startswith('.'):
                continue
            
            # Check for sample0 directory
            sample0_path = os.path.join(temp_dir_path, 'sample0')
            if os.path.exists(sample0_path) and os.path.isdir(sample0_path):
                code_path = os.path.join(sample0_path, 'code')
                
                if os.path.exists(code_path) and os.path.isdir(code_path):
                    # Determine relative path for output
                    rel_path = os.path.relpath(code_path, source_dir)
                    output_path = os.path.join(output_dir, rel_path, 'codeql_results.sarif')
                    
                    # Detect language
                    language = detect_language(code_path)
                    if language:
                        print(f"Analyzing {rel_path} (detected as {language})...")
                        run_codeql_analysis(code_path, output_path, language)
                    else:
                        print(f"Skipping {rel_path} - could not detect language")

print("CodeQL analysis complete!")
