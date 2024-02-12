import os
import requests
import zipfile
import subprocess
import shutil
from sonarqube import SonarQubeClient

# global variables
sonar_scanner_dir = 'sonar-scanner-5.0.1.3006-linux'
sonar_scanner_bin = os.path.join(sonar_scanner_dir, 'bin')
sonar_download_url = 'https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip'
sonar_project_name = 'Test'
sonar_api_key = 'sqp_aeeb91cd92f0851ad0b00a2dc032150a45fe5085'

repo_path = os.path.join(sonar_scanner_bin, 'repo')
git_repo_url = 'https://github.com/mermaid-js/mermaid'


# Check if the sonar-scanner directory exists
if not os.path.exists(sonar_scanner_dir):
    print("SonarQube not found. Downloading...\n")

    # Download the ZIP file
    response = requests.get(sonar_download_url)
    zip_file_path = 'sonar-scanner-cli-5.0.1.3006-linux.zip'
    with open(zip_file_path, 'wb') as file:
        file.write(response.content)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(".")
    os.system(f'chmod +x -R {sonar_scanner_dir}')

    # Remove the ZIP file after extraction
    os.remove(zip_file_path)


# Execute git clone
try:
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)

    subprocess.run(['git', 'clone', git_repo_url, repo_path], check=True)

    # Check and rename the default branch's name to main
    branchName = subprocess.run("git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'", shell=True, text=True, capture_output=True, cwd=repo_path)
    branchName = branchName.stdout.strip()
    if branchName != 'main':
        # Rename default branch to main
        subprocess.run(['git', 'branch', '-m', branchName, 'main'], check=True, cwd=repo_path)
    
    print("Repository cloned\n")

except subprocess.CalledProcessError as e:
    print(f"Error cloning repository: {e}")


# Execute SonarQube CLI
sonar_scanner_cmd = [
    './sonar-scanner',
    f'-Dsonar.projectKey={sonar_project_name}',
    '-Dsonar.sources=./repo',
    '-Dsonar.host.url=https://sonarqube.tobywinz.com',
    f'-Dsonar.login={sonar_api_key}'
]
subprocess.run(sonar_scanner_cmd, cwd=sonar_scanner_bin)
print("SonarQube analysis completed.")


# Get the SonarQube analysis result
sonar = SonarQubeClient(sonarqube_url="https://sonarqube.tobywinz.com", username='admin', password='ecs260project')
component = sonar.measures.get_component_with_specified_measures(component="Test",
                                                                branch="main",
                                                                metricKeys="code_smells")
print(component)
print(component['component']['measures'])
