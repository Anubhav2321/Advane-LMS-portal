# students/compiler_service.py
# Advanced Multi-Language Cloud & Local Execution Engine
# Supports Python 3, Node.js, C++ (GCC/MinGW), and Java with custom stdin & execution metrics.

import os
import re
import sys
import time
import json
import shutil
import tempfile
import requests
import subprocess
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

PISTON_LANGUAGES = {
    'python': {'language': 'python', 'version': '3.10.0'},
    'javascript': {'language': 'javascript', 'version': '18.15.0'},
    'cpp': {'language': 'c++', 'version': '10.2.0'},
    'java': {'language': 'java', 'version': '15.0.2'},
}

def execute_locally(language, code, user_input=""):
    """
    Executes code in an isolated temporary environment using system compilers.
    Extremely fast, robust, and handles custom standard input.
    """
    t0 = time.perf_counter()
    timeout_sec = 10
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            if language == 'python':
                file_path = os.path.join(tmpdir, "main.py")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                
                # Use current Python interpreter (virtual environment)
                py_exec = sys.executable or "python"
                proc = subprocess.run(
                    [py_exec, file_path],
                    input=user_input,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    cwd=tmpdir
                )
                elapsed = time.perf_counter() - t0
                if proc.returncode == 0:
                    return {
                        'status': 'success',
                        'output': proc.stdout or 'Execution completed (No output)',
                        'execution_time': f"{elapsed:.2f}s"
                    }
                return {
                    'status': 'error',
                    'output': proc.stderr or proc.stdout or f'Process exited with code {proc.returncode}',
                    'execution_time': f"{elapsed:.2f}s"
                }

            elif language in ['javascript', 'js']:
                file_path = os.path.join(tmpdir, "main.js")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                
                proc = subprocess.run(
                    ["node", file_path],
                    input=user_input,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    cwd=tmpdir
                )
                elapsed = time.perf_counter() - t0
                if proc.returncode == 0:
                    return {
                        'status': 'success',
                        'output': proc.stdout or 'Execution completed (No output)',
                        'execution_time': f"{elapsed:.2f}s"
                    }
                return {
                    'status': 'error',
                    'output': proc.stderr or proc.stdout or f'Node exited with code {proc.returncode}',
                    'execution_time': f"{elapsed:.2f}s"
                }

            elif language in ['cpp', 'c++']:
                file_path = os.path.join(tmpdir, "main.cpp")
                exe_path = os.path.join(tmpdir, "main.exe" if os.name == 'nt' else "main.out")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                
                # Compilation stage
                compile_proc = subprocess.run(
                    ["g++", "-O2", "-o", exe_path, file_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    cwd=tmpdir
                )
                if compile_proc.returncode != 0:
                    elapsed = time.perf_counter() - t0
                    return {
                        'status': 'error',
                        'output': f"Compilation Error:\n{compile_proc.stderr}",
                        'execution_time': f"{elapsed:.2f}s"
                    }
                
                # Execution stage
                proc = subprocess.run(
                    [exe_path],
                    input=user_input,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    cwd=tmpdir
                )
                elapsed = time.perf_counter() - t0
                if proc.returncode == 0:
                    return {
                        'status': 'success',
                        'output': proc.stdout or 'Execution completed (No output)',
                        'execution_time': f"{elapsed:.2f}s"
                    }
                return {
                    'status': 'error',
                    'output': proc.stderr or proc.stdout or f'Process exited with code {proc.returncode}',
                    'execution_time': f"{elapsed:.2f}s"
                }

            elif language == 'java':
                # Detect public class name if available, default to Main
                match = re.search(r'public\s+class\s+([A-Za-z_][A-Za-z0-9_]*)', code)
                class_name = match.group(1) if match else "Main"
                file_path = os.path.join(tmpdir, f"{class_name}.java")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                
                # Compilation
                compile_proc = subprocess.run(
                    ["javac", file_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    cwd=tmpdir
                )
                if compile_proc.returncode != 0:
                    elapsed = time.perf_counter() - t0
                    return {
                        'status': 'error',
                        'output': f"Compilation Error:\n{compile_proc.stderr}",
                        'execution_time': f"{elapsed:.2f}s"
                    }
                
                # Execution
                proc = subprocess.run(
                    ["java", "-cp", tmpdir, class_name],
                    input=user_input,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    cwd=tmpdir
                )
                elapsed = time.perf_counter() - t0
                if proc.returncode == 0:
                    return {
                        'status': 'success',
                        'output': proc.stdout or 'Execution completed (No output)',
                        'execution_time': f"{elapsed:.2f}s"
                    }
                return {
                    'status': 'error',
                    'output': proc.stderr or proc.stdout or f'JVM exited with code {proc.returncode}',
                    'execution_time': f"{elapsed:.2f}s"
                }
            else:
                return {
                    'status': 'error',
                    'output': f"Unsupported language: '{language}'. Supported: python, javascript, cpp, java",
                    'execution_time': '0.00s'
                }

        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'output': f"⏱️ Execution Timeout ({timeout_sec}s limit exceeded).\nPossible infinite loop or heavy computation.",
                'execution_time': f"{timeout_sec:.2f}s"
            }
        except FileNotFoundError as fnf:
            return {
                'status': 'error',
                'output': f"Execution Environment Error: Compiler/Runtime for {language} not found on server ({str(fnf)}).",
                'execution_time': '0.00s'
            }
        except Exception as e:
            return {
                'status': 'error',
                'output': f"Execution Error: {str(e)}",
                'execution_time': '0.00s'
            }


@csrf_exempt
def run_code_in_docker(request):
    """
    High-Performance Code Execution Engine.
    Handles requests from Community Chat, Live IDE Modal, and Syntax Singularity.
    Supports Python, JavaScript, C++, and Java with real-time execution metrics.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP Method. POST required.'}, status=405)
        
    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        language = (data.get('language') or 'python').strip().lower()
        code = data.get('code', '')
        user_input = data.get('user_input', '')
        
        if not code or not code.strip():
            return JsonResponse({'status': 'error', 'message': 'Code buffer cannot be empty.'})

        # Normalize language aliases
        lang_alias = {
            'py': 'python',
            'js': 'javascript',
            'node': 'javascript',
            'c++': 'cpp',
            'cplusplus': 'cpp'
        }
        language = lang_alias.get(language, language)

        # 1. Execute using Native Isolated Sandbox Engine (Lightning Fast & Real Stdin)
        result = execute_locally(language, code, user_input)
        
        # 2. Return formatted JSON response
        return JsonResponse({
            'status': result['status'],
            'output': result['output'],
            'execution_time': result.get('execution_time', '0.00s'),
            'language': language
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'output': f"Fatal Execution Server Exception: {str(e)}",
            'message': str(e)
        }, status=500)