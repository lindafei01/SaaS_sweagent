
import os
import tempfile
import subprocess

def test_typescript_compilation():
    print("Testing TypeScript compilation...")
    
    # Test with error
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.ts")
        with open(file_path, 'w') as f:
            f.write("let x = y * 2;")
        
        process = subprocess.run(
            ['tsc', '--noEmit', file_path],
            capture_output=True,
            text=True
        )
        
        print("TypeScript compilation with error:")
        print(f"Return code: {process.returncode}")
        print(f"Error output: {process.stderr}")
    
    # Test without error
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.ts")
        with open(file_path, 'w') as f:
            f.write("let x = 2 * 15;")
        
        process = subprocess.run(
            ['tsc', '--noEmit', file_path],
            capture_output=True,
            text=True
        )
        
        print("\nTypeScript compilation without error:")
        print(f"Return code: {process.returncode}")
        print(f"Error output: {process.stderr}")

def test_cpp_compilation():
    print("\nTesting C++ compilation...")
    
    # Test with error
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.cpp")
        with open(file_path, 'w') as f:
            f.write("int main() { undefinedVar = 10; return 0; }")
        
        process = subprocess.run(
            ['g++', '-o', os.path.join(temp_dir, "test"), file_path],
            capture_output=True,
            text=True
        )
        
        print("C++ compilation with error:")
        print(f"Return code: {process.returncode}")
        print(f"Error output: {process.stderr}")
    
    # Test without error
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.cpp")
        with open(file_path, 'w') as f:
            f.write("int main() { return 0; }")
        
        process = subprocess.run(
            ['g++', '-o', os.path.join(temp_dir, "test"), file_path],
            capture_output=True,
            text=True
        )
        
        print("\nC++ compilation without error:")
        print(f"Return code: {process.returncode}")
        print(f"Error output: {process.stderr}")

if __name__ == "__main__":
    test_typescript_compilation()
    test_cpp_compilation()
    print("\nTests completed.")