import os
import requests
import zipfile
import subprocess
import shutil
from sonarqube import SonarQubeClient


# # Paths
# base_dir = os.path.dirname(os.path.realpath(__file__))
# sonar_scanner_dir = os.path.join(base_dir, 'sonar-scanner-5.0.1.3006-linux')
# sonar_scanner_bin = os.path.join(sonar_scanner_dir, 'bin')
# zip_file_path = os.path.join(base_dir, 'sonar-scanner-cli-5.0.1.3006-linux.zip')
# sonar_scanner_conf_path = os.path.join(sonar_scanner_dir, 'conf', 'sonar-scanner.properties')
# repo_path = os.path.join(sonar_scanner_bin, 'repo')

# # Settings
# sonar_download_url = 'https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip'
# sonar_project_name = 'Test'
# sonar_api_key = 'sqp_aeeb91cd92f0851ad0b00a2dc032150a45fe5085'
# git_repo_url = 'https://github.com/mermaid-js/mermaid'


# # Check if the sonar-scanner directory exists
# if not os.path.exists(sonar_scanner_dir):
#     print("SonarQube scanner not found. Downloading...\n")

#     # Download the ZIP file
#     response = requests.get(sonar_download_url)
#     with open(zip_file_path, 'wb') as file:
#         file.write(response.content)
#     with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
#         zip_ref.extractall(base_dir)
#     os.system(f'chmod +x -R {sonar_scanner_dir}')
#     os.remove(zip_file_path)

#     # Edit sonar-scanner properties
#     properties_to_append = [
#         "sonar.scm.exclusions.disabled=true",
#         "sonar.qualitygate.wait=true"
#     ]
#     with open(sonar_scanner_conf_path, 'a') as file:
#         file.write('\n' + '\n'.join(properties_to_append) + '\n')


# # Execute git clone
# try:
#     if os.path.exists(repo_path):
#         shutil.rmtree(repo_path)

#     subprocess.run(['git', 'clone', git_repo_url, repo_path], check=True)

#     # Check and rename the default branch's name to main
#     branchName = subprocess.run("git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'", shell=True, text=True, capture_output=True, cwd=repo_path)
#     branchName = branchName.stdout.strip()
#     if branchName != 'main':
#         subprocess.run(['git', 'branch', '-m', branchName, 'main'], check=True, cwd=repo_path)
    
#     print("Repository cloned\n")

# except subprocess.CalledProcessError as e:
#     print(f"Error cloning repository: {e}")


# # Execute SonarQube CLI
# sonar_scanner_cmd = [
#     './sonar-scanner',
#     f'-Dsonar.projectKey={sonar_project_name}',
#     f'-Dsonar.sources={repo_path}',
#     '-Dsonar.host.url=https://sonarqube.tobywinz.com',
#     f'-Dsonar.login={sonar_api_key}'
# ]
# subprocess.run(sonar_scanner_cmd, cwd=sonar_scanner_bin)
# print("SonarQube analysis completed.\n")


# Get the SonarQube analysis result
sonar = SonarQubeClient(sonarqube_url="https://sonarqube.tobywinz.com", username='admin', password='ecs260project')
component = sonar.measures.get_component_with_specified_measures(component="Test",
                                                                 branch="main",
                                                                 metricKeys="code_smells, ncloc, complexity, cognitive_complexity")

try:
    for measure in component['component']['measures']:
        if measure['metric'] == 'code_smells':
            print("Code smells value:", measure['value'])
        elif measure['metric'] == 'ncloc':
            print("Total Lines of Code:", measure['value'])
        elif measure['metric'] == 'complexity':
            print("Cyclomatic Complexity:", measure['value'])
        elif measure['metric'] == 'cognitive_complexity':
            print("Cognitive Complexity:", measure['value'])
except KeyError:
    print("Error extracting measures from the response.")
