# students/compiler_service.py
# Cloud Code Execution Engine using Piston API
# Works on any hosting platform (Render, Heroku, etc.) without Docker.

import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Language configuration for Piston API
PISTON_LANGUAGES = {
    'python': {'language': 'python', 'version': '3.10.0'},
    'javascript': {'language': 'javascript', 'version': '18.15.0'},
    'cpp': {'language': 'c++', 'version': '10.2.0'},
    'java': {'language': 'java', 'version': '15.0.2'},
}

@csrf_exempt
def run_code_in_docker(request):
    """
    Cloud Code Execution using Piston API.
    Name kept as run_code_in_docker for backward compatibility with urls.py.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid Request'})
        
    try:
        data = json.loads(request.body)
        language = data.get('language', 'python')
        code = data.get('code', '')
        user_input = data.get('user_input', '')
        
        if not code.strip():
            return JsonResponse({'status': 'error', 'message': 'Code cannot be empty.'})

        # Validate language
        lang_config = PISTON_LANGUAGES.get(language)
        if not lang_config:
            return JsonResponse({'status': 'error', 'message': 'Unsupported language.'})

        # File extension mapping
        ext_map = {'python': 'py', 'javascript': 'js', 'cpp': 'cpp', 'java': 'java'}

        # Build Piston API payload
        piston_payload = {
            'language': lang_config['language'],
            'version': lang_config['version'],
            'files': [
                {
                    'name': f'main.{ext_map.get(language, "txt")}',
                    'content': code
                }
            ],
            'stdin': user_input,
            'run_timeout': 15000,
            'compile_timeout': 15000,
            'run_memory_limit': 256000000
        }

        # Call Piston API
        piston_response = requests.post(
            'https://emkc.org/api/v2/piston/execute',
            json=piston_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if piston_response.status_code != 200:
            return JsonResponse({
                'status': 'error',
                'output': f'Code execution service returned status {piston_response.status_code}. Please try again.'
            })

        result = piston_response.json()
        run_data = result.get('run', {})
        compile_data = result.get('compile', {})

        # Check compilation errors
        if compile_data and compile_data.get('code') is not None and compile_data.get('code') != 0:
            return JsonResponse({
                'status': 'error',
                'output': compile_data.get('stderr', '') or compile_data.get('output', 'Compilation failed.')
            })

        # Check run results
        stdout = run_data.get('stdout', '')
        stderr = run_data.get('stderr', '')
        exit_code = run_data.get('code', 0)
        signal = run_data.get('signal')

        if signal == 'SIGKILL':
            return JsonResponse({
                'status': 'error',
                'output': 'Timeout Error: Your code took too long to execute (Possible Infinite Loop).'
            })

        if exit_code == 0:
            final_output = stdout if stdout else "Execution completed (No output)"
            return JsonResponse({'status': 'success', 'output': final_output})
        else:
            error_output = stderr if stderr else stdout
            if not error_output:
                error_output = f"Program exited with code {exit_code}"
            return JsonResponse({'status': 'error', 'output': error_output})

    except requests.exceptions.Timeout:
        return JsonResponse({'status': 'error', 'output': 'Timeout: The code execution service did not respond in time.'})
    except requests.exceptions.ConnectionError:
        return JsonResponse({'status': 'error', 'output': 'Connection Error: Unable to reach the code execution service.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})