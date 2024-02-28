import requests
import json
import re
import time
import calendar
import datetime as dt
from datetime import timedelta
import constants
import shutil
import os
import pandas as pd
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from gensim import corpora
from gensim.models import LdaModel
import sys
import time
import csv
from tqdm import tqdm

import subprocess
from git import Repo
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import numpy as np
import scipy
from bokeh.models import HoverTool
from bokeh.plotting import figure, show
from matplotlib import pyplot
from numpy.polynomial.polynomial import polyfit
import random


class Sampling:
    """In this class, individual methods are implemented that were executed for sampling. The sampling process is iterative and cannot be performed in one single step. More about this can be found in the paper."""

    def __init__(self):
        self.curLanguage = language.getLanguage()
        # Set date here.
        self.startDate = dt.date(2012, 1, 1)
        self.endDate = dt.date(2021, 6, 28)
        self.incompleteResult = False
        self.errorCode = "200"
        self.counter = 0
        self.counter2 = 0
        pass

    def requestRepos(self, stars):
        """This is the first step of sampling. In this function, all repos that match the characteristics are stored in a file. More to the characteristics at the request url.

        Args:
            stars (integer): Minimum number of of stars a repository must have.
        """
        count = 0
        timeOut = 0
        reposCounter = 0
        repositories = []
        sampling.setErrorToDefault()

        # Repos are requested per day.
        for single_date in sampling.daterange(self.startDate, self.endDate):
            currentDate = single_date.strftime("%Y-%m-%d")

            timeOut += 1

            # Check if we need a timeout because of the low request limit of 5000 per hour to GitHub. If the intermediate results are saved.
            if sampling.timeOut(timeOut, 30):
                print("true")
                fileClass.writeToFile(
                    str(self.curLanguage) + "Repos.txt",
                    sampling.repoJsons(
                        reposCounter,
                        self.incompleteResult,
                        self.errorCode,
                        repositories,
                    ),
                )
                self.sortReposByStars()

            """ Only 100 results can be returned from GitHub per request, so repos are requested per day.
            Characteristics:
                1. More than xy stars
                2. No fork
                3. Primary language == language
                4. Date range
            """
            url = f"https://api.github.com/search/repositories?q=stars:>={stars}+language:{self.curLanguage}+created:{currentDate}&sort=stars&order=asc&per_page=100"
            repoByLanguageResponse = requests.get(
                url, auth=("username", constants.TOKEN)
            )
            count += 1
            print(count)

            if repoByLanguageResponse.status_code == 200:
                print(currentDate)
                repoByLanguageResponseJson = repoByLanguageResponse.json()

                for responseRepos in repoByLanguageResponseJson["items"]:
                    if not responseRepos["fork"]:
                        print("valid")
                        reposCounter += 1
                        # 'None' values will be added later in sampling
                        repositories.append(
                            sampling.repoKey(
                                None,
                                responseRepos["full_name"],
                                currentDate,
                                responseRepos["stargazers_count"],
                                None,
                                None,
                            )
                        )
            else:
                self.errorCode = repoByLanguageResponse.status_code
                if not self.errorCode == 404:
                    self.incompleteResult = True
                    print(self.errorCode)
                    print("error on repo requests. Current date: " + str(currentDate))

        fileClass.writeToFile(
            str(self.curLanguage) + "Repos.txt",
            sampling.repoJsons(
                reposCounter, self.incompleteResult, self.errorCode, repositories
            ),
        )
        self.sortReposByStars()
        print("Finished with requesting Repos.")

    def checkRepoByCharacteristics(self, firstRepoIndex, numberOfRepos):
        """The second step of sampling. The raw list from the requestRepos function is refined iterativly, sorted out and saved in a second file.

        Args:
            firstRepoIndex (integer): From this index, the raw repo list is refined.
            numberOfRepos(integer): The size of the repo list after refinement.
        """
        startIndex = firstRepoIndex
        startTime = time.time()
        repoList = fileClass.openFile(str(self.curLanguage) + "Repos.txt")

        print(len(repoList["repositories"]))

        if not firstRepoIndex + numberOfRepos <= len(repoList["repositories"]):
            sys.exit(
                "Index out of bounds. Set your index on function call lower. Last repo has index: "
                + str(len(repoList["repositories"]))
            )

        sampling.setErrorToDefault()

        reposWithcharacteristics = fileClass.openFile(
            self.curLanguage + str("ReposCharacteristics.txt")
        )

        reposMatchCharacteristics = []
        lostRepos = 0

        countReposWithCharac = 0

        """
        1 check if repo is an app
        1.1 check with lda if repo is an app and if so, save it
        1.2 check if repo has package.json and if so check if lda returns framework, library, etc. If it does not examine repo further

        2 get issues
        2.1 check if there are closed bug-issues and if so save them
        2.2 check if there are unlabeled closed issue and if so check if it is a bug and if so save them

        3 get commits
        3.1 check if there are more than 30 commits
        3.2 check if there are bug-commits and if so save them
        3.3 check commit if ts or js file is included
        """

        for repo in repoList["repositories"]:
            if repo["index"] < firstRepoIndex:
                continue

            try:
                countReposWithChara = reposWithcharacteristics["total_count"]
            except TypeError:
                countReposWithChara = 0
            if countReposWithChara <= numberOfRepos:
                # 1
                print(
                    "Repo "
                    + str(firstRepoIndex)
                    + " ("
                    + str(repo["repoFullName"])
                    + ") is currently checked"
                )

                # Check first criterion
                # print("checkIfApp")
                if sampling.checkIfApp(repo["repoFullName"]):
                    print("repo is app: " + str(repo["repoFullName"]))
                else:
                    print("Skip repo: " + str(repo["repoFullName"]))
                    lostRepos += 1
                    firstRepoIndex += 1
                    continue

                # Check second criterion
                print("getclosedIssues")
                closedBugIssues = sampling.getClosedIssues(repo["repoFullName"])
                print("finished with issues")

                if not closedBugIssues["issues"] == [] and not self.incompleteResult:
                    repo["issues"] = closedBugIssues
                else:
                    print("no closed bug issues")
                    lostRepos += 1
                    firstRepoIndex += 1
                    continue

                # Check third criterion
                print("getBugCommits")
                bugCommits = sampling.getBugCommits(repo["repoFullName"])
                print("finished with commits")

                if (
                    not bugCommits["bug_commits"] == []
                    and bugCommits["total_commits"] > 30
                    and not self.incompleteResult
                ):
                    repo["commits"] = bugCommits
                else:
                    print("no bug issues")
                    lostRepos += 1
                    firstRepoIndex += 1
                    continue

                if not reposWithcharacteristics:
                    reposWithcharacteristics = sampling.repoJsons(
                        len(reposMatchCharacteristics),
                        self.incompleteResult,
                        self.errorCode,
                        reposMatchCharacteristics,
                    )

                reposWithcharacteristics["incomplete_result"] = self.incompleteResult
                reposWithcharacteristics["error_code"] = self.errorCode
                reposWithcharacteristics["total_count"] += 1
                countReposWithCharac += 1
                repo["index"] = reposWithcharacteristics["total_count"]
                reposWithcharacteristics["repositories"].append(repo)
                fileClass.writeToFile(
                    self.curLanguage + str("ReposCharacteristics.txt"),
                    reposWithcharacteristics,
                )
                fileClass.writeToFile(
                    "ScriptStats.txt",
                    {
                        "checked_repos": "First checked repo: "
                        + str(startIndex)
                        + ", last checkedRepo"
                        + str(firstRepoIndex),
                        "lostRepos": lostRepos,
                        "checkNextIndex": firstRepoIndex + 1,
                    },
                )
            else:
                print(
                    str(len(reposWithcharacteristics["repositories"]))
                    + " Repos found that machtch the characteristics"
                )
                print("Start with next index: " + str(firstRepoIndex))
                endTime = time.time()
                print("{:5.3f}s".format(endTime - startTime))
                fileClass.writeToFile(
                    "ScriptStats.txt",
                    {
                        "checked_repos": "First checked repo: "
                        + str(startIndex)
                        + ", last checkedRepo"
                        + str(firstRepoIndex - 1),
                        "lostRepos": lostRepos,
                        "timeToCheck": "{:5.3f}s".format(endTime - startTime),
                        "checkNextIndex": firstRepoIndex,
                    },
                )
                break
            firstRepoIndex += 1

    def getClosedIssues(self, repoName):
        """Iterates through all GitHub issues of a repository.

        Args:
            repoName (string): The complete name of a GitHub repository from which the issues are examined.

        Returns:
            list: json from the issues with all the important information for the study.
        """
        page = 0
        issues = []
        totalBugIssues = 0
        totalIssues = 0
        sampling.setErrorToDefault()

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Since GitHub only returns the first 100 results per request, multiple requests must be made. Only when all issues have been retrieved, they will be returned.
        while True:
            self.counter2 += 1
            page += 1
            issuesUrl = f"https://api.github.com/repos/{repoName}/issues?state=closed&per_page=100&page={page}"

            try:
                repoIssuesResponse = session.get(
                    issuesUrl, auth=("username", constants.TOKEN)
                )
            except session.exceptions.ConnectionError:
                time.sleep(300)

            if repoIssuesResponse.status_code == 200:
                repoIssuesResponseJson = repoIssuesResponse.json()
                print(repoIssuesResponse.status_code)
                if not (repoIssuesResponseJson == []):
                    # Iterate through all closed issues
                    for issueKey in repoIssuesResponseJson:
                        # Closed pull requests will be listet here too
                        if "pull_request" in issueKey:
                            continue
                        totalIssues += 1
                        label = ""
                        text = (
                            issueKey["title"].lower() + issueKey["body"].lower()
                            if issueKey["body"]
                            else issueKey["title"].lower()
                        )
                        # If there are labels
                        if 0 < len(issueKey["labels"]):
                            # If there are more than one label
                            for labelKey in issueKey["labels"]:
                                if "bug" in labelKey["name"].lower():
                                    label = "bug"
                                    totalBugIssues += 1
                                    break
                        # If there is no label
                        elif len(issueKey["labels"]) == 0:
                            if sampling.checkIfBug(text):
                                label = "unlabeledBug"
                                totalBugIssues += 1

                        if not label == "":
                            issueCommentInfo = sampling.requestIssueComments(
                                repoName, issueKey["number"]
                            )
                            issues.append(
                                sampling.issueKey(
                                    issueKey["title"],
                                    issueKey["body"] if issueKey["body"] else "",
                                    label,
                                    issueKey["created_at"],
                                    issueKey["closed_at"],
                                    issueCommentInfo[0],
                                    issueCommentInfo[1],
                                )
                            )
                else:
                    break

            else:
                if not repoIssuesResponse.status_code == 404:
                    print(repoIssuesResponse.status_code)
                    self.incompleteResult = True
                    self.errorCode = repoIssuesResponse.status_code
                    print("error on issue requests. Current repo: " + str(repoName))
        print("totalBugIssues")
        print(totalBugIssues)
        print("totalIssues")
        print(totalIssues)
        return sampling.issuesJson(
            self.incompleteResult, self.errorCode, totalBugIssues, totalIssues, issues
        )

    def requestIssueComments(self, repoName, issueNumber):
        """An important information for the study is the time stamp of the last comment under the Issues. These are requested here.

        Args:
            repoName (string): The complete name of a GitHub repository from which the issues are examined.
            issueNumber (integer): The unique issue id.

        Returns:
            lsit: List with date and number of comments
        """
        page = 0
        totalComments = 0
        lastCommentCreated = ""
        sampling.setErrorToDefault()

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Since GitHub only returns the first 100 results per request, multiple requests must be made. Only when all comments have been retrieved, they will be returned.
        while True:
            self.counter += 1
            page += 1
            issuesUrl = f"https://api.github.com/repos/{repoName}/issues/{issueNumber}/comments?per_page=100&page={page}"

            sampling.timeOut(self.counter, 79)

            try:
                repoIssuesCommentsResponse = session.get(
                    issuesUrl, auth=("username", constants.TOKEN)
                )
            except session.exceptions.ConnectionError:
                time.sleep(300)

            if repoIssuesCommentsResponse.status_code == 200:
                repoIssuesCommentResponseJson = repoIssuesCommentsResponse.json()
                print(repoIssuesCommentsResponse.status_code)
                if not (repoIssuesCommentResponseJson == []):
                    # Iterate through all comments
                    for commentKey in repoIssuesCommentResponseJson:
                        totalComments += 1
                        lastCommentCreated = commentKey["updated_at"]
                else:
                    break

            else:
                if not repoIssuesCommentsResponse.status_code == 404:
                    print(repoIssuesCommentsResponse.status_code)
                    self.incompleteResult = True
                    self.errorCode = repoIssuesCommentsResponse.status_code
                    print("error on issue requests. Current repo: " + str(repoName))
        return [lastCommentCreated, totalComments]

    def checkIfBug(self, text):
        """This function checks if a text contains a bug.

        Args:
            text (string): The text which is to be examined after bug.

        Returns:
            boolean: If the text contains a bug.
        """
        bugWords = ["bug", "fix"]

        if any(bug in text for bug in bugWords):
            return True
        else:
            return False

    def checkIfContainsChinese(self, string):
        """Checks if a text contains chinese.

        Args:
            string (string): The text which is to be examined.

        Returns:
            boolean: If the text contains chinese
        """
        countSymbols = 0
        # Problem here: Smileys are also reported as chinese
        if re.search("[\u4e00-\u9fff]", string):
            countSymbols += 1
            # contains chinese
        # contains no chinese

        # Returns only true if there are more than 7 symbols
        if countSymbols > 7:
            return True
        else:
            return False

    def getBugCommits(self, repoName):
        """This function requests all commits and checks if they address a bug and if so, if they contain a relevant file (i.e. JS or TS).

        Args:
            repoName (string): The complete name of a GitHub repository from which the commits are examined.

        Returns:
            list: List of all commits with relevant informations for the study.
        """
        print("commits")

        sampling.setErrorToDefault()
        timeOut = 0
        page = 0
        commitCount = 0
        fullComitCount = 0
        commits = []
        countRequest = 0
        count422 = 0

        # Since several thousand commits are sometimes examined here, several GitHub tokens are needed to reduce the timeout to zero.
        # If not all 6 tokens are used, a timeout is needed --> not here implemented. It is not recomended to do this without this 6 tokens
        tokenRequest = [
            constants.TOKEN,
            constants.TOKEN4,
            constants.TOKEN5,
            constants.TOKEN6,
            constants.TOKEN2,
            constants.TOKEN1,
        ]

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        print(repoName)

        # Since GitHub only returns the first 100 results per request, multiple requests must be made. Only when all comments have been retrieved, they will be returned.
        while True:
            timeOut += 1
            page += 1
            # First get all commits
            commitUrl = f"https://api.github.com/repos/{repoName}/commits?per_page=100&page={page}"

            if timeOut % 80 == 0:
                countRequest += 1

            # Since the script can run for a very long time, several attempts have been implemented here in case an error occurs.
            try:
                repoCommitRequest = session.get(
                    commitUrl,
                    auth=("username", tokenRequest[countRequest % len(tokenRequest)]),
                )

                if repoCommitRequest.status_code == 403:
                    print(
                        f"Status code 403. Sleep for 5 mins. Token for first request used (Need to have a look at array index): {countRequest % len(tokenRequest)}"
                    )
                    time.sleep(300)
                    countRequest += 1
                    repoCommitRequest = session.get(
                        commitUrl,
                        auth=(
                            "username",
                            tokenRequest[countRequest % len(tokenRequest)],
                        ),
                    )
                    if repoCommitRequest.status_code == 403:
                        print(
                            f"Still status code 403. Sleep for another 5 mins. Token for first request used (Need to have a look at array index): {countRequest % len(tokenRequest)}"
                        )
                        time.sleep(300)
                        countRequest += 1
                        repoCommitRequest = session.get(
                            commitUrl,
                            auth=(
                                "username",
                                tokenRequest[countRequest % len(tokenRequest)],
                            ),
                        )
                elif not repoCommitRequest.status_code == 200:
                    print(
                        f"Status code {repoCommitRequest.status_code}. Sleep for 5 mins and try again. If same error again the script will stop. Token for first request used (Need to have a look at array index): {countRequest % 6}"
                    )
                    time.sleep(300)
                    countRequest += 1
                    repoCommitRequest = session.get(
                        commitUrl,
                        auth=(
                            "username",
                            tokenRequest[countRequest % len(tokenRequest)],
                        ),
                    )

            except session.exceptions.ConnectionError:
                time.sleep(300)
                repoCommitRequest = session.get(
                    commitUrl,
                    auth=("username", tokenRequest[countRequest % len(tokenRequest)]),
                )

            if repoCommitRequest.status_code == 200:
                repoCommitRequestJson = repoCommitRequest.json()
                print(
                    f'{time.strftime("%d.%m.%Y %H:%M:%S")}: {repoCommitRequest.status_code}'
                )

                if not repoCommitRequestJson == []:
                    for commit in repoCommitRequestJson:
                        fullComitCount += 1

                        message = commit["commit"]["message"]
                        # Second get all files from the commit
                        commitFilesUrl = f'https://api.github.com/repos/{repoName}/commits/{commit["sha"]}'
                        timeOut += 1

                        if timeOut % 80 == 0:
                            countRequest += 1

                        # Since the script can run for a very long time, several attempts have been implemented here in case an error occurs.
                        try:
                            repoCommitFilesRequest = session.get(
                                commitFilesUrl,
                                auth=(
                                    "username",
                                    tokenRequest[countRequest % len(tokenRequest)],
                                ),
                            )
                            if repoCommitFilesRequest.status_code == 403:
                                print(
                                    f"Status code 403. Sleep for 5 mins. Token for second request used (Need to have a look at array index): {countRequest % len(tokenRequest)}"
                                )
                                countRequest += 1
                                time.sleep(300)
                                repoCommitFilesRequest = session.get(
                                    commitFilesUrl,
                                    auth=(
                                        "username",
                                        tokenRequest[countRequest % len(tokenRequest)],
                                    ),
                                )
                                if repoCommitFilesRequest.status_code == 403:
                                    print(
                                        f"Still status code 403. Sleep for another 5 mins. Token for second request used (Need to have a look at array index): {countRequest % len(tokenRequest)}"
                                    )
                                    time.sleep(300)
                                    countRequest += 1
                                    repoCommitFilesRequest = session.get(
                                        commitFilesUrl,
                                        auth=(
                                            "username",
                                            tokenRequest[
                                                countRequest % len(tokenRequest)
                                            ],
                                        ),
                                    )
                            elif not repoCommitFilesRequest.status_code == 200:
                                print(
                                    f"Status code {repoCommitRequest.status_code}. Sleep for 5 mins and try again. If same error again the script will stop. Token for second request used (Need to have a look at array index): {countRequest % 6}"
                                )
                                countRequest += 1
                                time.sleep(300)
                                repoCommitFilesRequest = session.get(
                                    commitFilesUrl,
                                    auth=(
                                        "username",
                                        tokenRequest[countRequest % len(tokenRequest)],
                                    ),
                                )

                        except session.exceptions.ConnectionError:
                            time.sleep(300)
                            repoCommitFilesRequest = session.get(
                                commitFilesUrl,
                                auth=(
                                    "username",
                                    tokenRequest[countRequest % len(tokenRequest)],
                                ),
                            )
                        print(
                            f'{time.strftime("%d.%m.%Y %H:%M:%S")}: {repoCommitFilesRequest.status_code}, cur commit to investigate: {fullComitCount}'
                        )

                        binary = repoCommitFilesRequest.content

                        repoCommitFiles = json.loads(binary)

                        timeOut += 1
                        if repoCommitFilesRequest.status_code == 422:
                            print("Skip commit because of 422 satatus code.")
                            count422 += 1
                            continue
                        bool = False
                        # Check for each commit if it contains a relevant file (.ts or .js)
                        for commitFile in repoCommitFiles["files"]:
                            if (
                                commitFile["filename"].endswith(
                                    ".ts" if self.curLanguage == "TypeScript" else ".js"
                                )
                                or commitFile["filename"].endswith(
                                    ".tsx"
                                    if self.curLanguage == "TypeScript"
                                    else ".jsx"
                                )
                                or commitFile["filename"].endswith(".vue")
                            ):
                                if not bool:
                                    commitCount += 1
                                bool = True
                                if sampling.checkIfBug(message):
                                    commits.append(
                                        sampling.bugCommitKey(
                                            message,
                                            commit["commit"]["committer"]["date"],
                                            commit["sha"],
                                        )
                                    )
                                    break
                else:
                    break
            else:
                if not repoCommitRequest.status_code == 404:
                    print(repoCommitRequest.status_code)
                    self.incompleteResult = True
                    self.errorCode = repoCommitRequest.status_code
                    print("error on commit requests. Current repo: " + str(repoName))
            print(f"Finished with commits. Lost commits due to 422: {count422}")
            return sampling.commitJson(
                self.incompleteResult,
                self.errorCode,
                len(commits),
                commitCount,
                commits,
            )

    def checkIfApp(self, repoName):
        """This function tokens, if the repo contains an application.

        Args:
            repoName (string): The complete name of a GitHub repository.

        Returns:
            [boolean: If the repo contains an app.
        """
        repoTopics = sampling.lda(repoName)

        if not repoTopics:
            print("Empty readme and description")
            return False

        isApp = False

        dct = dict(repoTopics)

        result = []
        for i in range(0, 2):
            result += re.findall(r'"(.+?)"', dct.get(i))

        # Words that indicate that the repo contains no app
        blacklist = [
            "compon",
            "opencollect",
            "hook",
            "state",
            "collect",
            "plugin",
            "rout",
            "schema",
            "modul",
            "modal",
            "extens",
            "schema",
            "runtim",
            "engin",
            "api",
            "databas",
            "framework",
            "librari",
            "cli",
            "templat",
            "grid",
            "boilerplat",
            "toolkit",
        ]
        for word in blacklist:
            if word in result:
                print(word)
                print(
                    "'framework' in result or 'librari' in result or 'compon' in result...1"
                )
                return False

        # packageJson = sampling.checkIfPackegeJson(repoName)

        # If the readme of a repo indicates, that it is an app or it it contains a package.json file it returns true.
        if (
            "app" in result
            or "application" in result
            or "websit" in result
            or "platform" in result
        ):
            isApp = True
        # elif packageJson:
        #     isApp = True
        else:
            tqdm.write("No 'app','application','websit' or 'platform'")
            isApp = False
        tqdm.write(f"check if app: {isApp}")
        return isApp

    def checkIfPackegeJson(self, repoName):
        """Checks if the repo contains a package.json file

        Args:
            repoName (boolean): The complete name of a GitHub repository.

        Returns:
            list: List of all paths to the package.json files
        """
        sampling.setErrorToDefault()
        path = []
        pathOriginal = []

        # First request the default branch of the repo to request later the file tree
        defaultBranchUrl = f"https://api.github.com/repos/{repoName}"

        branchRequest = requests.get(
            defaultBranchUrl, auth=("username", constants.TOKEN)
        )

        if branchRequest.status_code == 200:
            branchJson = branchRequest.json()
            # Request file tree
            treeUrls = f'https://api.github.com/repos/{repoName}/git/trees/{branchJson["default_branch"]}?recursive=1'

            treeRequest = requests.get(treeUrls, auth=("username", constants.TOKEN))

            print(treeRequest.status_code)

            if treeRequest.status_code == 200:
                treeJson = treeRequest.json()

                for fileName in treeJson["tree"]:
                    if fileName["path"].endswith("package.json"):
                        path.append(fileName["path"])
                    if fileName["path"].endswith("package.jsonoriginal"):
                        pathOriginal.append(fileName["path"])
            else:
                statusCode = treeRequest.status_code
                if statusCode == 404:
                    incompleteResult = True
                    print("Error on tree request. Current Repo: " + str(repoName))
        else:
            if branchRequest.status_code == 404:
                self.incompleteResult = True
                self.errorCode = branchRequest.status_code
                print("Error on tree request. Current Repo: " + str(repoName))

        return sampling.packageJsonKey(
            self.incompleteResult, self.errorCode, path, pathOriginal
        )

    def lda(self, repoFullName):
        """Latent Dirichlet Allocation algorithm is executed here, which outputs to the readme and project description topics with different weights.

        Args:
            repoFullName (boolean): The complete name of a GitHub repository.

        Returns:
            list of tuples: Tuples that contain the topic and a weighting.
        """
        # Request the diffrently writed readmes and the project descriptions
        readmeUrl = f"https://raw.githubusercontent.com/{repoFullName}/master/README.md"
        readmeUrl2 = (
            f"https://raw.githubusercontent.com/{repoFullName}/master/readme.md"
        )
        readmeUrl3 = (
            f"https://raw.githubusercontent.com/{repoFullName}/master/Readme.md"
        )
        readmeUrl4 = (
            f"https://raw.githubusercontent.com/{repoFullName}/main/Readme.md"
        )
        readmeUrl5 = (
            f"https://raw.githubusercontent.com/{repoFullName}/main/readme.md"
        )
        readmeUrl6 = (
            f"https://raw.githubusercontent.com/{repoFullName}/main/Readme.md"
        )
        descriptionUrl = f"https://api.github.com/repos/{repoFullName}"

        description = requests.get(descriptionUrl, auth=("username", constants.TOKEN))

        descriptionJson = description.json()

        readme = requests.get(readmeUrl, auth=("username", constants.TOKEN))

        # If README.md is not written in capital letters
        if readme.status_code == 404:
            readme = requests.get(readmeUrl2, auth=("username", constants.TOKEN))
            if readme.status_code == 404:
                readme = requests.get(readmeUrl3, auth=("username", constants.TOKEN))
                if readme.status_code == 404:
                    readme = requests.get(readmeUrl4, auth=("username", constants.TOKEN))
                    if readme.status_code == 404:
                        readme = requests.get(readmeUrl5, auth=("username", constants.TOKEN))
                        if readme.status_code == 404:
                            readme = requests.get(readmeUrl6, auth=("username", constants.TOKEN))

        readmeText = readme.text

        if not description.status_code == 200 and not readme.status_code:
            return None
        elif not description.status_code == 200 or not descriptionJson["description"]:
            descriptionJson["description"] = ""
        elif not readme.status_code == 200:
            readmeText = ""

        tokenizer = RegexpTokenizer(r"\w+")

        # If already dowloaded comment the following line
        # nltk.download("stopwords")
        en_stop = stopwords.words("english")

        p_stemmer = PorterStemmer()

        readmeWithoutNumb = re.sub(r"\d+", "", readmeText)

        descriptionWithoutNumb = re.sub(r"\d+", "", descriptionJson["description"])

        doc_set = [readmeWithoutNumb, descriptionWithoutNumb]

        texts = []
        repoInfo = repoFullName.split("/")
        repoName = repoInfo[1]
        userName = repoInfo[0]
        # Tokenize the readme and project description and delete the stopwords
        for i in doc_set:
            raw = i.lower()
            tokens = tokenizer.tokenize(raw)

            stopped_tokens = [i for i in tokens if not i in en_stop]

            stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens]

            repoName = p_stemmer.stem(repoName)
            userName = p_stemmer.stem(userName)

            texts.append(stemmed_tokens)

        tokens = []
        # Filter out some unnecessary words from the token lists
        for text in texts:
            text = list(filter(lambda x: x != "http", text))
            text = list(filter(lambda x: x != "com", text))
            text = list(filter(lambda x: x != "org", text))
            text = list(filter(lambda x: x != "github", text))
            text = list(filter(lambda x: x != "img", text))
            text = list(filter(lambda x: x != "imag", text))
            text = list(filter(lambda x: x != "www", text))
            text = list(filter(lambda x: x != "href", text))
            text = list(filter(lambda x: x != "svg", text))
            text = list(filter(lambda x: x != "png", text))
            text = list(filter(lambda x: x != "src", text))
            text = list(filter(lambda x: x != "div", text))
            text = list(filter(lambda x: x != "p", text))
            text = list(filter(lambda x: x != "v", text))
            text = list(filter(lambda x: x != "br", text))
            text = list(filter(lambda x: x != "badg", text))
            text = list(filter(lambda x: x != "npm", text))
            text = list(filter(lambda x: x != "js", text))
            text = list(filter(lambda x: x != "jsx", text))
            text = list(filter(lambda x: x != "html", text))
            text = list(filter(lambda x: x != "ts", text))
            text = list(filter(lambda x: x != "tsx", text))
            text = list(filter(lambda x: x != "md", text))
            text = list(filter(lambda x: x != "readm", text))
            text = list(filter(lambda x: x != "licens", text))
            text = list(filter(lambda x: x != "io", text))
            text = list(filter(lambda x: x != "sponsor", text))
            text = list(filter(lambda x: x != "support", text))
            text = list(filter(lambda x: x != "angular", text))
            text = list(filter(lambda x: x != "react", text))
            text = list(filter(lambda x: x != "vue", text))
            text = list(filter(lambda x: x != "javascript", text))
            text = list(filter(lambda x: x != "typescript", text))
            text = list(filter(lambda x: x != repoName, text))
            text = list(filter(lambda x: x != userName, text))

            tokens.append(text)
        dictionary = corpora.Dictionary(tokens)

        corpus = [dictionary.doc2bow(token) for token in tokens]

        if len(dictionary) == 0:
            return

        # Execute LDA algorithm
        ldaModel = LdaModel(corpus, num_topics=2, id2word=dictionary, passes=20)

        return ldaModel.print_topics(-1)

    def sortVueProjectsLanguage(self):
        """The projects that have Vue as the primary programming language must be assigned to JS or TS. This is done in this function."""
        vueRepos = fileClass.openFile("VueRepos.txt")

        tsRepos = fileClass.openFile("TypeScriptRepos.txt")

        jsRepos = fileClass.openFile("JavaScriptRepos.txt")

        timeOutCounter = 0
        lostVueRepos = 0

        currentRepo = 0

        for vueRepo in vueRepos["repositories"]:
            timeOutCounter += 1
            currentRepo += 1

            print("Repo " + str(currentRepo) + " von " + str(vueRepos["total_count"]))

            if sampling.timeOut(timeOutCounter, 80):
                fileClass.writeToFile("TypeScriptRepos.txt", tsRepos)
                fileClass.writeToFile("JavaScriptRepos.txt", jsRepos)

            # Get other languages than Vue
            langRequest = sampling.requestLanguages(vueRepo["repoFullName"])

            if langRequest.status_code == 200:
                print(langRequest.status_code)
                langRequestJson = langRequest.json()

                # If the percentage among JS and TS of one of the two languages is over 70%, it is added to the corresponding pl list.
                if "JavaScript" in langRequestJson:
                    if "TypeScript" in langRequestJson:
                        countJS = langRequestJson["JavaScript"]
                        countTS = langRequestJson["TypeScript"]
                        allJSTS = countJS + countTS
                        if countJS / allJSTS > 0.7:
                            jsRepos["repositories"].append(vueRepo)
                            jsRepos["total_count"] += 1
                        elif countTS / allJSTS > 0.7:
                            tsRepos["repositories"].append(vueRepo)
                            tsRepos["total_count"] += 1
                        else:
                            lostVueRepos += 1
                    else:
                        jsRepos["repositories"].append(vueRepo)
                        jsRepos["total_count"] += 1
                elif "TypeScript" in langRequestJson:
                    tsRepos["repositories"].append(vueRepo)
                    tsRepos["total_count"] += 1
            else:
                if not langRequest.status_code == 404:
                    print(langRequest.status_code)
                    tsRepos["incomplete_results"] = True
                    jsRepos["incomplete_results"] = True
                    tsRepos["status_code"] = langRequest.status_code
                    jsRepos["status_code"] = langRequest.status_code
                    print(
                        "Error on vue language requests. Current repo: "
                        + str(vueRepo["repoFullName"])
                    )

        fileClass.writeToFile("TypeScriptRepos.txt", tsRepos)
        fileClass.writeToFile("JavaScriptRepos.txt", jsRepos)
        print("repos lost: " + str(lostVueRepos))

    def sortReposByStars(self):
        """Sorts the repo list by stars and gives each repo an id."""
        reposList = fileClass.openFile(str(self.curLanguage) + "Repos.txt")
        repos = reposList["repositories"]

        sortedRepos = sorted(repos, key=lambda repo: repo["stars"], reverse=True)

        index = 1
        for repo in sortedRepos:
            repo["index"] = index
            index += 1

        fileClass.writeToFile(
            str(self.curLanguage) + "Repos.txt",
            sampling.repoJsons(
                reposList["total_count"],
                reposList["incomplete_results"],
                reposList["status_code"],
                sortedRepos,
            ),
        )

    def daterange(self, startDate, endDate):
        """Function that gives the range of the date.

        Args:
            startDate (date): Date of the first repo to be examined.
            endDate (date): Date of the last repo to be examined.

        Yields:
            list: List of all dates in the given range.
        """
        for n in range(int((endDate - startDate).days)):
            yield startDate + timedelta(n)

    def requestLanguages(self, repoName):
        """Function to get all languages used in the repo.

        Args:
            repoName (boolean): The complete name of a GitHub repository.

        Returns:
            json: Json of the languages used in the repo.
        """
        url = f"https://api.github.com/repos/{repoName}/languages"

        return requests.get(url, auth=("username", constants.TOKEN))

    def checkApiLimit(self, username):
        """Check how many requests have already been made this hour. Change token number in function.

        Args:
            username (string): The username behind the token.
        """
        url = f"https://api.github.com/users/{username}"
        test = requests.head(url, auth=("username", constants.TOKEN))
        print(test.headers)

    def repoKey(self, index, repoFullName, creationDate, stars, issues, commits):
        return {
            "index": index,
            "repoFullName": repoFullName,
            "creationDate": creationDate,
            "stars": stars,
            "issues": issues,
            "commits": commits,
        }

    def repoJsons(self, totalCount, incompleteResult, statusCode, repositories):
        return {
            "language": self.curLanguage,
            "total_count": totalCount,
            "time_period": "Start date: "
            + str(self.startDate)
            + ", end date: "
            + str(self.endDate),
            "incomplete_results": incompleteResult,
            "status_code": statusCode,
            "repositories": repositories,
        }

    def issuesJson(
        self, incompleteResult, statusCode, totalBugIssues, totalIssues, issues
    ):
        return {
            "incomplete_results": incompleteResult,
            "status_code": statusCode,
            "total_bug_issues": totalBugIssues,
            "total_issues": totalIssues,
            "issues": issues,
        }

    def issueKey(
        self, title, description, label, createdAt, closedAt, lastComment, commentCount
    ):
        return {
            "title": title,
            "description": description,
            "label": label,
            "createdAt": createdAt,
            "closedAt": closedAt,
            "lastComment": lastComment,
            "commentCount": commentCount,
        }

    def commitJson(
        self, incompleteResult, statusCode, totalBugCommits, totalCommits, bugCommits
    ):
        return {
            "incomplete_results": incompleteResult,
            "status_code": statusCode,
            "total_bug_commits": totalBugCommits,
            "total_commits": totalCommits,
            "bug_commits": bugCommits,
        }

    def bugCommitKey(self, message, createdAt, sha):
        return {"message": message, "created_at": createdAt, "sha": sha}

    def packageJsonKey(self, incompleteResult, statusCode, path, pathsOriginal):
        return {
            "incomplete_result": incompleteResult,
            "status_code": statusCode,
            "paths": path,
            "paths_original": pathsOriginal,
        }

    def timeOut(self, currRequestCount, timeOutRequestNumb):
        """If more than the allowed number of requests is exceeded, there will be a one-minute pause.
        Args:
            currRequestCount ([integer): Cur number of request.
            timeOutRequestNumb (integer): If this number is exceeded, a timeout is made.

        Returns:
            boolean: If a timeout is necessary
        """
        if currRequestCount % timeOutRequestNumb == 0:
            self.counter = 0
            time.sleep(60)
            return True

    def setErrorToDefault(self):
        self.incompleteResult = False
        self.errorCode = "200"

    def correctIndex(self):
        """When repos are deleted, there is a need to correct the unique ids."""
        repos = fileClass.openFile(str(self.curLanguage) + "ReposCharacteristics.txt")
        print(type(repos))
        count = 0

        for repo in repos["repositories"]:
            count += 1
            repo["index"] = count
        repos["total_count"] = count

        fileClass.writeToFile(str(self.curLanguage) + "ReposCharacteristics.txt", repos)

    def deleteElementFromJson(self, indexe):
        """When the manual inspection is done and repos are not wrongly selected as valid, they need to be deleted.

        Args:
            indexe (integer): The number of the wrongly selected repo.
        """
        repos = fileClass.openFile(str(self.curLanguage) + "ReposCharacteristics.txt")
        delElements = 0

        for index in indexe:
            del repos["repositories"][index - 1 - delElements]
            delElements += 1

        count = 0
        for repo in repos["repositories"]:
            count += 1
            repo["index"] = count

        repos["total_count"] = count

        fileClass.writeToFile(str(self.curLanguage) + "ReposCharacteristics.txt", repos)

    def writeIssueDataFromJsonToCSV(self):
        """Reads the data from the json and writes to the csv format for further data analysis."""
        repos = fileClass.openFile(str(self.curLanguage) + "ReposCharacteristics.txt")

        for repo in repos["repositories"]:
            print(f'Started with repo {repo["index"]}')
            issueCount = repo["issues"]["total_bug_issues"]
            # Add issue count to csv
            commaSeparatedValues = CSV("ReposCharacteristics.csv")
            commaSeparatedValues.changeValueInCSV(
                repo["index"], "bug_issues_count", issueCount
            )

            secsOpen = 0
            countIssues = 0

            print("Calculate avg time")
            for issue in repo["issues"]["issues"]:
                lastComment = issue["lastComment"]

                # If there is no comment under the issue use the time until the issue was closed
                if lastComment == "":
                    lastComment = issue["closedAt"]

                issueCreated = time.strptime(issue["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
                issueLastComment = time.strptime(lastComment, "%Y-%m-%dT%H:%M:%SZ")

                issueCreated = calendar.timegm(issueCreated)
                issueLastComment = calendar.timegm(issueLastComment)

                # Time difference in seconds
                timedif = issueLastComment - issueCreated

                if timedif <= 120 or timedif >= 31536000:
                    print(f"time issue is open: {timedif}")
                    continue
                secsOpen += timedif
                countIssues += 1

            if countIssues < 5:
                print(
                    f"Less than 5 issues (bug issues can be more than 5 but the issues that are not longer than 2 mins or more than 365 days open are subtracted): {countIssues}"
                )
                commaSeparatedValues.changeValueInCSV(
                    repo["index"], "avg_bug-issue_time", float("inf")
                )
                commaSeparatedValues = CSV("Metrics.csv")
                commaSeparatedValues.changeValueInCSV(
                    repo["index"], "avg_bug-issue_time", float("inf")
                )
                continue

            print(f"secs open: {secsOpen}")
            # If there are more than 5 bug issues add the avg time to close the issue (to last comment under issue) to csv
            commaSeparatedValues.changeValueInCSV(
                repo["index"], "avg_bug-issue_time", secsOpen / countIssues
            )
            commaSeparatedValues = CSV("Metrics.csv")
            commaSeparatedValues.changeValueInCSV(
                repo["index"], "avg_bug-issue_time", secsOpen / countIssues
            )

    def writeCommitsDataFromJsonToCSV(self):
        """Reads the data from the json and writes to the csv format for further data analysis."""
        repos = fileClass.openFile(str(self.curLanguage) + "ReposCharacteristics.txt")

        for repo in repos["repositories"]:
            print(f'Started with repo {repo["index"]}')
            commaSeparatedValues = CSV("ReposCharacteristics.csv")
            # Add bug-fix commit count
            commaSeparatedValues.changeValueInCSV(
                repo["index"],
                "bug-fix_commits_count",
                repo["commits"]["total_bug_commits"],
            )

            # Add commit count
            commaSeparatedValues.changeValueInCSV(
                repo["index"], "commits_count", repo["commits"]["total_commits"]
            )

            commaSeparatedValues = CSV("Metrics.csv")

            if repo["commits"]["total_commits"] >= 30:
                # Add bug-fix commit ratio
                commaSeparatedValues.changeValueInCSV(
                    repo["index"],
                    "bug-fix-commits_ratio",
                    repo["commits"]["total_bug_commits"]
                    / repo["commits"]["total_commits"],
                )
            else:
                commaSeparatedValues.changeValueInCSV(
                    repo["index"], "bug-fix-commits_ratio", float("inf")
                )

    def checkLabelRatio(self):
        """Checks how many of the issues are labeled with bug."""
        repoFile = fileClass.openFile(f"{self.curLanguage}ReposCharacteristics.txt")
        unlabeledIssues = 0
        labeledIssues = 0
        totalIssues = 0
        totalBugIssues = 0

        for repo in repoFile["repositories"]:
            for issue in repo["issues"]["issues"]:
                if issue["label"] == "bug":
                    labeledIssues += 1
                else:
                    unlabeledIssues += 1
            totalIssues += repo["issues"]["total_issues"]
            totalBugIssues += repo["issues"]["total_bug_issues"]

        print(
            f"{self.curLanguage}: unlabeledIssues= {unlabeledIssues}, labeledIssues= {labeledIssues}. Total issues= {totalIssues}, total bug issues= {totalBugIssues}.  {labeledIssues/totalBugIssues}% der bug issues are labeled."
        )

    def getStarsOfReposPerPL(self):
        languages = ["JavaScript", "TypeScript"]
        arrayStarsTS = []
        arrayStarsJS = []
        for language in languages:
            countStars = 0
            reposList = fileClass.openFile(str(language) + "ReposCharacteristics.txt")
            repos = reposList["repositories"]
            for repo in repos:
                arrayStarsTS.append(
                    repo["stars"]
                ) if language == "TypeScript" else arrayStarsJS.append(repo["stars"])
                countStars += repo["stars"]

            print("Language " + language + " has stars in total: " + str(countStars))

        print(f"JS has stars median of: {np.median(arrayStarsJS)}")
        print(f"TS has stars median of: {np.median(arrayStarsTS)}")

        printDiagramms.boxplot(
            [arrayStarsJS, arrayStarsTS],
            "stars",
            [1, 2],
            ["JavaScript", "TypeScript"],
        )


class SonarQubeDance:
    """This class handles the SonarQube analysis. All data from code smells to cognitive complexity to LoC are genereted via the following functions."""

    def __init__(self):
        self.curLanguage = language.getLanguage()
        self.repoFullName = ""
        pass

    def createAndAnalyzeRepos(self, startIndex, endIndex):
        """From here the analysis is created and started. At the end the metrics are saved in csv.
        Steps are made:
            1: Prerequesite: Clone repo (CloneRepo class)
            2: Generate token for analysis
            3: Execute analysis
            4: Output code smells and cognitive comlexity

        Args:
            startIndex (integer): The index of the repository of the refined list at which the analysis is to be started.
            endIndex (integer): The index of the repository of the refined list at which the analysis is to be ended.
        """

        repos = fileClass.openFile(str(self.curLanguage) + "ReposCharacteristics.txt")

        for repo in repos["repositories"]:
            if repo["index"] < startIndex or endIndex < repo["index"]:
                continue
            self.repoFullName = repo["repoFullName"].replace("/", "-")
            print(self.repoFullName)
            if self.curLanguage == "TypeScript":
                fileClass.deleteFiles(tsconfig.checkLocalTsconfig(self.repoFullName))
                tsconfig.createDefaultTsconfig(self.repoFullName)

            sonarQubeDance.executeAnalysis(sonarQubeDance.generateToken())
            print(os.getcwd())
            os.chdir("../../../")
            commaSeparatedValues.changeValueInCSV(
                repo["index"], "code_smells", sonarQubeDance.getCodeSmellsIssues()
            )
            print("nach speichern")
            commaSeparatedValues.changeValueInCSV(
                repo["index"],
                "cognitive_complexity",
                sonarQubeDance.getCogComplexityOrNcloc("cognitive_complexity"),
            )
            commaSeparatedValues.changeValueInCSV(
                repo["index"], "ncloc", sonarQubeDance.getCogComplexityOrNcloc("ncloc")
            )
            print(f'Repo {self.repoFullName}: {repo["index"]} analyzed')

    def generateToken(self):
        """The token for the repository will be automatically created here.

        Returns:
            string: The string of the token.
        """
        queryToken = {"name": self.repoFullName}
        tokenRequest = requests.post(
            constants.URLGENERATETOKEN, params=queryToken, auth=(constants.TOKEN3, "")
        )
        print(tokenRequest.status_code)
        print(tokenRequest.json())
        return tokenRequest.json()["token"]

    def executeAnalysis(self, token):
        """The analysis of the repo is executed in the root folder.

        Args:
            token (string): The token created for the repository.
        """
        js = "./git-repos/JS/" + str(self.repoFullName)
        ts = "./git-repos/TS/" + str(self.repoFullName)
        os.chdir(js if self.curLanguage == "JavaScript" else ts)
        os.system(
            f'sonar-scanner.bat -D"sonar.projectKey={self.repoFullName}" -D"sonar.host.url=http://localhost:9000" -D"sonar.login={token}"'
        )

    def getCodeSmellsIssues(self):
        """Requests the issues found from SonarQube. Code smells are only counted if there are related to ts or js.

        Returns:
            integer: The number of code smells.
        """
        # In large projects SonarQube need some time to process the analysis. Update value here.
        print(
            "SonarQube needs time to process the analysis. Therefore wait for 3 mins until the data is available. For very large projects it is possible that the time needs to be manually increased."
        )
        time.sleep(180)
        queryTSJS = {
            "componentKeys": f"{self.repoFullName}",
            "languages": "js" if self.curLanguage == "JavaScript" else "ts",
            "types": "CODE_SMELL",
        }
        reqTSJS = requests.get(
            constants.URLISSUES, params=queryTSJS, auth=(constants.TOKEN3, "")
        )

        jsonRequestTSJS = reqTSJS.json()
        print(jsonRequestTSJS)
        print("Code smell count: " + str(jsonRequestTSJS["total"]))
        return int(jsonRequestTSJS["total"])

    def getCogComplexityOrNcloc(self, metric):
        """Funtion to get the number of cog. complex. or LoC. Only counted if related to .ts or .js.

        Args:
            metric (ncloc or cognitive_complexity): The desired metric.

        Returns:
            integer: The numer of the collected metric.
        """
        pageNumber = 0
        metricCount = 0
        while True:
            pageNumber += 1
            query = {
                "component": f"{self.repoFullName}",
                "metricKeys": metric,
                "ps": 500,
                "p": pageNumber,
            }

            req = requests.get(
                constants.URLCOMPONENTREE, params=query, auth=(constants.TOKEN3, "")
            )

            jsonRequestComponents = req.json()["components"]
            if not jsonRequestComponents == []:
                for file in jsonRequestComponents:
                    try:
                        # Only when number is related to file. Not when to folder.
                        if file["qualifier"] == "FIL" and (
                            (
                                file["language"]
                                == ("js" if self.curLanguage == "JavaScript" else "ts")
                            )
                            or (
                                file["path"].endswith(".vue")
                                and file["language"] == "js"
                            )
                        ):
                            try:
                                metricCount += int(file["measures"][0]["value"])
                            except:
                                print("No value measured")
                    except:
                        print("File with no language attribute, e.g. xml")
            else:
                print(metric + " count: " + str(metricCount))
                return metricCount

    def metricSearch(self):
        """Prints all metrics from SonarQube."""
        url = "http://localhost:9000/api/metrics/search"
        query = {"ps": 500}
        req = requests.get(url, params=query, auth=(constants.TOKEN3, ""))
        print(req.json())


class ESLint:
    """To retrive the number of used any types ESLint needs to be installed and executed for each TypeScript porject."""

    def __init__(self):
        self.curLanguage = language.getLanguage()
        self.repoFullName = ""
        pass

    def createEslintReport(self, startIndex, endIndex):
        """Function for the whole ESLint process.
        Steps:
            1. delete existing ESLint files,
            2. rename existing package.json,
            3. copy default ESLint config into project root,
            4. delete new created package.json config and rename old one,
            5. install and run ESLint,
            6. read report and save value in csv.

        Args:
            startIndex (integer): The index of the repository of the refined list at which the analysis is to be started.
            endIndex (integer): The index of the repository of the refined list at which the analysis is to be ended.
        """
        file = fileClass.openFile(self.curLanguage + "ReposCharacteristics.txt")
        for repo in file["repositories"]:
            if startIndex > repo["index"] or endIndex < repo["index"]:
                continue
            self.repoFullName = repo["repoFullName"].replace("/", "-")

            eslint.deleteExistingEslint(eslint.findAllEslintFilesInDir())
            packageJson.renamePackageJson(self.repoFullName)
            eslint.copyLintConfigInDir()
            eslint.runEslint()
            anyCount = eslint.readReport()
            print(anyCount)
            print("Any-count: " + str(anyCount))
            packageJson.deletePackageJson(self.repoFullName)
            commaSeparatedValues.changeValueInCSV(
                repo["index"], "any-type_count", anyCount
            )

    def findAllEslintFilesInDir(self):
        """Get paths of existing ESLint files.

        Returns:
            list: List of all existing ESLint paths.
        """
        print("find all eslints")
        filesDir = []

        for path in constants.ESLINTPATHS:
            for root, dirs, files in os.walk("./git-repos/TS/" + self.repoFullName):
                for file in files:
                    if file.endswith(path):
                        filesDir.append(os.path.join(root, file))
        print(filesDir)
        return filesDir

    def deleteExistingEslint(self, dirs):
        """Delete all paths of ESLint files.

        Args:
            dirs (list): Paths that will be deleted.
        """
        print("delete existing eslint config")
        for dir in dirs:
            print(dir)
            os.remove(dir)
        print("deletion finished")

    def copyLintConfigInDir(self):
        """Copy default ESLint config file into root of repo."""
        print("copy new eslint config")
        for file in constants.ESLINTFILES:
            shutil.copy(
                file,
                "./git-repos/JS/"
                if self.curLanguage == "JavaScript"
                else "./git-repos/TS/" + f"{self.repoFullName}/.eslintignore",
            )
            shutil.copy(
                file,
                "./git-repos/JS/"
                if self.curLanguage == "JavaScript"
                else "./git-repos/TS/" + f"{self.repoFullName}/.eslintrc.js",
            )
        print("copy finished")

    def runEslint(self):
        """Installs the typescript eslint plugin and runs the analysis. If it is a react project the .tsx extension is analysed too. Saves the report in folder."""
        os.chdir(
            "./git-repos/JS/"
            if self.curLanguage == "JavaScript"
            else "./git-repos/TS/" + f"{self.repoFullName}"
        )
        print("install")
        try:
            subprocess.check_call(
                "npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin --force",
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            print("error on installation")
        print("install finished")
        try:
            print(os.getcwd())
            subprocess.check_call(
                f'npx eslint . --ext .ts,.tsx -o "../../../eslint/eslintReports/eslint_output_{self.repoFullName}.txt"',
                shell=True,
            )
        except subprocess.CalledProcessError as e:
            if str(e).endswith("1."):
                print("Eslint report created")
            else:
                try:
                    print(os.getcwd())
                    subprocess.check_call(
                        f'npx eslint . --ext .ts -o "../../../eslint/eslintReports/eslint_output_{self.repoFullName}.txt"',
                        shell=True,
                    )
                except subprocess.CalledProcessError as e:
                    print("Eslint report created") if str(e).endswith("1.") else print(
                        "Can't create eslint report!"
                    )

    def readReport(self):
        """Reads the saved eslint report and investigates how often the any type was used.

        Returns:
            string: The number of used any types.
        """
        try:
            with open(
                f"./../../../eslint/eslintReports/eslint_output_{self.repoFullName}.txt"
            ) as f:
                contents = f.readlines()
                os.chdir(f"./../../../")
                return str(contents).count("Unexpected any. Specify a different type")
        except FileNotFoundError:
            os.chdir(f"./../../../")
            print("error on read file")
            return 0


class Framework:
    """To detect the used frameworks for the applications this class was used."""

    def __init__(self):
        self.curLanguage = language.getLanguage()
        self.repoFullName = ""
        pass

    def getFramework(self, startIndex, endIndex):
        """The whole process of the detection of the framework of the application.
        1. get all package.json files where the framework is mostly specified,
        2. check if well-known client-side frameworks are in package.json defined,
        3. save used framework in csv.

        Args:
            startIndex (integer): The index of the repository of the refined list at which the analysis is to be started.
            endIndex (integer): The index of the repository of the refined list at which the analysis is to be ended.
        """
        repos = fileClass.openFile(self.curLanguage + "ReposCharacteristics.txt")
        for repo in repos["repositories"]:
            if startIndex > repo["index"] or endIndex < repo["index"]:
                continue
            self.repoFullName = repo["repoFullName"].replace("/", "-")
            print(self.repoFullName)

            paths = packageJson.checkLocalPackageJson(self.repoFullName, "")

            frameworklists = []
            for path in paths:
                frameworkList = framework.checkFramework(fileClass.openFile(path))
                if not frameworkList == []:
                    for frameworkEle in frameworkList:
                        if not frameworkEle in frameworklists:
                            frameworklists.append(frameworkEle)

            # Express is not a framework for the client-side
            if len(frameworklists) == 2 and "express" in frameworklists:
                for frameworkEle in frameworklists:
                    if not frameworkEle == "express":
                        commaSeparatedValues.changeValueInCSV(
                            repo["index"], "framework", str(frameworkEle)
                        )
            elif len(frameworklists) == 1:
                commaSeparatedValues.changeValueInCSV(
                    repo["index"], "framework", str(frameworklists[0])
                )
            elif len(frameworklists) > 1:
                print(
                    f'{repo["repoFullName"]} has more than one framework used: {frameworklists}'
                )
            else:
                print("No framework identified")
                commaSeparatedValues.changeValueInCSV(
                    repo["index"], "framework", str("No framework identified")
                )

    def checkFramework(self, text):
        """Check if well-known frameworks are in text defined.

        Args:
            text (string): The text to be examied.

        Returns:
            list: List of all detected frameworks.
        """
        frameworks = [
            "'react'",
            "angular",
            "'vue'",
            "ember-cli",
            "preact",
            "foundation",
            "phoenix",
            "meteor",
            "'express'",
            "express.oi",
            "aurelia-cli",
            "backbone",
            "sails",
            "adonis",
            "derby",
        ]
        frameworkList = []
        for frameworkEle in frameworks:
            if frameworkEle in str(text):
                if not frameworkEle in frameworkList:
                    val = frameworkEle.replace("'", "")
                    if val == "express.oi":
                        val = "express"
                    frameworkList.append(val)
        return frameworkList


class CSV:
    """Handles all csv related functions."""

    def __init__(self, fileSuffix):
        """
        Args:
            fileSuffix (string): The file suffix after the programming language.
        """
        self.curLanguage = language.getLanguage()
        self.fileSuffix = fileSuffix
        pass

    def createAndInitCSV(self):
        """Creates csv and adds default values."""
        if not os.path.isfile(str(self.curLanguage) + self.fileSuffix):
            commaSeparatedValues.createCSV()
            commaSeparatedValues.initCSV()

    def changeValueInCSV(self, rowIndex, columnName, value):
        """
        Args:
            rowIndex (integer): Index of csv row.
            columnName (integer): Number of csv column.
            value (integer or string): Value to be changed in csv.
        """
        df = pd.read_csv(str(self.curLanguage) + self.fileSuffix)

        if columnName == "framework":
            df["framework"] = df["framework"].astype(str)

        df.at[rowIndex - 1, columnName] = value

        df.to_csv(str(self.curLanguage) + self.fileSuffix, index=False)

    def createCSV(self):
        """Creates csv file with file suffix defined in constructor."""
        with open(str(self.curLanguage) + self.fileSuffix, "a+", newline="") as f:
            writer = csv.writer(f)

            writer.writerow(
                self.getHEADER(
                    "CalculatedVals.csv"
                    if self.fileSuffix.endswith("CalculatedVals.csv")
                    else self.fileSuffix
                )
            )
            f.close()

    def getHEADER(self, type):
        switch = {
            "ReposCharacteristics.csv": constants.REPOSCHARACTERISTICS,
            "Metrics.csv": constants.METRICS,
            "CalculatedVals.csv": constants.CALCULATEDVALS,
        }
        return switch.get(type, "No such column in csv")

    def getCSVRowIndexMetricFramework(self, calculatedValueType):
        switch = {
            "count": 1,
            "mean": 2,
            "std": 3,
            "min": 4,
            "25%": 5,
            "50%": 6,
            "75%": 7,
            "max": 8,
        }
        return switch.get(calculatedValueType, "No such column in csv")

    def getCSVColumnIndexData(self, columnName):
        switch = {
            "ncloc": 2,
            "code_smells": 3,
            "any-type_count": 4,
            "cognitive_complexity": 5 if self.curLanguage == "TypeScript" else 4,
            "framework": 6 if self.curLanguage == "TypeScript" else 5,
            "bug_issues_count": 7 if self.curLanguage == "TypeScript" else 6,
            "bug-fix_commits_count": 8 if self.curLanguage == "TypeScript" else 7,
            "commits_count": 9 if self.curLanguage == "TypeScript" else 8,
        }
        return switch.get(columnName, "No such column in csv")

    def getCSVColumnIndexMetric(self, columnName):
        switch = {
            "code-smells_ncloc": 2,
            "bug-fix-commits_ratio": 3,
            "avg_bug-issue_time": 4,
            "cognitive-complexity_ncloc": 5,
            "any-type-count_ncloc": 6,
        }
        return switch.get(columnName, "No such column in csv")

    def initCSV(self):
        """Adds values (index and repo name) from json to csv."""
        repoFile = fileClass.openFile(self.curLanguage + "ReposCharacteristics.txt")
        print("Add repos from json to csv without values")
        for repo in repoFile["repositories"]:
            commaSeparatedValues.writeInitToCSV(repo["index"], repo["repoFullName"])
        print("All repos added to csv")

    def writeInitToCSV(self, index, repoName):
        """Writes index and repo name to csv.

        Args:
            index (integer): Id from repo.
            repoName (string): Full repo name.
        """
        with open(str(self.curLanguage) + self.fileSuffix, "a+", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([index, repoName])
            f.close()

    def addColumnWithDefaultText(self, columnName, defaultText):
        """Add new column with default text. Needs to be added at getCSVColumnIndexData().

        Args:
            columnName (string): Name of the new column.
            defaultText (string): Default text.
        """
        df = pd.read_csv(str(self.curLanguage) + self.fileSuffix)
        print(f"Create column: {columnName} with default text: {defaultText}")

        df[columnName] = defaultText
        df.to_csv(str(self.curLanguage) + self.fileSuffix, index=False)
        print(
            f"Please add {columnName} to getCSVColumnIndexData() with index to change later values via code"
        )

    def deleteRowAndCorrectIndex(self, index):
        """
        Args:
            index (integer): Index of repo and not of csv.
        """
        print(f"delete index: {index}")
        df = pd.read_csv(str(self.curLanguage) + self.fileSuffix)
        df.drop(index - 1, axis=0, inplace=True)
        for row in range(index, len(df.index) + 1):
            df.loc[row, "index"] = row
        df.to_csv(str(self.curLanguage) + self.fileSuffix, index=False)

        print("Maybe you need to delete this element from the .txt (json) too!")

    def getCSVcolumnValues(self, columnIndex, fileName):
        """
        Args:
            columnIndex (integer): Index of repo and not of csv.
            fileName (string): Complete filename with pl.

        Returns:
            integer: Value of csv.
        """
        df = pd.read_csv(fileName)

        values = []
        for row in range(0, len(df.index)):
            values.append(df.values[row][columnIndex])

        return values

    def deleteColumn(self, columnName):
        """
        Args:
            columnName (string): Name of the column to be deleted.
        """
        df = pd.read_csv(str(self.curLanguage) + self.fileSuffix)

        df.drop(columnName, inplace=True, axis=1)

        df.to_csv(str(self.curLanguage) + self.fileSuffix, index=False)

    def sumColumn(self, columnName, fileName):
        """Summs up all values of a column that are not inf value.

        Args:
            columnName (string): Name of the column.
            fileName (string): Complete filename with pl.

        Returns:
            integer: Sum of all values that are not inf from the column.
        """
        df = pd.read_csv(fileName)

        sum = 0
        for row in df[columnName]:
            if row == float("inf"):
                continue
            sum += row

        print(sum)
        return sum

    def describeColumn(self, columnName, fileName):
        """Calulates values (count, mean, std, min, 25%, 50%, 75%, max) of a column.

        Args:
            columnName (string): Name of the column.
            fileName (string): Complete filename with pl.
        """
        df = pd.read_csv(fileName)
        print(df.loc[(df[columnName] < float("inf"))][columnName].describe())


class CloneRepo:
    """Automatically downloads the repositories from the list."""

    def __init__(self):
        self.curLanguage = language.getLanguage()
        pass

    def cloneRepoFromList(self, startIndex):
        """Clones all repos from the list.

        Args:
            startIndex (integer): The index of the repository of the refined list at which the download is to be started.
        """
        repos = fileClass.openFile(str(self.curLanguage) + "ReposCharacteristics.txt")

        print("Started with cloning")
        for repo in repos["repositories"]:
            if repo["index"] < startIndex:
                continue
            print("Cur repo: " + str(repo["index"]))
            path = (
                "./git-repos/JS/"
                if self.curLanguage == "JavaScript"
                else "./git-repos/TS/"
            )
            repoName = f'{repo["repoFullName"].replace("/", "-")}'
            fullPath = path + repoName
            if not os.path.isdir(fullPath):
                try:
                    Repo.clone_from(
                        f'https://github.com/{repo["repoFullName"]}.git', fullPath
                    )
                except Exception as inst:
                    print("Problem during cloning: " + str(inst))
            else:
                print("Already cloned")
        print("Done")


class File:
    """All functions related to the json file are in this class."""

    def __init__(self):
        pass

    def openFile(self, fileName):
        """Opens txt file.

        Args:
            fileName (string): Complete filename with pl.

        Returns:
            list: Json of the txt file.
        """
        try:
            with open(fileName, encoding="utf8") as f:
                return json.load(f)
        except:
            print("Create default file")
            fileClass.writeToFile(fileName, None)

    def writeToFile(self, fileName, repoJson):
        """Writes to txt file.

        Args:
            fileName (string): Complete filename with pl.
            repoJson (list): The json object to written in the txt file.
        """
        with open(fileName, "w", encoding="utf-8") as file:
            json.dump(repoJson, file, ensure_ascii=False, indent=4)

    def deleteFiles(self, files):
        """Remove file from os.

        Args:
            files (list): List of paths to be deleted.
        """
        for file in files:
            os.remove(file)


class PackageJson:
    """All related functions to the package.json file are in this class."""

    def __init__(self):
        self.curLanguage = language.getLanguage()
        pass

    def checkLocalPackageJson(self, repoFullName, fileSuffix):
        """Iterates local folder and returns all paths to package.json.

        Args:
            repoFullName (string): Full repo name [username-reponame].
            fileSuffix (string): File suffix from package.json (Original or empty).

        Returns:
            list: List of all paths from package.json from local folder.
        """
        paths = []
        js = "./git-repos/JS/" + f"{repoFullName}"
        ts = "./git-repos/TS/" + f"{repoFullName}"
        for root, dirs, files in os.walk(
            js if self.curLanguage == "JavaScript" else ts
        ):
            if "package.json" + fileSuffix in files:
                paths.append(os.path.join(root, "package.json" + fileSuffix))
        return paths

    def renamePackageJson(self, repoFullName):
        """Renames existing package.json and adds suffix to original or delets it.

        Args:
            repoFullName (string): Full repo name [username-reponame].
        """
        renamedFiles = packageJson.checkLocalPackageJson(repoFullName, "Original")
        files = packageJson.checkLocalPackageJson(repoFullName, "")
        print(files)
        for file in files:
            file = file
            os.rename(file, file + "Original")

        for file in renamedFiles:
            file = file
            os.rename(file, file[:-8])

    def deletePackageJson(self, repoFullName):
        """Deletes new created package.json files.

        Args:
            repoFullName (string): Full repo name [username-reponame].
        """
        files = packageJson.checkLocalPackageJson(repoFullName, "")
        fileClass.deleteFiles(files)
        files = packageJson.renamePackageJson(repoFullName)


class Tsconfig:
    """For the creation of the default tsconfig."""

    def __init__(self):
        pass

    def checkLocalTsconfig(self, repoFullName):
        """Checks if a tsconfig exists in local folder.

        Args:
            repoFullName (string): Full repo name [username-reponame].

        Returns:
            list: List of all paths from tsconfig from local folder.
        """
        paths = []
        for root, dirs, files in os.walk("./git-repos/TS/" + f"{repoFullName}"):
            if "tsconfig.json" in files:
                paths.append(os.path.join(root, "tsconfig.json"))
        return paths

    def createDefaultTsconfig(self, repoFullName):
        """
        Args:
            repoFullName (string): Full repo name [username-reponame].
        """
        os.chdir("./git-repos/TS/" + f"{repoFullName}")
        os.system("tsc --init")
        os.chdir("../../../")


class Language:
    """Sets the programming languages to be examined."""

    def __init__(self, language):
        self.curLanguage = language
        pass

    def getLanguage(self):
        return self.curLanguage


class Test:
    """Functions related to tests for the statistical analysis."""

    def __init__(self):
        pass

    def normalityTest(self, values):
        """Executes normality test.

        Args:
            values (list): List of values.
        """
        statNormal, pNormal = scipy.stats.shapiro(values)

        if pNormal < 0.05:
            print(
                "Values comes not from a normal distribution. Sample does not look Gaussian"
            )
        else:
            print("Values comes from a normal distribution. Sample looks Gaussian")

    def testHypothesis(self, values, alternative):
        """Hypothesis test.

        Args:
            values (list): List of values.
            alternative (string): alternative = less, if tsvals less than jsval. alternative = greater, if tsvals greater than jsval. Else alternative = two-sided
        """

        # Check if same distribution
        statKs, pKs = scipy.stats.ks_2samp(
            values[1], values[0], alternative=alternative
        )

        print(f"ks_2samp --> stat: {statKs}, p: {pKs}")

        firstNormallyDist = False
        secondNormallyDist = False
        # js
        statNormalFirst, pNormalFirst = scipy.stats.shapiro(values[0])
        print(statNormalFirst, pNormalFirst)
        if pNormalFirst < 0.05:
            print(
                "JS values comes not from a normal distribution. Sample does not look Gaussian"
            )
        else:
            firstNormallyDist = True
            print("JS values comes from a normal distribution. Sample looks Gaussian")

        # ts
        statNormalSecond, pNormalSecond = scipy.stats.shapiro(values[1])
        print(statNormalSecond, pNormalSecond)
        if pNormalSecond < 0.05:
            print(
                "TS values comes not from a normal distribution. Sample does not look Gaussian"
            )
        else:
            secondNormallyDist = True
            print("TS values comes from a normal distribution. Sample looks Gaussian")

        if secondNormallyDist and firstNormallyDist:
            # p value = 0.000 means pValue < 0.0005.
            print(scipy.stats.ttest_ind(values[1], values[0], alternative=alternative))
        else:
            # p value = 0.000 means pValue < 0.0005.
            print(
                scipy.stats.mannwhitneyu(values[1], values[0], alternative=alternative)
            )

    def pearson(self, metric):
        """Pearson correlation test. Prints result in console.

        Args:
            metric (string): Metric can be 'code_smells' or 'cognitive_complexity' or 'any-type_count'
        """
        checkCorrelationLists = self.getMetricAndAnyVals(metric)

        pearson_coef, p_value = scipy.stats.pearsonr(
            checkCorrelationLists["any-type-count_ncloc"], checkCorrelationLists[metric]
        )

        print(
            "Pearson Correlation Coefficient: ",
            pearson_coef,
            "and a P-value of:",
            p_value,
        )

    def spearman(self, metric, alternative):
        """Spearman correlation test. Prints result in console.

        Args:
            metric (string): Metrics can be: avg_bug-issue_time, code-smells_ncloc, cognitive-complexity_ncloc, bug-fix-commits_ratio.
            alternative (string): Alternative: 'two-sided' (the correlation is nonzero), 'less' (the correlation is negative), 'greater' (the correlation is positive).
        """
        checkCorrelationLists = self.getMetricAndAnyVals(metric)

        spearman_coef, p_value = scipy.stats.spearmanr(
            checkCorrelationLists["any-type-count_ncloc"],
            checkCorrelationLists[metric],
            alternative=alternative,
        )

        print(
            "Spearman Correlation Coefficient: ",
            spearman_coef,
            "and a P-value of:",
            p_value,
        )

    def getMetricAndAnyVals(self, metric):
        """Get values with used any types.

        Args:
            metric (string): Metrics can be: avg_bug-issue_time, code-smells_ncloc, cognitive-complexity_ncloc, bug-fix-commits_ratio.

        Returns:
            list: list: List of JS and TS values.
        """
        dfChar = pd.read_csv("TypeScriptReposCharacteristics.csv")
        dfMetric = pd.read_csv("TypeScriptMetrics.csv")
        dfMerged = pd.merge(dfChar, dfMetric, on="index", how="outer")
        vals = dfMerged.loc[dfMerged[metric] < float("inf")]
        print(vals["any-type-count_ncloc"])
        return vals

    def getRandomCommits(self, numberRandomComits):
        """Selects random commits from json.

        Args:
            numberRandomComits (integer): Number of printed commits.
        """
        languages = ["TypeScript", "JavaScript"]
        commitlist = []
        for lang in languages:
            repos = fileClass.openFile(f"{lang}ReposCharacteristics.txt")

            for repo in repos["repositories"]:
                for commit in repo["commits"]["bug_commits"]:
                    commitlist.append(commit["message"])

        listRandomCommits = random.sample(commitlist, numberRandomComits)
        counter = 0
        for commitsAS in listRandomCommits:
            counter += 1
            print(f"Commit nr. {counter}")
            print(commitsAS)


class Metrics:
    """All functions related to metrics are in this class implemented."""

    def __init__(self):
        self.curLanguage = language.getLanguage()
        pass

    def calculateMetricPerLoc(self, metric):
        """
        Args:
            metric (string): Metric can be 'code_smells' or 'cognitive_complexity' or 'any-type_count'
        """
        metricList = commaSeparatedValues.getCSVcolumnValues(
            commaSeparatedValues.getCSVColumnIndexData(metric),
            f"{self.curLanguage}ReposCharacteristics.csv",
        )

        ncloc = commaSeparatedValues.getCSVcolumnValues(
            commaSeparatedValues.getCSVColumnIndexData("ncloc"),
            f"{self.curLanguage}ReposCharacteristics.csv",
        )

        for i in range(0, len(metricList)):
            print(metricList[i])
            print(ncloc[i])
            print(metricList[i] / ncloc[i])
            csvColumn = f'{metric.replace("_", "-")}_ncloc'
            commaSeparatedValues.changeValueInCSV(
                i + 1, csvColumn, metricList[i] / ncloc[i]
            )

    def calculateAvgBugResulutionTime(self):
        """Calculates the average time a bug issue was open. Time from opening the issue to the last comment under the issue in seconds."""
        repos = fileClass.openFile(str(self.curLanguage) + "ReposCharacteristics.txt")

        for repo in repos["repositories"]:
            secsOpen = 0
            countIssues = 0

            print("Calculate avg time")
            for issue in repo["issues"]["issues"]:
                lastComment = issue["lastComment"]

                # If there is no comment under the issue use the time until the issue was closed
                if lastComment == "":
                    lastComment = issue["closedAt"]

                issueCreated = time.strptime(issue["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
                issueLastComment = time.strptime(lastComment, "%Y-%m-%dT%H:%M:%SZ")

                issueCreated = calendar.timegm(issueCreated)
                issueLastComment = calendar.timegm(issueLastComment)

                # Time difference in seconds
                timedif = issueLastComment - issueCreated

                if timedif <= 120 or timedif >= 31536000:
                    print(f"time issue is open: {timedif}")
                    continue
                secsOpen += timedif
                countIssues += 1

            if countIssues < 5:
                print(
                    f"Less than 5 issues (bug issues can be more than 5 but the issues that are not longer than 2 mins or more than 365 days open are subtracted): {countIssues}"
                )
                commaSeparatedValues.changeValueInCSV(
                    repo["index"], "avg_bug-issue_time", float("inf")
                )
                continue

            print(f"secs open: {secsOpen/countIssues}")
            # If there are more than 5 bug issues add the avg time to close the issue (to last comment under issue) to csv
            commaSeparatedValues.changeValueInCSV(
                repo["index"], "avg_bug-issue_time", secsOpen / countIssues
            )

    def getMetricWithoutInf(self, metric):
        """Categorized by language.

        Args:
            metric (string): Metrics can be: avg_bug-issue_time, code-smells_ncloc, cognitive-complexity_ncloc, bug-fix-commits_ratio

        Returns:
            list: List of JS and TS values.
        """
        files = ["JavaScript", "TypeScript"]
        valJSTS = []
        for file in files:
            dfMerged = self.mergeCharMetricDF(file)
            valJSTS.append(dfMerged.loc[dfMerged[metric] < float("inf")][metric])
            print(dfMerged.loc[dfMerged[metric] < float("inf")][metric].describe())
        return valJSTS

    def getMetricWithoutInfFramework(self, metric, framework):
        """Categorized by framework.

        Args:
            metric (string): Metrics can be: avg_bug-issue_time, code-smells_ncloc, cognitive-complexity_ncloc, bug-fix-commits_ratio
            framework (string): Framework could be: vue, angular, react, others

        Returns:
            list: List of JS and TS values.
        """
        files = ["JavaScript", "TypeScript"]
        valJSTS = []
        for file in files:
            dfMerged = self.mergeCharMetricDF(file)
            if framework == "others":
                valJSTS.append(
                    dfMerged.loc[
                        (dfMerged["framework"] != "vue")
                        & (dfMerged["framework"] != "angular")
                        & (dfMerged["framework"] != "react")
                        & (dfMerged[metric] < float("inf"))
                    ][metric]
                )
            else:
                valJSTS.append(
                    dfMerged.loc[
                        (dfMerged["framework"] == framework)
                        & (dfMerged[metric] < float("inf"))
                    ][metric]
                )

        return valJSTS

    def mergeCharMetricDF(self, language):
        """Merges two data frames to one.

        Args:
            language (string): The language of the dataframe to be merged.

        Returns:
            dataFrame: The merged data frame.
        """
        dfChar = pd.read_csv(f"{language}ReposCharacteristics.csv")
        dfMetric = pd.read_csv(f"{language}Metrics.csv")
        return pd.merge(dfChar, dfMetric, on="index", how="outer")

    def getMetricsPerFrameWork(self, metric, frameworks):
        """Gets the metric values per framework and saves values ("count", "mean", "std", "min", "25%", "50%", "75%", "max") in file.

        Args:
            metric (string): Metrics can be: avg_bug-issue_time, code-smells_ncloc, cognitive-complexity_ncloc, bug-fix-commits_ratio
            framework (string): Framework could be: vue, angular, react, others

        Returns:
            list: List of JS and TS values.
        """
        files = ["JavaScript", "TypeScript"]
        values = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
        valJSTS = []
        for framework in frameworks:
            for file in files:
                dfChar = pd.read_csv(f"{file}ReposCharacteristics.csv")
                dfMetric = pd.read_csv(f"{file}Metrics.csv")
                dfMerged = pd.merge(dfChar, dfMetric, on="index", how="outer")
                commaSeparatedValues.curLanguage = file
                commaSeparatedValues.fileSuffix = f"{metric}Framework.csv"
                # Create file if not already happend and save data
                if framework == "others":
                    for calcValues in values:
                        commaSeparatedValues.changeValueInCSV(
                            commaSeparatedValues.getCSVRowIndexMetricFramework(
                                calcValues
                            ),
                            framework,
                            dfMerged.loc[
                                (dfMerged["framework"] != "vue")
                                & (dfMerged["framework"] != "angular")
                                & (dfMerged["framework"] != "react")
                                & (dfMerged[metric] < float("inf"))
                            ][metric].describe()[calcValues],
                        )

                    valJSTS.append(
                        dfMerged.loc[
                            (dfMerged["framework"] != "vue")
                            & (dfMerged["framework"] != "angular")
                            & (dfMerged["framework"] != "react")
                            & (dfMerged[metric] < float("inf"))
                        ][metric]
                    )
                else:
                    for calcValues in values:
                        commaSeparatedValues.changeValueInCSV(
                            commaSeparatedValues.getCSVRowIndexMetricFramework(
                                calcValues
                            ),
                            framework,
                            dfMerged.loc[
                                (dfMerged["framework"] == framework)
                                & (dfMerged[metric] < float("inf"))
                            ][metric].describe()[calcValues],
                        )

                    valJSTS.append(
                        dfMerged.loc[
                            (dfMerged["framework"] == framework)
                            & (dfMerged[metric] < float("inf"))
                        ][metric]
                    )

        return valJSTS


class PrintDiagramms:
    """Print diagramms for statistical analysis"""

    def __init__(self):
        pass

    def printScatterplot(self, metric, xRange, yRange):
        """
        Args:
            metric (string): Metrics can be: avg_bug-issue_time, code-smells_ncloc, cognitive-complexity_ncloc, bug-fix-commits_ratio.
            xRange (integer): X-Range of metric for scatterplot.
            yRange (integer): Y-Range of metric for scatterplot.
        """
        df = pd.read_csv(
            "TypeScriptMetrics.csv", usecols=["any-type-count_ncloc", metric]
        )
        df = df[np.isfinite(df).all(1)]

        hover = HoverTool(tooltips=[(f"(any-type,{metric}", "($x, $y)")])
        p = figure(
            x_range=(xRange[0], xRange[1]),
            y_range=(yRange[0], yRange[1]),
            tools=[hover],
        )

        p.scatter(df["any-type-count_ncloc"], df[metric], size=4)

        b, m = polyfit(df["any-type-count_ncloc"], df[metric], 1)
        p.line(
            df["any-type-count_ncloc"],
            b + m * df["any-type-count_ncloc"],
            line_width=2.5,
        )

        p.background_fill_color = "mintcream"
        p.background_fill_alpha = 0.2
        p.xaxis.axis_label = "any-type-count_ncloc"
        p.yaxis.axis_label = metric

        p.xaxis.axis_label_text_font_size = "20pt"
        p.yaxis.axis_label_text_font_size = "20pt"
        p.xaxis.major_label_text_font_size = "15px"
        p.yaxis.major_label_text_font_size = "15px"
        show(p)

    def histogramm(self, metric, minValue, maxValue, steps, width, vals):
        """
        Args:
            metric (string): Metrics can be: avg_bug-issue_time, code-smells_ncloc, cognitive-complexity_ncloc, bug-fix-commits_ratio.
            minValue (integer): Minimum value.
            maxValue (integer): Maximum value.
            steps (integer): Steps.
            width (integer): Width.
            vals (list): List of js and ts vals.
        """
        # First val is JS, second is TS
        for val in vals:
            pyplot.hist(val, bins=np.arange(min(val), max(val) + width, width))
            pyplot.xlabel(metric)
            pyplot.axis([minValue, maxValue, 0, steps])
            pyplot.grid(True)
            pyplot.show()

    def boxplot(self, vals, metric, countDataSet, xTicks):
        """
        Args:
            vals (list): List of js and ts vals.
            metric (string): Subtitle
            countDataSet (list): List of numbers of box plots (For example: [1, 2, 3, ...])
            xTicks (list): List of labels of box plots (For example: ['JavaScript with react', 'TypeScript with react', 'JavaScript with angular', 'TypeScript with angular', ...])
        """
        pyplot.figure(figsize=(5, 5))
        pyplot.boxplot(vals)
        pyplot.suptitle(metric, fontsize=20, fontweight="bold")
        pyplot.xticks(countDataSet, xTicks, fontsize=15)
        pyplot.yticks(fontsize=15)
        pyplot.yticks.labelsize = 20
        pyplot.grid(True)
        pyplot.show()

    def getMean(self, metric, vals):
        """Gets mean of csv column.

        Args:
            metric (string): Metrics can be: avg_bug-issue_time, code-smells_ncloc, cognitive-complexity_ncloc, bug-fix-commits_ratio.
            vals (list): List of js and ts vals.
        """
        print(f"JavaScript {metric} mean: {np.mean(vals[0])}")
        print(f"TypeScript {metric} mean: {np.mean(vals[1])}")


language = Language("TypeScript")

fileClass = File()

sampling = Sampling()

sonarQubeDance = SonarQubeDance()

eslint = ESLint()

framework = Framework()

# Suffix could be: ReposCharacteristics.csv or Metrics.csv
commaSeparatedValues = CSV("Metrics.csv")

cloneRepo = CloneRepo()

packageJson = PackageJson()

tsconfig = Tsconfig()

metrics = Metrics()

test = Test()

printDiagramms = PrintDiagramms()


# test
# read data/JavaScriptRepos.json
# get all repositories
# for each repository
print("test")
i = 0


import pandas as pd
import multiprocessing as mp
from tqdm.contrib.concurrent import process_map

df = pd.read_csv('target_1.csv')

def checkIsApp(row):
    # Ensure row is treated as a Pandas Series directly
    isApp = sampling.checkIfApp(row['owner'] + '/' + row['name'])
    return row['owner'], row['name'], isApp

if __name__ == "__main__":
    # Directly use DataFrame rows as a list of Series objects without wrapping them in tuples
    arguments = [row for index, row in df.iterrows()]

    # Adjust process_map call to pass each Series object directly to checkIsApp
    results = process_map(checkIsApp, arguments, max_workers=mp.cpu_count(), chunksize=1)

    # Update DataFrame with results
    for owner, name, isApp in results:
        df.loc[(df['owner'] == owner) & (df['name'] == name), 'isApp'] = isApp

    # Save the updated DataFrame to CSV once, after all updates
    df.to_csv('target_1.csv', index=False)
