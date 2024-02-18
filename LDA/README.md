# Do TypeScript Applications Exhibit Better Software Quality than JavaScript Applications? A Repository Mining Study on GitHub
> In the following, all the necessary steps are described for the sampling process, the data collection, and the statistical analysis of the study.

## Prerequisites for `script.py`
Install all dependencies by executing `pip install -r requirements.txt`.

## Prerequisites for Sampling
Create six GitHub tokens from different accounts for the authentication of the API requests and copy the tokens into `constants.py`.
(recommended to reduce time; if you use only one, you need to change code in `getBugCommits()` in the `Sampling` class)

## Sampling
Set the the creation date and the current date of the repositories to be examined in the `init()` method of the `Sampling` class (`self.startDate` and `self.endDate`).

Execute the following two points for all programming languages (first JavaScript, second TypeScript, and finally Vue):

* Set the programming language of the repositories to be requested when creating the `Language` object (at the bottom of the file).
* Step one of the sampling: execute the `requestRepos()` method in the `Sampling` class to get a list of all repositories of the selected programming language. The parameter is the minimum number of stars a repository must have. A `.txt` file is created for each programming language in the same directory. It contains all repositories that have more than the given number of stars and that are not a fork.
* After the Vue repositories have been stored, they need to be added to the appropriate JS or TS file. To do this, call the `sortVueProjectsLanguage()` method in the `Sampling` class. To adjust the index of the added repositories in the respective file, the `sortReposByStars()` method of the `Sampling` class needs to be called afterwards. Remember to set the appropriate language in the language object.

There are now three `.txt` files in total (`JavaScriptRepos.txt`, `TypeScriptRepos.txt` and `VueRepos.txt`). `VueRepos.txt` is no longer needed as the repositories are already added to the list of the primary programming language (TypeScript or JavaScript).

Execute the following two steps for JavaScript and TypeScript (Note: set the appropriate language in the `Language` object).

* Step two of sampling: execute the `checkRepoByCharacteristics()` method in the `Sampling` class to check the repositories from the list created in the first sampling step for the following three characteristics:
  1. Repositories needs to be an application
  2. Have closed bug issues
  3. have more than 30 commits
* When this method is run, a new file is created with a new list containing only valid repositories for the study (returned by the script and needs to be manually checked). As the first parameter, the first index of the repository from the list (from step one) is specified. At this index the script starts to check for the characteristics. The second parameter specifies how many repos should be in the new list of valid repositories after the characteristics have been checked. This has the advantage that, for example, after 400 repositories you don't have to examine the rest of the list (from step one) and you can manually examine the returned repositories from the second sampling step. Delete repositories from the list if they were incorrectly selected.
* After the manual examination, the second sampling step can be performed again until the correct sample size is obtained.

## Prerequisites for Data Collection
* Sampling step completed
* Create a SonarQube account and install all the required building blocks to run SonarQube locally (https://www.sonarqube.org)
* Create a token in SonarQube and copy it into the `constants.py` file
* Download and install Node.js including npm (https://nodejs.org)
* Create the following folder structure in the directory of `script.py` for storing later files:
  * `./git-repos/TS/`
  * `./git-repos/JS/`
  * `.eslint/eslintReports` (make sure to have the default `.eslintignore` and `.eslintrc` in the `.eslint/` folder)
* After creating the folder structure, clone all repositories from the `JavaScriptReposCharacteristics.txt` and `TypeScriptReposCharacteristics.txt` files. To do so, execute for both programming languages the method `cloneRepoFromList()` from the `CloneRepo` class (remember to change the programming language in the `Language` object).
* Create two `.csv` files for each programming language where the collected data will be stored. To do this, when creating the `CSV` object (at the very end of the file), enter `ReposCharacteristics.csv` for the parameter suffix and then execute the `createAndInitCSV()` method of the CSV class. Repeat this, but this time with the parameter `Metrics.csv`. This creates and fills two files per programming language at the root level. Repeat this for the other programming language.

## Data Collection
### Code Smells, Cognitive Complexity and ncloc
For this, SonarQube needs to be already running locally. Now execute for both programming languages (change at `Language` Object) the method `createAndAnalyzeRepos` in the `SonarQubeDance` class. The analysis of all projects from the list will be started automatically and all three values will be stored in the `.csv` file (name is: language + `ReposCharacteristics.csv` suffix). This step takes a while, because all projects are examined by SonarQube. Afterwards the data collection needs to be manually examined. If a value is found to be incorrect, the analysis needs to be done manually again.

### `any` Type
For this, only the TypeScript repositories need to be examined (`Language` object needs TypeScript as parameter). To get the `any` type, ESLint (https://typescript-eslint.io) is installed and executed automatically. To choose the right storage location, pass in the `CSV` object (bottom of the file) the suffix `ReposCharacteristics.csv` as parameter. Now, execute the `createEslintReport()` method in the `ESLint` object (bottom of the file). This step takes a while, because all TypeScript projects are examined by ESLint. Afterwards the data collection needs to be manually examined. If a value is found to be incorrect, the analysis needs to be done manually again.

### Framework used (not necessary for MSR conference)
For both programming languages (change at `Language` Object), execute the `getFramework()` method in the `Framework` class. Note: to choose the right storage location, pass in the `CSV` object (bottom of the file) the suffix `ReposCharacteristics.csv` as parameter. For each project the used frameworks is stored in the `.csv` file (name is language + `ReposCharacteristics.csv` suffix). If multiple frameworks are specified, the `package.json` file of the project needs to be examined manually. This will quickly reveal which framework was used.

### Bug Issues
The raw data of this is still in the `.txt` file (language + `ReposCharacteristics.txt`). Now, these need to be written to the `.csv` files. For each of the programming languages (change at `Language` Object) execute the method `writeIssueDataFromJsonToCSV` in the `Sampling` class. The values are written in both `.csv` files (with suffix `Metrics.csv` and `ReposCharacteristics.csv`) at the same time. So, there is no need to specify the suffix as a parameter when creating the CSV object.

### Bug-Fix Commits
The raw data of this is still in the `.txt` file (language + `ReposCharacteristics.txt`). These needs to be now written to the `.csv` files. For each of the programming languages (change at `Language` Object) execute the method `writeCommitsDataFromJsonToCSV()` in the `Sampling` class. The values are written in both `.csv` files (with suffix `Metrics.csv` and `ReposCharacteristics.csv`) at the same time. So, there is no need to specify the suffix as a parameter when creating the CSV object.

### Code Smells per LoC, Cognitive Complexity per LoC & `any` Type per LoC
To get the last values per line of code and store them in the `.csv` file (language + `Metrics.csv` suffix) the method `calculateMetricPerLoc()` needs to be executed in the `Metrics` class for both programming languages (change at `Language` Object). The metrics are passed as parameters, in this case `any-type_count` (of course only for TypeScript), `code_smells` and `cognitive_complexity`.

Now, both tables (with suffix `Metrics.csv` and `ReposCharacteristics.csv`) are filled and the statistical analysis can be performed.

## Statistical Analysis
### Hypothesis Tests
The hypothesis test is performed by the method `testHypothesis()` in the class `Test`. As first parameter the method gets the data collection of the metric (method `getMetricWithoutInf()` from the `Metrics` class returns the values of a metric from the table without `inf` values). The second parameter is the alternative (see `script.py` or the `numpy` documentation). Make sure to pass the correct programming language when creating the `Language` object.

### Correlation Tests
Depending on the distribution of the data, either the Pearson test or the Spearman test needs to be used. The methods (`pearson` and `spearman`) can be found in the `Test` class.